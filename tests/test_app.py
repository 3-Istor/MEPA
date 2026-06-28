import json
from types import SimpleNamespace

import pytest

from mepa import create_app
from mepa.ai_service import analyze_with_gemini
from mepa.db import get_db
from mepa.routes import classify_age


@pytest.fixture()
def app(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake-mp4-for-routing-test")
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "DATABASE_PATH": str(tmp_path / "test.sqlite"),
        "LOCAL_VIDEO_PATH": str(video),
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL": "test-model",
        "PROMPT_ATTEMPT_LIMIT": 3,
    })
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def csrf(client):
    response = client.get("/api/me")
    return response.get_json()["csrf_token"]


def post(client, path, payload=None, token=None):
    return client.post(
        path,
        data=json.dumps(payload or {}),
        content_type="application/json",
        headers={"X-CSRF-Token": token or csrf(client)},
    )


def register(client, email="test@example.com", age=18):
    token = csrf(client)
    response = post(client, "/api/register", {
        "name": "Lina",
        "email": email,
        "age": age,
        "role": "citoyen",
        "password": "Motdepasse123",
        "consent": True,
    }, token)
    assert response.status_code == 200
    return response.get_json()["csrf_token"]


def test_protected_endpoint_requires_authentication(client):
    response = client.get("/api/content")
    assert response.status_code == 401


def test_privacy_policy_is_public(client):
    response = client.get("/confidentialite")
    assert response.status_code == 200
    assert "Politique de confidentialité" in response.get_data(as_text=True)


def test_new_branding_and_removed_project_dates(client):
    page = client.get("/").get_data(as_text=True)
    assert "IA Citoyenne" in page
    assert "IA Clair" not in page
    assert "Projet lancé le 14 avril 2026" not in page
    assert "Projet étudiant MEPA - identité institutionnelle" not in page


def test_csrf_is_required(client):
    response = client.post("/api/register", json={})
    assert response.status_code == 403


def test_registration_content_and_answers_are_not_exposed(client):
    register(client)
    response = client.get("/api/content")
    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload["videos"]) == 3
    assert len(payload["videos"][0]["quiz"]) == 8
    assert "answer" not in payload["videos"][0]["quiz"][0]
    assert payload["videos"][0]["title"] == "Introduction à l'intelligence artificielle"
    assert payload["videos"][0]["source_type"] == "local"
    assert payload["videos"][0]["source_url"] == "/media/video-intro-ia"
    assert payload["videos"][1]["title"] == "Comment fonctionne une IA ?"
    assert payload["videos"][1]["source_type"] == "embed"
    assert payload["videos"][1]["source_url"].startswith("https://app.heygen.com/embeds/")
    assert payload["videos"][2]["available"] is False


def test_video_must_be_opened_before_completion(client):
    token = register(client)
    denied = post(client, "/api/videos/video-introduction-ia/complete", token=token)
    assert denied.status_code == 409
    opened = post(client, "/api/videos/video-introduction-ia/open", token=token)
    assert opened.status_code == 200
    completed = post(client, "/api/videos/video-introduction-ia/complete", token=token)
    assert completed.status_code == 200
    assert "video-introduction-ia" in completed.get_json()["progress"]["completed_videos"]


def test_video_quiz_is_corrected_server_side(client):
    token = register(client)
    post(client, "/api/videos/video-introduction-ia/open", token=token)
    answers = [0, 2, 1, 2, 0, 1, 2, 0]
    response = post(client, "/api/videos/video-introduction-ia/quiz", {"answers": answers}, token)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["correct_count"] == 8
    assert payload["points"] == 22


def test_each_video_question_can_be_checked_server_side(client):
    token = register(client)
    closed = post(client, "/api/videos/video-introduction-ia/quiz/check", {
        "question_index": 0,
        "answer": 0,
    }, token)
    assert closed.status_code == 409

    post(client, "/api/videos/video-introduction-ia/open", token=token)
    correct = post(client, "/api/videos/video-introduction-ia/quiz/check", {
        "question_index": 0,
        "answer": 0,
    }, token)
    assert correct.status_code == 200
    assert correct.get_json()["correct"] is True

    incorrect = post(client, "/api/videos/video-introduction-ia/quiz/check", {
        "question_index": 0,
        "answer": 1,
    }, token)
    assert incorrect.status_code == 200
    assert incorrect.get_json()["correct"] is False

    invalid = post(client, "/api/videos/video-introduction-ia/quiz/check", {
        "question_index": 99,
        "answer": 0,
    }, token)
    assert invalid.status_code == 400


def test_prompt_limit_and_full_structured_result(client, monkeypatch):
    token = register(client)

    def fake_ai(*_args, **_kwargs):
        return {
            "original_response": "Réponse initiale spécifique.",
            "improved_prompt": "Prompt amélioré spécifique.",
            "improved_response": "Réponse améliorée spécifique.",
            "defects": ["Contexte insuffisant"],
            "improvement_reasons": ["Le public est précisé"],
            "pedagogical_advice": ["Demander un format"],
        }

    monkeypatch.setattr("mepa.routes.analyze_with_gemini", fake_ai)
    for remaining in [2, 1, 0]:
        response = post(client, "/api/prompt/analyze", {"prompt": "Explique les biais algorithmiques à un élève avec une liste."}, token)
        assert response.status_code == 200
        assert response.get_json()["points"] == 20
        assert response.get_json()["prompt_usage"]["remaining"] == remaining
    blocked = post(client, "/api/prompt/analyze", {"prompt": "Un quatrième prompt valide."}, token)
    assert blocked.status_code == 429


