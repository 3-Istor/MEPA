import json
import re
from dataclasses import dataclass

try:
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover - testé via le mode non configuré
    genai = None
    types = None


@dataclass
class PromptEvaluation:
    points: int
    checks: list[dict]
    improved_prompt: str


def normalize_prompt(value: str, limit: int = 1500) -> str:
    value = (value or "").replace("\x00", "").strip()
    value = re.sub(r"[\t ]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value[:limit]


def evaluate_prompt(prompt: str) -> PromptEvaluation:
    text = prompt.lower()
    words = re.findall(r"[a-zàâçéèêëîïôûùüÿñæœ0-9'-]+", text)
    checks = [
        {
            "key": "objectif",
            "label": "Objectif précis",
            "ok": len(words) >= 8 or "?" in prompt,
            "tip": "Indique exactement le résultat attendu.",
        },
        {
            "key": "contexte",
            "label": "Contexte ou public",
            "ok": any(k in text for k in ["pour", "niveau", "élève", "classe", "enseignant", "public", "contexte", "je suis"]),
            "tip": "Précise le public, le niveau ou la situation.",
        },
        {
            "key": "format",
            "label": "Format attendu",
            "ok": any(k in text for k in ["liste", "tableau", "étapes", "points", "résumé", "plan", "exemple", "mots", "lignes"]),
            "tip": "Demande une liste, un tableau, un plan, une longueur ou des étapes.",
        },
        {
            "key": "verification",
            "label": "Vérification et limites",
            "ok": any(k in text for k in ["source", "sources", "vérifie", "fiable", "limite", "incertitude", "compare", "signale"]),
            "tip": "Demande les limites, incertitudes ou éléments à vérifier.",
        },
    ]
    points = sum(5 for check in checks if check["ok"])
    clean = normalize_prompt(prompt, 1000)
    improved = (
        "Tu es un assistant pédagogique rigoureux. Réponds à la demande suivante : "
        f"« {clean} ». Adapte le niveau à un public débutant sauf indication contraire. "
        "Structure la réponse avec des titres courts et des exemples concrets. "
        "Distingue clairement les faits, les hypothèses et les informations à vérifier. "
        "Termine par un résumé pratique et cite les types de sources fiables à consulter."
    )
    return PromptEvaluation(points=points, checks=checks, improved_prompt=improved)


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "original_response": {"type": "string"},
        "improved_prompt": {"type": "string"},
        "improved_response": {"type": "string"},
        "defects": {"type": "array", "items": {"type": "string"}},
        "improvement_reasons": {"type": "array", "items": {"type": "string"}},
        "pedagogical_advice": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "original_response",
        "improved_prompt",
        "improved_response",
        "defects",
        "improvement_reasons",
        "pedagogical_advice",
    ],
}


def analyze_with_gemini(api_key: str, model: str, prompt: str, suggested_prompt: str) -> dict:
    if not api_key:
        raise RuntimeError("ai_not_configured")
    if genai is None or types is None:
        raise RuntimeError("google_genai_not_installed")

    instruction = f"""
Tu es le moteur du laboratoire de prompts d'une plateforme française d'éducation à l'IA.
Analyse le prompt utilisateur ci-dessous, puis réponds réellement à ce prompt.
Ensuite, améliore le prompt et réponds réellement à la version améliorée.
Explique précisément pourquoi la nouvelle version est meilleure.

Contraintes :
- Répondre en français, sauf demande explicite d'une autre langue.
- Ne jamais inventer de sources ou de faits. Signaler les incertitudes.
- Ne pas reproduire de donnée personnelle sensible dans les conseils.
- Pour une demande dangereuse ou illégale, refuser brièvement et proposer une alternative sûre.
- Les deux réponses doivent être utiles, spécifiques au sujet et différentes si l'amélioration apporte plus de précision.
- Rester concis : environ 180 mots maximum par réponse.

Prompt utilisateur :
{prompt}

Proposition heuristique à utiliser comme point de départ, sans obligation de la recopier :
{suggested_prompt}
""".strip()

    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=30000))
    response = client.models.generate_content(
        model=model,
        contents=instruction,
        config=types.GenerateContentConfig(
            temperature=0.25,
            max_output_tokens=1800,
            response_mime_type="application/json",
            response_json_schema=RESPONSE_SCHEMA,
        ),
    )
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("empty_ai_response")
    payload = json.loads(text)
    for key in RESPONSE_SCHEMA["required"]:
        if key not in payload:
            raise RuntimeError("invalid_ai_response")
    return payload
