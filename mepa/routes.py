import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Blueprint, Response, current_app, jsonify, render_template, request, send_file
from werkzeug.security import check_password_hash, generate_password_hash

from .ai_service import analyze_with_gemini, evaluate_prompt, normalize_prompt
from .content import IMAGE_EXERCISES, PROMPT_EXAMPLES, SCAM_SCENARIOS, VIDEO_MODULES, VIDEO_QUIZZES, public_video_payload
from .db import get_db
from .pdf_service import build_certificate_pdf
from .security import client_ip, consume_rate_limit, current_user, ensure_csrf_token, login_required, rotate_session, utc_now

bp = Blueprint("main", __name__)
PRIVACY_VERSION = "2026-06-RGPD-MEPA-v2"
MAX_SCORE = 100
CERTIFICATION_THRESHOLD = 70
ROLE_OPTIONS = {"jeune", "enseignant", "etablissement", "citoyen"}


def sanitize_text(value: str, limit: int) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())[:limit]


def is_valid_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email or ""))


def classify_age(age: int) -> str:
    if age < 18:
        return "jeune"
    if age >= 65:
        return "senior"
    return "adulte"


def user_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "role": row["role"],
        "age_group": row["age_group"],
        "created_at": row["created_at"],
        "consent_version": row["consent_version"],
    }


def save_activity(user_id: int, module_id: str, activity_type: str, points: int, max_points: int, details: dict | None = None) -> None:
    points = max(0, min(int(points), int(max_points)))
    db = get_db()
    db.execute(
        """
        INSERT INTO activities(user_id, module_id, activity_type, points, max_points, details, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, module_id, activity_type) DO UPDATE SET
            points = MAX(activities.points, excluded.points),
            max_points = excluded.max_points,
            details = CASE WHEN excluded.points >= activities.points THEN excluded.details ELSE activities.details END,
            completed_at = CASE WHEN excluded.points >= activities.points THEN excluded.completed_at ELSE activities.completed_at END
        """,
        (user_id, module_id, activity_type, points, max_points, json.dumps(details or {}, ensure_ascii=False), utc_now()),
    )
    db.commit()


def prompt_usage(user_id: int) -> dict:
    used = get_db().execute("SELECT COUNT(*) FROM prompt_attempts WHERE user_id = ?", (user_id,)).fetchone()[0]
    limit = current_app.config["PROMPT_ATTEMPT_LIMIT"]
    return {"used": used, "limit": limit, "remaining": max(0, limit - used)}


def get_progress(user_id: int) -> dict:
    db = get_db()
    raw_activities = [dict(row) for row in db.execute(
        "SELECT module_id, activity_type, points, max_points, completed_at FROM activities WHERE user_id = ? ORDER BY completed_at",
        (user_id,),
    ).fetchall()]
    valid_keys = {
        ("video-introduction-ia", "video"),
        ("video-fonctionnement-ia", "video"),
        ("video-introduction-ia-qcm", "video_quiz"),
        ("video-fonctionnement-ia-qcm", "video_quiz"),
        ("prompt-lab", "prompt"),
        ("arnaque-scenario", "scam"),
        ("image-detection", "image"),
    }
    activities = [
        item for item in raw_activities
        if (item["module_id"], item["activity_type"]) in valid_keys
    ]
    opened = [row["video_id"] for row in db.execute("SELECT video_id FROM video_views WHERE user_id = ?", (user_id,)).fetchall()]
    total = min(MAX_SCORE, sum(item["points"] for item in activities))
    quiz_scores = {
        item["module_id"].removesuffix("-qcm"): {"points": item["points"], "max_points": item["max_points"]}
        for item in activities
        if item["activity_type"] == "video_quiz"
    }
    return {
        "score": total,
        "max_score": MAX_SCORE,
        "eligible": total >= CERTIFICATION_THRESHOLD,
        "threshold": CERTIFICATION_THRESHOLD,
        "activities": activities,
        "opened_videos": opened,
        "completed_videos": [item["module_id"] for item in activities if item["activity_type"] == "video" and item["points"] > 0],
        "video_quiz_scores": quiz_scores,
        "certificate_unlocked": total >= CERTIFICATION_THRESHOLD,
        "prompt_usage": prompt_usage(user_id),
    }


