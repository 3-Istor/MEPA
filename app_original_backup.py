import json
import os
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, render_template, request

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "scores.json"

app = Flask(__name__)

AGE_GROUPS = [
    {"key": "enfant", "label": "Enfant", "min": 0, "max": 12},
    {"key": "adolescent", "label": "Adolescent", "min": 13, "max": 17},
    {"key": "adulte", "label": "Adulte", "min": 18, "max": 64},
    {"key": "senior", "label": "Senior", "min": 65, "max": 130},
]

VIDEO_CATEGORIES = [
    "Découverte de l’IA",
    "Dangers de l’IA",
    "Fake news",
    "Deepfakes",
    "Cybersécurité",
    "IA à l’école",
    "IA dans la vie quotidienne",
    "Espace seniors",
]

QUIZ_QUESTIONS = [
    {
        "question": "Quel est le meilleur réflexe face à une information surprenante générée par IA ?",
        "choices": ["La partager vite", "Vérifier la source", "Croire l’image", "Répondre immédiatement"],
        "answer": 1,
        "explanation": "Une source officielle ou reconnue permet de limiter les fake news et manipulations.",
    },
    {
        "question": "Un deepfake est :",
        "choices": ["Une vidéo modifiée par IA", "Un antivirus", "Un moteur de recherche", "Un mot de passe"],
        "answer": 0,
        "explanation": "Les deepfakes peuvent imiter une voix ou un visage. Il faut vérifier avant de croire.",
    },
    {
        "question": "Pour bien demander quelque chose à une IA, il faut :",
        "choices": ["Être vague", "Donner du contexte", "Écrire en majuscules", "Ne poser qu’un mot"],
        "answer": 1,
        "explanation": "Un bon prompt précise le rôle, le contexte, le public et le format attendu.",
    },
]

SCAMS = [
    {
        "type": "Faux SMS administratif",
        "message": "AMELI: Votre carte vitale expire aujourd’hui. Cliquez ici pour éviter une amende: http://maj-droits-securite.info",
        "suspects": ["urgence", "lien non officiel", "menace d’amende"],
        "advice": "Ne cliquez jamais sur un lien reçu par SMS. Passez par le site officiel depuis votre navigateur.",
    },
    {
        "type": "Faux mail bancaire",
        "message": "Bonjour, votre conseiller bancaire demande vos codes pour bloquer une fraude IA en cours. Répondez vite.",
        "suspects": ["demande de codes", "pression", "prétexte technique"],
        "advice": "Une banque ne demande jamais vos codes par mail, SMS ou téléphone.",
    },
    {
        "type": "Faux appel vocal",
        "message": "Une voix ressemblant à un proche demande un virement urgent pour régler un problème.",
        "suspects": ["voix imitée", "demande d’argent", "urgence émotionnelle"],
        "advice": "Raccrochez et rappelez la personne avec son numéro habituel.",
    },
]


def classify_age(age: int) -> str:
    for group in AGE_GROUPS:
        if group["min"] <= age <= group["max"]:
            return group["key"]
    return "adulte"


def load_scores():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_scores(scores):
    DATA_FILE.write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")


def fallback_ai_response(prompt: str, age_group: str):
    simple = age_group in {"enfant", "senior"}
    response = (
        "L’intelligence artificielle est un outil informatique qui peut aider à écrire, résumer, traduire, "
        "chercher des idées ou repérer certains risques. Elle peut se tromper : il faut vérifier les informations importantes."
    )
    tips = [
        "Préciser le sujet exact.",
        "Dire pour qui la réponse est destinée.",
        "Demander un format clair : liste, étapes, exemple.",
        "Ajouter une limite : réponse courte, niveau débutant, sources à vérifier.",
    ]
    improved = "Explique-moi l’intelligence artificielle en 5 phrases simples, avec 2 exemples de la vie quotidienne et 2 précautions à prendre."
    if simple:
        improved = "Explique-moi l’IA avec des mots simples, en 5 phrases, avec un exemple concret et un conseil de prudence."
    if len(prompt.strip()) > 40:
        response = "Votre demande est déjà assez précise. Je peux y répondre, mais elle serait encore meilleure avec un public cible et un format attendu."
    return {"answer": response, "tips": tips, "improved_prompt": improved, "used_openai": False}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/profile", methods=["POST"])
def profile():
    data = request.get_json(force=True)
    age = int(data.get("age", 18))
    group = classify_age(age)
    return jsonify({"age": age, "group": group, "groups": AGE_GROUPS})


@app.route("/api/content")
def content():
    return jsonify({"videos": VIDEO_CATEGORIES, "quiz": QUIZ_QUESTIONS, "scams": SCAMS})


@app.route("/api/quiz/submit", methods=["POST"])
def submit_quiz():
    data = request.get_json(force=True)
    age_group = data.get("age_group", "adulte")
    score = int(data.get("score", 0))
    name = (data.get("name") or "Citoyen anonyme")[:40]
    entry = {
        "name": name,
        "age_group": age_group,
        "score": score,
        "date": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    scores = load_scores()
    scores.append(entry)
    scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)[:100]
    save_scores(scores)
    return jsonify({"saved": True, "entry": entry, "national": scores[:10], "age_group": [s for s in scores if s.get("age_group") == age_group][:10]})


@app.route("/api/ranking")
def ranking():
    age_group = request.args.get("age_group")
    scores = load_scores()
    national = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)[:10]
    by_age = [s for s in national if not age_group or s.get("age_group") == age_group]
    return jsonify({"national": national, "age_group": by_age})


@app.route("/api/prompt", methods=["POST"])
def prompt_simulator():
    data = request.get_json(force=True)
    prompt = (data.get("prompt") or "").strip()
    age_group = data.get("age_group", "adulte")
    if not prompt:
        return jsonify({"error": "Prompt vide"}), 400

    api_key = os.getenv("OPENAI_API_KEY")
    if OpenAI and api_key:
        client = OpenAI(api_key=api_key)
        system = (
            "Tu es un assistant pédagogique français sur l'intelligence artificielle. "
            "Réponds avec prudence, clarté, accessibilité et propose toujours une amélioration du prompt."
        )
        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Public: {age_group}. Prompt à analyser: {prompt}"},
            ],
            temperature=0.4,
        )
        text = completion.choices[0].message.content
        return jsonify({
            "answer": text,
            "tips": ["Ajoutez le contexte", "Précisez le public", "Demandez un format", "Indiquez le niveau souhaité"],
            "improved_prompt": f"Pour un public {age_group}, explique clairement: {prompt}. Donne une réponse structurée, avec exemples et précautions.",
            "used_openai": True,
        })

    return jsonify(fallback_ai_response(prompt, age_group))


if __name__ == "__main__":
    app.run(debug=True)
