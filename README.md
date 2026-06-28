# IA Citoyenne / MEPA - plateforme de sensibilisation à l'intelligence artificielle

Version auditée et corrigée du projet Flask MEPA. L'interface garde une identité française institutionnelle, tout en indiquant clairement qu'il s'agit d'un projet étudiant et non d'un site officiel.

## Fonctionnalités de cette version

- Page d'accueil publique responsive et accessible.
- Inscription et connexion avec consentement RGPD, mots de passe hachés avec scrypt et sessions protégées.
- Deux vidéos disponibles et une troisième annoncée prochainement.
- Vidéo 1, « Introduction à l’intelligence artificielle », lue depuis le fichier local `Video intro a l'IA.mp4`.
- Vidéo 2, « Comment fonctionne une IA ? », intégrée depuis HeyGen.
- Obligation d'ouvrir une vidéo avant de pouvoir la marquer comme terminée ou valider son QCM.
- Deux QCM de 8 questions, corrigés uniquement côté serveur.
- Laboratoire de prompts Gemini : diagnostic, réponse initiale, prompt amélioré, réponse améliorée et explications.
- Jusqu'à trois tentatives Gemini automatiques en cas d'échec temporaire et limite serveur de 3 essais réussis par compte.
- Exercices anti-arnaques et détection d'images générées.
- Score sur 100 et vrai certificat PDF à partir de 70/100.
- Export JSON, politique de confidentialité dédiée et suppression définitive du compte.

Le détail des défauts trouvés et des corrections se trouve dans [`AUDIT.md`](AUDIT.md).

## 1. Installation locale

Depuis le dossier du projet :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Le fichier `.env` est déjà inclus dans cette archive avec une clé Flask aléatoire. Il suffit d'y ajouter votre `GEMINI_API_KEY` lorsque vous en aurez une. Ne publiez jamais ce fichier dans GitHub.

## 2. Configurer Gemini gratuitement

1. Créez une clé API dans Google AI Studio.
2. Ajoutez-la uniquement dans le fichier `.env` :

```env
GEMINI_API_KEY=votre_cle_ici
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_RETRY_ATTEMPTS=3
PROMPT_ATTEMPT_LIMIT=3
```

La clé ne doit jamais être écrite dans `static/js/app.js`, dans un dépôt Git ou dans le navigateur. L'application réessaie automatiquement jusqu'à trois fois en cas d'échec temporaire. Seuls les essais réussis sont décomptés, et le quatrième succès est bloqué pour chaque compte.

Les quotas gratuits sont gérés par Google et peuvent varier selon le projet. Consultez vos limites actives dans Google AI Studio.

## 3. Ajouter la vidéo locale

Le fichier doit porter exactement ce nom :

```text
Video intro a l'IA.mp4
```

Placez-le à la racine du projet, au même niveau que `app.py` :

```text
Video intro a l'IA.mp4
app.py
templates/
static/
...
```

Dans votre cas, décompressez directement l'archive dans :

```text
/home/joebuntu/Desktop/SIGL/MEPA/MEPA
```

Le fichier `Video intro a l'IA.mp4` déjà présent dans ce dossier sera détecté automatiquement. L'archive ne crée aucun sous-dossier `MEPA` supplémentaire.

Une autre possibilité consiste à définir un chemin absolu :

```env
LOCAL_VIDEO_PATH=/home/joebuntu/Desktop/SIGL/MEPA/MEPA/Video intro a l'IA.mp4
```

## 4. Lancer le site

```bash
source .venv/bin/activate
python app.py
```

Ouvrez ensuite :

```text
http://127.0.0.1:5000
```

Pour tester avec Gunicorn, plus proche de la production :

```bash
source .venv/bin/activate
gunicorn --bind 127.0.0.1:8000 --workers 2 --threads 4 --timeout 90 app:app
```

## 5. Lancer les tests automatisés

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

Les tests vérifient notamment :

- l'authentification et le CSRF ;
- la protection des routes ;
- l'impossibilité de valider une vidéo non ouverte ;
- les QCM côté serveur ;
- la limite de trois prompts ;
- la génération du certificat PDF ;
- la suppression définitive du compte.

## 6. Scénario de test manuel conseillé

1. Créez un compte avec un mot de passe contenant au moins 10 caractères, une lettre et un chiffre.
2. Ouvrez la première vidéo locale « Introduction à l’intelligence artificielle », puis marquez-la comme terminée.
3. Répondez aux 8 questions du QCM et vérifiez les corrections.
4. Ouvrez la deuxième vidéo et vérifiez que la capsule HeyGen « Comment fonctionne une IA ? » s’affiche correctement.
5. Testez trois prompts différents ; le quatrième doit être bloqué.
6. Réalisez les deux exercices anti-arnaques.
7. Vérifiez l'export des données dans l'onglet Compte.
8. Une fois 70 points atteints, téléchargez le certificat PDF.