def find_video(video_id: str):
    return next((video for video in VIDEO_MODULES if video["id"] == video_id), None)


def find_local_video_path() -> Path | None:
    candidates = [
        Path(current_app.config["LOCAL_VIDEO_PATH"]),
        Path(current_app.root_path).parent / "Video intro a l'IA.mp4",
        Path(current_app.static_folder) / "videos" / "Video intro a l'IA.mp4",
        Path(current_app.static_folder) / "videos" / "video-introduction-ia.mp4",
    ]
    return next((path for path in candidates if path.is_file()), None)


@bp.get("/")
def index():
    return render_template(
        "index.html",
        threshold=CERTIFICATION_THRESHOLD,
        privacy_version=PRIVACY_VERSION,
        csrf_token=ensure_csrf_token(),
    )


@bp.get("/confidentialite")
def privacy_policy():
    return render_template("privacy.html", privacy_version=PRIVACY_VERSION)


@bp.get("/api/me")
def api_me():
    user = current_user()
    payload = {"authenticated": bool(user), "csrf_token": ensure_csrf_token()}
    if user:
        payload.update({"user": user_to_dict(user), "progress": get_progress(user["id"])})
    return jsonify(payload)


@bp.post("/api/register")
def register():
    if not consume_rate_limit("register", client_ip(), 5, 3600):
        return jsonify({"errors": ["Trop de tentatives d'inscription. Réessayez plus tard."]}), 429
    data = request.get_json(silent=True) or {}
    email = sanitize_text(str(data.get("email", "")).lower(), 180)
    password = str(data.get("password", ""))
    name = sanitize_text(str(data.get("name", "")), 80)
    role = sanitize_text(str(data.get("role", "citoyen")), 40)
    consent = data.get("consent") is True
    try:
        age = int(data.get("age", 18))
    except (TypeError, ValueError):
        age = -1

    errors = []
    if not is_valid_email(email):
        errors.append("Adresse e-mail invalide.")
    if len(password) < 10 or not re.search(r"[A-Za-zÀ-ÿ]", password) or not re.search(r"\d", password):
        errors.append("Le mot de passe doit contenir au moins 10 caractères, une lettre et un chiffre.")
    if not name:
        errors.append("Le prénom ou pseudo est obligatoire.")
    if role not in ROLE_OPTIONS:
        errors.append("Profil invalide.")
    if not 10 <= age <= 120:
        errors.append("L'âge doit être compris entre 10 et 120 ans.")
    if not consent:
        errors.append("Le consentement RGPD est nécessaire pour créer un compte.")
    if errors:
        return jsonify({"errors": errors}), 400

    db = get_db()
    try:
        cursor = db.execute(
            """
            INSERT INTO users(email, name, role, age_group, password_hash, rgpd_consent, consent_version, consent_at, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (email, name, role, classify_age(age), generate_password_hash(password, method="scrypt"), PRIVACY_VERSION, utc_now(), utc_now()),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"errors": ["Un compte existe déjà avec cette adresse e-mail."]}), 409

    csrf_token = rotate_session(cursor.lastrowid)
    return jsonify({"ok": True, "csrf_token": csrf_token, "user": user_to_dict(current_user()), "progress": get_progress(cursor.lastrowid)})


@bp.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = sanitize_text(str(data.get("email", "")).lower(), 180)
    password = str(data.get("password", ""))
    limiter_key = f"{client_ip()}:{email}"
    if not consume_rate_limit("login", limiter_key, 8, 900):
        return jsonify({"errors": ["Trop de tentatives de connexion. Réessayez dans quelques minutes."]}), 429

    db = get_db()
    row = db.execute("SELECT * FROM users WHERE email = ? AND deleted_at IS NULL", (email,)).fetchone()
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"errors": ["Identifiants incorrects."]}), 401
    db.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (utc_now(), row["id"]))
    db.commit()
    csrf_token = rotate_session(row["id"])
    return jsonify({"ok": True, "csrf_token": csrf_token, "user": user_to_dict(current_user()), "progress": get_progress(row["id"])})


@bp.post("/api/logout")
def logout():
    return jsonify({"ok": True, "csrf_token": rotate_session()})


@bp.get("/api/content")
@login_required
def api_content():
    user = current_user()
    videos = [public_video_payload(video) for video in VIDEO_MODULES]
    local_exists = find_local_video_path() is not None
    for video in videos:
        if video["source_type"] == "local":
            video["media_ready"] = local_exists
    return jsonify({
        "videos": videos,
        "scams": [{key: value for key, value in scenario.items() if key != "correct_signs"} for scenario in SCAM_SCENARIOS],
        "image_exercises": [{key: value for key, value in exercise.items() if key != "correct_signs"} for exercise in IMAGE_EXERCISES],
        "prompt_examples": PROMPT_EXAMPLES,
        "score_map": {"videos_qcm": 55, "prompt": 20, "arnaques": 25},
        "ai": {"configured": bool(current_app.config["GEMINI_API_KEY"]), "model": current_app.config["GEMINI_MODEL"]},
        "progress": get_progress(user["id"]),
    })


@bp.post("/api/videos/<video_id>/open")
@login_required
def open_video(video_id: str):
    user = current_user()
    video = find_video(video_id)
    if not video:
        return jsonify({"error": "video_not_found", "message": "Vidéo introuvable."}), 404
    if not video["available"]:
        return jsonify({"error": "video_unavailable", "message": "Cette vidéo arrive bientôt."}), 409
    now = utc_now()
    db = get_db()
    db.execute(
        """
        INSERT INTO video_views(user_id, video_id, first_opened_at, last_opened_at, open_count)
        VALUES (?, ?, ?, ?, 1)
        ON CONFLICT(user_id, video_id) DO UPDATE SET
            last_opened_at = excluded.last_opened_at,
            open_count = video_views.open_count + 1
        """,
        (user["id"], video_id, now, now),
    )
    db.commit()
    return jsonify({"ok": True, "video": public_video_payload(video), "progress": get_progress(user["id"])})


@bp.post("/api/videos/<video_id>/complete")
@login_required
def complete_video(video_id: str):
    user = current_user()
    video = find_video(video_id)
    if not video:
        return jsonify({"error": "video_not_found", "message": "Vidéo introuvable."}), 404
    if not video["available"]:
        return jsonify({"error": "video_unavailable", "message": "Cette vidéo arrive bientôt."}), 409
    opened = get_db().execute(
        "SELECT 1 FROM video_views WHERE user_id = ? AND video_id = ?",
        (user["id"], video_id),
    ).fetchone()
    if not opened:
        return jsonify({"error": "video_not_opened", "message": "Ouvrez d'abord la vidéo avant de la marquer comme terminée."}), 409
    save_activity(user["id"], video_id, "video", video["completion_points"], video["completion_points"], {"title": video["title"]})
    return jsonify({"ok": True, "progress": get_progress(user["id"])})


@bp.post("/api/videos/<video_id>/quiz")
@login_required
def submit_video_quiz(video_id: str):
    user = current_user()
    video = find_video(video_id)
    questions = VIDEO_QUIZZES.get(video_id)
    if not video or not questions:
        return jsonify({"error": "quiz_not_found", "message": "QCM introuvable."}), 404
    opened = get_db().execute("SELECT 1 FROM video_views WHERE user_id = ? AND video_id = ?", (user["id"], video_id)).fetchone()
    if not opened:
        return jsonify({"error": "video_not_opened", "message": "Ouvrez la vidéo avant de répondre à son QCM."}), 409
    answers = (request.get_json(silent=True) or {}).get("answers", [])
    if not isinstance(answers, list) or len(answers) != len(questions) or any(not isinstance(answer, int) for answer in answers):
        return jsonify({"errors": ["Répondez à toutes les questions du QCM."]}), 400

    corrections = []
    correct_count = 0
    for index, question in enumerate(questions):
        selected = answers[index]
        is_correct = selected == question["answer"]
        correct_count += int(is_correct)
        corrections.append({
            "question": question["question"],
            "selected": selected,
            "answer": question["answer"],
            "correct": is_correct,
            "correct_text": question["choices"][question["answer"]],
        })
    points = round((correct_count / len(questions)) * video["quiz_points"])
    save_activity(
        user["id"],
        f"{video_id}-qcm",
        "video_quiz",
        points,
        video["quiz_points"],
        {"correct_count": correct_count, "question_count": len(questions)},
    )
    return jsonify({
        "ok": True,
        "points": points,
        "max_points": video["quiz_points"],
        "correct_count": correct_count,
        "question_count": len(questions),
        "corrections": corrections,
        "progress": get_progress(user["id"]),
    })


@bp.get("/media/video-intro-ia")
@login_required
def local_video():
    path = find_local_video_path()
    if not path:
        return jsonify({
            "error": "local_video_missing",
            "message": "Le fichier vidéo local est introuvable. Placez « Video intro a l'IA.mp4 » à la racine du projet ou configurez LOCAL_VIDEO_PATH.",
        }), 404
    return send_file(path, mimetype="video/mp4", conditional=True, max_age=0)


def score_selection(correct: list[str], selected: list[str], max_points: int) -> tuple[int, dict]:
    correct_set = set(correct)
    selected_set = {item for item in selected if isinstance(item, str)}
    true_positive = len(correct_set & selected_set)
    false_positive = len(selected_set - correct_set)
    raw = max(0, true_positive - 0.5 * false_positive)
    points = round((raw / max(1, len(correct_set))) * max_points)
    return max(0, min(max_points, points)), {
        "found": sorted(correct_set & selected_set),
        "missed": sorted(correct_set - selected_set),
        "false_positive": sorted(selected_set - correct_set),
    }


@bp.post("/api/scam/submit")
@login_required
def submit_scam():
    user = current_user()
    data = request.get_json(silent=True) or {}
    scenario = next((item for item in SCAM_SCENARIOS if item["id"] == data.get("scenario_id")), None)
    if not scenario:
        return jsonify({"error": "scenario_not_found", "message": "Scénario introuvable."}), 404
    points, details = score_selection(scenario["correct_signs"], data.get("selected", []), 15)
    details["explanation"] = scenario["explanation"]
    save_activity(user["id"], "arnaque-scenario", "scam", points, 15, details)
    return jsonify({"ok": True, "points": points, "max_points": 15, "details": details, "progress": get_progress(user["id"])})


@bp.post("/api/image/submit")
@login_required
def submit_image_exercise():
    user = current_user()
    data = request.get_json(silent=True) or {}
    exercise = next((item for item in IMAGE_EXERCISES if item["id"] == data.get("exercise_id")), None)
    if not exercise:
        return jsonify({"error": "exercise_not_found", "message": "Exercice introuvable."}), 404
    points, details = score_selection(exercise["correct_signs"], data.get("selected", []), 10)
    details["explanation"] = exercise["explanation"]
    save_activity(user["id"], "image-detection", "image", points, 10, details)
    return jsonify({"ok": True, "points": points, "max_points": 10, "details": details, "progress": get_progress(user["id"])})


@bp.post("/api/prompt/analyze")
@login_required
def analyze_prompt():
    user = current_user()
    prompt = normalize_prompt(str((request.get_json(silent=True) or {}).get("prompt", "")))
    if not prompt:
        return jsonify({"errors": ["Écrivez un prompt à tester."]}), 400
    if len(prompt) < 3:
        return jsonify({"errors": ["Le prompt est trop court."]}), 400
    if not current_app.config["GEMINI_API_KEY"]:
        return jsonify({
            "error": "ai_not_configured",
            "message": "Le laboratoire IA n'est pas encore configuré. Ajoutez GEMINI_API_KEY dans le fichier .env puis relancez l'application.",
        }), 503

    usage = prompt_usage(user["id"])
    if usage["remaining"] <= 0:
        return jsonify({"error": "prompt_limit_reached", "message": "La limite de 3 prompts de démonstration est atteinte."}), 429

    evaluation = evaluate_prompt(prompt)
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    db = get_db()
    cursor = db.execute(
        "INSERT INTO prompt_attempts(user_id, provider, prompt_sha256, status, created_at) VALUES (?, 'gemini', ?, 'started', ?)",
        (user["id"], prompt_hash, utc_now()),
    )
    db.commit()

    try:
        ai_result = analyze_with_gemini(
            current_app.config["GEMINI_API_KEY"],
            current_app.config["GEMINI_MODEL"],
            prompt,
            evaluation.improved_prompt,
        )
        db.execute("UPDATE prompt_attempts SET status = 'success' WHERE id = ?", (cursor.lastrowid,))
        db.commit()
    except Exception as exc:
        db.execute("UPDATE prompt_attempts SET status = 'failed' WHERE id = ?", (cursor.lastrowid,))
        db.commit()
        current_app.logger.exception("Erreur Gemini: %s", exc)
        return jsonify({
            "error": "ai_unavailable",
            "message": "Le service Gemini n'a pas répondu correctement. Vérifiez la clé, le modèle et les quotas, puis réessayez avec un autre compte de test si la limite est atteinte.",
            "prompt_usage": prompt_usage(user["id"]),
        }), 502

    improved_prompt = normalize_prompt(ai_result.get("improved_prompt", ""), 1800) or evaluation.improved_prompt
    save_activity(
        user["id"],
        "prompt-lab",
        "prompt",
        evaluation.points,
        20,
        {
            "provider": "gemini",
            "model": current_app.config["GEMINI_MODEL"],
            "checks": evaluation.checks,
            "prompt_sha256": prompt_hash,
        },
    )
    progress = get_progress(user["id"])
    return jsonify({
        "ok": True,
        "points": evaluation.points,
        "max_points": 20,
        "checks": evaluation.checks,
        "answer": ai_result["original_response"],
        "improved_prompt": improved_prompt,
        "improved_answer": ai_result["improved_response"],
        "defects": ai_result["defects"],
        "improvement_reasons": ai_result["improvement_reasons"],
        "pedagogical_advice": ai_result["pedagogical_advice"],
        "provider": "gemini",
        "model": current_app.config["GEMINI_MODEL"],
        "prompt_usage": progress["prompt_usage"],
        "progress": progress,
    })


@bp.get("/api/progress")
@login_required
def api_progress():
    return jsonify(get_progress(current_user()["id"]))


@bp.get("/api/account/export")
@login_required
def export_account():
    user = current_user()
    db = get_db()
    certificates = [dict(row) for row in db.execute(
        "SELECT certificate_id, score, issued_at FROM certificates WHERE user_id = ?", (user["id"],)
    ).fetchall()]
    payload = {
        "user": user_to_dict(user),
        "progress": get_progress(user["id"]),
        "certificates": certificates,
        "exported_at": utc_now(),
        "privacy_version": PRIVACY_VERSION,
        "note": "Les prompts ne sont pas conservés. Seule une empreinte SHA-256 technique est stockée pour chaque tentative.",
    }
    return Response(
        json.dumps(payload, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=export-mepa.json"},
    )


@bp.post("/api/account/delete")
@login_required
def delete_account():
    user = current_user()
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user["id"],))
    db.commit()
    return jsonify({"ok": True, "csrf_token": rotate_session()})


@bp.post("/certificate/download")
@login_required
def download_certificate():
    user = current_user()
    progress = get_progress(user["id"])
    if not progress["eligible"]:
        return jsonify({"error": "certificate_locked", "threshold": CERTIFICATION_THRESHOLD, "score": progress["score"]}), 403
    certificate_id = hashlib.sha256(f"{user['id']}:{user['email']}:{PRIVACY_VERSION}".encode()).hexdigest()[:12].upper()
    issued_date = datetime.now().strftime("%d/%m/%Y")
    db = get_db()
    db.execute(
        """
        INSERT INTO certificates(user_id, certificate_id, score, issued_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET score = excluded.score, issued_at = excluded.issued_at
        """,
        (user["id"], certificate_id, progress["score"], utc_now()),
    )
    db.commit()
    pdf = build_certificate_pdf(user["name"], progress["score"], certificate_id, issued_date)
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=certificat-mepa-{certificate_id}.pdf"},
    )


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})
