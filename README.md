# IA Clair — plateforme éducative IA

Prototype Flask + Bootstrap d’une plateforme française de sensibilisation à l’intelligence artificielle.

## Fonctionnalités

- Page d’entrée demandant uniquement l’âge
- Adaptation automatique : enfant, adolescent, adulte, senior
- Mode senior : grands textes, gros boutons, contraste renforcé, navigation simplifiée, synthèse vocale, bouton micro
- Vidéos éducatives par catégories
- Quiz interactif avec score, badges et classement
- Simulateur de prompts IA avec amélioration automatique
- Simulateur d’arnaques IA : faux SMS, mails, appels vocaux, messages administratifs
- Stockage simple des scores dans `data/scores.json`
- Emplacement prêt pour l’API OpenAI

## Installation

```bash
cd ia_sensibilisation
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Puis ouvrir : http://127.0.0.1:5000

## API IA facultative (OpenAI ou Gemini)

Sans clé API, le simulateur utilise une réponse pédagogique locale.

### Pour activer OpenAI :

```bash
export OPENAI_API_KEY="votre-cle"
export AI_PROVIDER="openai"
python app.py
```

### Pour activer Gemini :

```bash
export GEMINI_API_KEY="votre-cle"
export AI_PROVIDER="gemini"
export GEMINI_MODEL="gemini-1.5-flash"  # Optional, defaults to gemini-1.5-flash
python app.py
```

**Modèles Gemini disponibles :**
- `gemini-1.5-flash` (par défaut, rapide et efficace)
- `gemini-1.5-pro` (plus puissant, meilleure qualité)
- `gemini-pro` (version précédente)
- `gemini-2.0-flash-exp` (expérimental, dernière version)

Par défaut, le système utilise OpenAI si `AI_PROVIDER` n'est pas défini. Vous pouvez choisir entre "openai" ou "gemini".

## Structure

```text
ia_sensibilisation/
├── app.py
├── requirements.txt
├── data/scores.json
├── templates/index.html
└── static/
    ├── css/style.css
    └── js/app.js
```