def test_ai_configuration_error_does_not_consume_attempt(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "DATABASE_PATH": str(tmp_path / "no-ai.sqlite"),
        "GEMINI_API_KEY": "",
    })
    client = app.test_client()
    token = register(client, "noai@example.com")
    response = post(client, "/api/prompt/analyze", {"prompt": "Explique l'IA à un enfant."}, token)
    assert response.status_code == 503
    progress = client.get("/api/progress").get_json()
    assert progress["prompt_usage"]["used"] == 0


def test_ai_runtime_error_does_not_consume_attempt(client, monkeypatch):
    token = register(client)

    def unavailable(*_args, **_kwargs):
        raise RuntimeError("temporary_failure")

    monkeypatch.setattr("mepa.routes.analyze_with_gemini", unavailable)
    response = post(client, "/api/prompt/analyze", {"prompt": "Explique les biais avec des exemples."}, token)
    assert response.status_code == 502
    assert response.get_json()["prompt_usage"]["used"] == 0
    assert client.get("/api/progress").get_json()["prompt_usage"]["remaining"] == 3


def test_gemini_retries_transient_errors(monkeypatch):
    calls = {"count": 0}
    successful_payload = {
        "original_response": "Réponse initiale.",
        "improved_prompt": "Prompt amélioré.",
        "improved_response": "Réponse améliorée.",
        "defects": [],
        "improvement_reasons": ["Plus précis."],
        "pedagogical_advice": ["Vérifier les faits."],
    }

    class FakeModels:
        def generate_content(self, **_kwargs):
            calls["count"] += 1
            if calls["count"] < 3:
                raise RuntimeError("temporary_failure")
            return SimpleNamespace(text=json.dumps(successful_payload))

    class FakeClient:
        models = FakeModels()

    fake_genai = SimpleNamespace(Client=lambda **_kwargs: FakeClient())
    fake_types = SimpleNamespace(
        HttpOptions=lambda **_kwargs: object(),
        GenerateContentConfig=lambda **_kwargs: object(),
    )
    monkeypatch.setattr("mepa.ai_service.genai", fake_genai)
    monkeypatch.setattr("mepa.ai_service.types", fake_types)
    monkeypatch.setattr("mepa.ai_service.time.sleep", lambda _seconds: None)

    result = analyze_with_gemini("key", "model", "prompt", "suggestion", retry_attempts=3)
    assert calls["count"] == 3
    assert result == successful_payload


def test_age_groups_become_progressively_more_accessible():
    assert classify_age(17) == "jeune"
    assert classify_age(30) == "adulte"
    assert classify_age(50) == "mature"
    assert classify_age(65) == "senior"
    assert classify_age(80) == "grand_senior"


def test_local_video_route_is_protected_and_served(client):
    assert client.get("/media/video-intro-ia").status_code == 401
    register(client)
    response = client.get("/media/video-intro-ia")
    assert response.status_code == 200
    assert response.mimetype == "video/mp4"


def test_certificate_is_a_real_pdf(client, app):
    register(client)
    with app.app_context():
        db = get_db()
        user_id = db.execute("SELECT id FROM users").fetchone()[0]
        rows = [
            (user_id, "video-introduction-ia", "video", 5, 5, "{}", "2026-06-23T10:00:00+00:00"),
            (user_id, "video-fonctionnement-ia", "video", 5, 5, "{}", "2026-06-23T10:01:00+00:00"),
            (user_id, "video-introduction-ia-qcm", "video_quiz", 22, 22, "{}", "2026-06-23T10:02:00+00:00"),
            (user_id, "video-fonctionnement-ia-qcm", "video_quiz", 23, 23, "{}", "2026-06-23T10:03:00+00:00"),
            (user_id, "prompt-lab", "prompt", 20, 20, "{}", "2026-06-23T10:04:00+00:00"),
            (user_id, "arnaque-scenario", "scam", 15, 15, "{}", "2026-06-23T10:05:00+00:00"),
            (user_id, "image-detection", "image", 10, 10, "{}", "2026-06-23T10:06:00+00:00"),
        ]
        db.executemany(
            "INSERT INTO activities(user_id,module_id,activity_type,points,max_points,details,completed_at) VALUES(?,?,?,?,?,?,?)",
            rows,
        )
        db.commit()
    assert client.get("/api/progress").get_json()["score"] == 100
    response = post(client, "/certificate/download", token=csrf(client))
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")


def test_account_deletion_is_final(client, app):
    token = register(client)
    response = post(client, "/api/account/delete", token=token)
    assert response.status_code == 200
    assert client.get("/api/content").status_code == 401
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