## 7. Arborescence

```text
./
├── app.py
├── mepa/
│   ├── __init__.py
│   ├── ai_service.py
│   ├── config.py
│   ├── content.py
│   ├── db.py
│   ├── pdf_service.py
│   ├── routes.py
│   └── security.py
├── templates/
│   ├── index.html
│   └── privacy.html
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   ├── img/
│   └── videos/README.txt
├── tests/
│   └── test_app.py
├── data/.gitkeep
├── AUDIT.md
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── .env
├── .env.example
└── Dockerfile
```

## 8. Base de données

SQLite est créée automatiquement dans :

```text
data/mepa.sqlite
```

Tables :

- `users` : comptes et consentement ;
- `activities` : scores et progression ;
- `video_views` : preuve d'ouverture des vidéos ;
- `prompt_attempts` : compteur, statut et empreinte technique des essais ;
- `certificates` : certificats émis ;
- `rate_limit_events` : limitation des inscriptions et connexions.

Pour réinitialiser uniquement votre environnement de développement :

```bash
rm -f data/mepa.sqlite data/mepa.sqlite-shm data/mepa.sqlite-wal
python app.py
```

## 9. Docker

Le MP4 doit être monté séparément afin d'éviter une image Docker trop lourde :

```bash
docker build -t mepa-ia-clair .
docker run --rm -p 8000:8000 \
  --env-file .env \
  -v "$PWD/Video intro a l'IA.mp4:/app/Video intro a l'IA.mp4:ro" \
  -v "$PWD/data:/app/data" \
  mepa-ia-clair
```

## 10. À changer impérativement avant déploiement

### Déploiement Kubernetes avec Helm

Le fichier `.env` n'est volontairement jamais copié dans l'image Docker. Créez
un Secret Kubernetes, puis demandez au chart de l'utiliser :

```bash
kubectl create secret generic ia-clair-runtime \
  --from-literal=SECRET_KEY='une-valeur-longue-et-aleatoire' \
  --from-literal=GEMINI_API_KEY='votre-cle-gemini'

helm upgrade --install ia-clair ./helm/ia-clair \
  --set secrets.create=false \
  --set secrets.existingSecret=ia-clair-runtime
```

Après le déploiement, `/health` doit indiquer
`"gemini_configured": true`. Le chart configure aussi les délais NGINX pour
laisser les nouvelles tentatives Gemini se terminer.

- Remplacer `SECRET_KEY` par une valeur longue et aléatoire.
- Activer HTTPS et mettre `SESSION_COOKIE_SECURE=true`.
- Ne jamais publier `GEMINI_API_KEY` ; utiliser les secrets de l'hébergeur.
- Désactiver définitivement `FLASK_DEBUG`.
- Conserver une base persistante et sauvegardée. Pour plusieurs instances, migrer vers PostgreSQL et un outil de migrations.
- Remplacer la limitation SQLite par Redis ou une solution distribuée si plusieurs workers ou serveurs sont utilisés à grande échelle.
- Ajouter vérification d'e-mail, réinitialisation de mot de passe et éventuellement authentification multifacteur.
- Faire valider les mentions légales, la politique de confidentialité, les durées de conservation et le consentement par un responsable RGPD.
- Vérifier les droits d'utilisation des vidéos, images, logos et contenus pédagogiques.
- Ajouter journalisation centralisée, alertes, sauvegardes testées et supervision.
- Effectuer un audit d'accessibilité RGAA et des tests sur lecteurs d'écran.
- Vérifier que l'intégration HeyGen reste autorisée par la politique CSP et par les conditions de la plateforme.
- Définir des quotas Gemini adaptés au budget et surveiller les limites dans Google AI Studio.
- Placer l'application derrière un reverse proxy correctement configuré avant d'activer `TRUST_PROXY=true`.

## Limites connues

- SQLite convient à la soutenance et à un petit déploiement, mais pas à une forte concurrence.
- Le lecteur HeyGen est externe ; son suivi de lecture précis n'est pas accessible à cause de l'isolation entre domaines. MEPA enregistre donc l'ouverture de la capsule, comme demandé.
- Le fichier MP4 n'est pas inclus dans cette archive, car il n'était pas présent dans le ZIP reçu. Le code détecte automatiquement le fichier déjà présent dans votre dépôt local.
