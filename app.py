import json
import os
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, render_template, request

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    import google.generativeai as genai
except Exception:
    genai = None

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "scores.json"

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")  # Default to gemini-1.5-flash
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()  # "openai" or "gemini"

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OpenAI and OPENAI_API_KEY else None
gemini_model = None

if genai and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(GEMINI_MODEL)

AGE_GROUPS = [
    {"key": "enfant", "label": "Enfant", "min": 0, "max": 12},
    {"key": "adolescent", "label": "Adolescent", "min": 13, "max": 17},
    {"key": "adulte", "label": "Adulte", "min": 18, "max": 64},
    {"key": "senior", "label": "Senior", "min": 65, "max": 130},
]

VIDEO_CATEGORIES = [
    "Découverte de l'IA",
    "Dangers de l'IA",
    "Fake news",
    "Deepfakes",
    "Cybersécurité",
    "IA à l'école",
    "IA dans la vie quotidienne",
    "Espace seniors",
]

QUIZ_QUESTIONS = [
    {
        "question": "Quel est le meilleur réflexe face à une information surprenante générée par IA ?",
        "choices": ["La partager vite", "Vérifier la source", "Croire l'image", "Répondre immédiatement"],
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
        "choices": ["Être vague", "Donner du contexte", "Écrire en majuscules", "Ne poser qu'un mot"],
        "answer": 1,
        "explanation": "Un bon prompt précise le rôle, le contexte, le public et le format attendu.",
    },
]

SCAMS = [
    {
        "type": "Faux SMS administratif",
        "message": "AMELI: Votre carte vitale expire aujourd'hui. Cliquez ici pour éviter une amende: http://maj-droits-securite.info",
        "suspects": ["urgence", "lien non officiel", "menace d'amende"],
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
        "suspects": ["voix imitée", "demande d'argent", "urgence émotionnelle"],
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
    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")


def fallback_ai_response(prompt: str, age_group: str):
    simple = age_group in {"enfant", "senior"}

    answer = f"""
Réponse de l'IA :
Je peux t'aider sur ce sujet : {prompt}

Comme le mode IA n'est pas activé, voici une réponse pédagogique simple :
l'intelligence artificielle peut aider à expliquer, résumer, traduire, organiser des idées ou repérer certains risques.
Mais elle peut aussi se tromper, donc il faut toujours vérifier les informations importantes.

Analyse du prompt :
Ton prompt est compréhensible, mais il peut être amélioré en ajoutant le niveau, le format attendu et le contexte.

Conseils d'amélioration :
- précise si tu veux une réponse courte ou détaillée ;
- indique ton niveau ;
- demande des exemples ;
- demande un résumé final.
"""

    tips = [
        "Préciser le sujet exact.",
        "Dire pour qui la réponse est destinée.",
        "Demander un format clair : liste, étapes, exemple.",
        "Ajouter une limite : réponse courte, niveau débutant, sources à vérifier.",
    ]

    improved_prompt = (
        f"Explique-moi clairement : {prompt}. "
        "Donne des exemples simples, adapte la réponse à mon niveau et termine par un résumé."
    )

    if simple:
        improved_prompt = (
            f"Explique-moi avec des mots simples : {prompt}. "
            "Fais court, rassurant, avec un exemple concret."
        )

    return {
        "answer": answer,
        "tips": tips,
        "improved_prompt": improved_prompt,
        "used_openai": False,
        "used_gemini": False,
    }


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

    return jsonify({
        "saved": True,
        "entry": entry,
        "national": scores[:10],
        "age_group": [s for s in scores if s.get("age_group") == age_group][:10],
    })


@app.route("/api/ranking")
def ranking():
    age_group = request.args.get("age_group")
    scores = load_scores()
    national = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)[:10]
    by_age = [s for s in national if not age_group or s.get("age_group") == age_group]
    return jsonify({"national": national, "age_group": by_age})


@app.route("/api/prompt", methods=["POST"])
@app.route("/simulate_prompt", methods=["POST"])
def simulate_prompt():
    data = request.get_json(silent=True) or {}

    prompt = (data.get("prompt") or "").strip()
    age_mode = (
        data.get("ageMode")
        or data.get("age")
        or data.get("age_group")
        or "adulte"
    )

    if not prompt:
        message = "Écris d'abord un prompt pour que je puisse répondre."
        return jsonify({
            "answer": message,
            "response": message,
            "tips": [
                "Ajoute un sujet précis.",
                "Indique le niveau souhaité.",
                "Précise le format attendu.",
            ],
            "improved_prompt": "Explique-moi un sujet précis avec des mots simples, des exemples et un résumé final.",
            "used_openai": False,
            "used_gemini": False,
        })

    if openai_client is None and gemini_model is None:
        fallback = fallback_ai_response(prompt, age_mode)
        return jsonify({
            "answer": fallback["answer"],
            "response": fallback["answer"],
            "tips": fallback["tips"],
            "improved_prompt": fallback["improved_prompt"],
            "used_openai": False,
            "used_gemini": False,
        })

    try:
        system_message = f"""
Tu es l'assistant pédagogique officiel de la plateforme MEPA.

Tu réponds uniquement en texte.
Jamais d'image.

Tu es :
- clair
- rassurant
- éducatif
- moderne
- adapté au profil : {age_mode}

Tu réponds toujours en français.

Structure toujours ta réponse comme ceci :
1. Réponse de l'IA
2. Analyse du prompt
3. Conseils d'amélioration
4. Prompt amélioré
"""

        answer = None
        used_provider = None

        # Try Gemini if it's the preferred provider or if OpenAI is not available
        if (AI_PROVIDER == "gemini" and gemini_model) or (AI_PROVIDER == "gemini" and not openai_client):
            full_prompt = f"{system_message}\n\nQuestion de l'utilisateur : {prompt}"
            response = gemini_model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=900,
                )
            )
            answer = response.text.strip()
            used_provider = "gemini"
        
        # Try OpenAI if it's the preferred provider or if Gemini failed
        elif openai_client:
            completion = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=900,
            )
            answer = completion.choices[0].message.content.strip()
            used_provider = "openai"

        if answer is None:
            raise Exception("No AI provider available")

        improved_prompt = (
            f"Explique-moi clairement : {prompt}. "
            "Donne des exemples simples, adapte la réponse à mon niveau et termine par un résumé."
        )

        return jsonify({
            "answer": answer,
            "response": answer,
            "tips": [
                "Précise le contexte.",
                "Indique le niveau de détail souhaité.",
                "Demande un format clair : liste, exemple, étapes ou résumé.",
            ],
            "improved_prompt": improved_prompt,
            "used_openai": used_provider == "openai",
            "used_gemini": used_provider == "gemini",
            "provider": used_provider,
        })

    except Exception as e:
        fallback = fallback_ai_response(prompt, age_mode)
        return jsonify({
            "answer": fallback["answer"],
            "response": fallback["answer"],
            "tips": fallback["tips"],
            "improved_prompt": fallback["improved_prompt"],
            "used_openai": False,
            "used_gemini": False,
            "error": str(e),
        })


if __name__ == "__main__":
    app.run(debug=True)
