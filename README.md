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

## API OpenAI facultative

Sans clé API, le simulateur utilise une réponse pédagogique locale.

Pour activer OpenAI :

```bash
export OPENAI_API_KEY="votre-cle"
export OPENAI_MODEL="gpt-4o-mini"
python app.py
```

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
