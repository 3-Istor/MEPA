"""Contenus pédagogiques statiques de MEPA.

Les réponses des QCM restent exclusivement côté serveur. Les routes publiques
n'exposent que les questions et choix nécessaires à l'interface.
"""

VIDEO_MODULES = [
    {
        "id": "video-introduction-ia",
        "title": "Introduction à l'intelligence artificielle",
        "duration": "Vidéo locale",
        "summary": "Découvrir ce qu'est l'IA, les données, les algorithmes, l'apprentissage automatique et les usages courants.",
        "takeaways": [
            "Distinguer IA, algorithme, modèle et données",
            "Comprendre ce que produit une IA générative",
            "Toujours vérifier une réponse importante",
        ],
        "source_type": "local",
        "source_url": "/media/video-intro-ia",
        "completion_points": 5,
        "quiz_points": 22,
        "available": True,
    },
    {
        "id": "video-fonctionnement-ia",
        "title": "Comment fonctionne une IA ?",
        "duration": "Capsule HeyGen",
        "summary": "Comprendre l'entraînement, les modèles, les prompts, les erreurs possibles et les bonnes pratiques.",
        "takeaways": [
            "Une IA apprend à partir de nombreux exemples",
            "Le modèle répond à partir d'une consigne",
            "Les données sensibles ne doivent pas être transmises",
        ],
        "source_type": "embed",
        "source_url": "https://app.heygen.com/embeds/4f886bd2c8114f659a8d4cc0a7455247",
        "completion_points": 5,
        "quiz_points": 23,
        "available": True,
    },
    {
        "id": "video-3-bientot",
        "title": "Vidéo 3 - Arrive bientôt",
        "duration": "Prochainement",
        "summary": "Une troisième capsule pédagogique sera ajoutée prochainement.",
        "takeaways": ["Le contenu et son QCM seront annoncés dans une prochaine version."],
        "source_type": "coming_soon",
        "source_url": None,
        "completion_points": 0,
        "quiz_points": 0,
        "available": False,
    },
]

VIDEO_QUIZZES = {
    "video-introduction-ia": [
        {
            "question": "Qu'est-ce que l'intelligence artificielle ?",
            "choices": [
                "Un système capable d'effectuer certaines tâches associées à l'intelligence humaine.",
                "Un robot capable de remplacer tous les métiers.",
                "Un ordinateur plus rapide que les autres.",
                "Un réseau internet spécialisé.",
            ],
            "answer": 0,
        },
        {
            "question": "Parmi les exemples suivants, lequel utilise souvent l'IA ?",
            "choices": [
                "Une prise électrique.",
                "Un cahier papier.",
                "Un moteur de recommandation de vidéos.",
                "Une règle graduée.",
            ],
            "answer": 2,
        },
        {
            "question": "Que signifie le terme « données » ?",
            "choices": [
                "Les résultats finaux d'une IA.",
                "Les informations utilisées pour apprendre.",
                "Les erreurs produites par une IA.",
                "Les programmes installés sur un ordinateur.",
            ],
            "answer": 1,
        },
        {
            "question": "Un algorithme est :",
            "choices": [
                "Une base de données.",
                "Une vidéo produite par une IA.",
                "Une suite d'instructions permettant d'effectuer une tâche.",
                "Un document numérique.",
            ],
            "answer": 2,
        },
        {
            "question": "L'apprentissage automatique permet à une IA :",
            "choices": [
                "D'apprendre à partir d'exemples.",
                "De se connecter à internet.",
                "De remplacer les enseignants.",
                "De stocker plus de fichiers.",
            ],
            "answer": 0,
        },
        {
            "question": "L'IA générative sert principalement à :",
            "choices": [
                "Réparer des ordinateurs.",
                "Créer du contenu comme du texte ou des images.",
                "Augmenter la mémoire d'un ordinateur.",
                "Scanner des documents papier.",
            ],
            "answer": 1,
        },
        {
            "question": "Dans l'éducation, une IA peut notamment :",
            "choices": [
                "Corriger automatiquement tous les examens.",
                "Supprimer le besoin d'enseignants.",
                "Préparer des supports ou résumer un document.",
                "Garantir des réponses toujours exactes.",
            ],
            "answer": 2,
        },
        {
            "question": "Pourquoi faut-il vérifier les réponses d'une IA ?",
            "choices": [
                "Parce qu'elle peut produire des erreurs.",
                "Parce qu'elle est toujours hors ligne.",
                "Parce qu'elle ne comprend que l'anglais.",
                "Parce qu'elle ne fonctionne que sur téléphone.",
            ],
            "answer": 0,
        },
    ],
    "video-fonctionnement-ia": [
        {
            "question": "Quel est le premier élément nécessaire à l'apprentissage d'une IA ?",
            "choices": ["Un prompt.", "Une connexion internet.", "Des données.", "Une imprimante."],
            "answer": 2,
        },
        {
            "question": "Pendant l'entraînement, une IA :",
            "choices": [
                "Analyse de nombreux exemples.",
                "Change automatiquement de matériel.",
                "Crée un nouveau système d'exploitation.",
                "Supprime ses données.",
            ],
            "answer": 0,
        },
        {
            "question": "Le résultat de l'entraînement d'une IA est appelé :",
            "choices": ["Un navigateur.", "Un modèle.", "Une image.", "Une base réseau."],
            "answer": 1,
        },
        {
            "question": "Qu'est-ce qu'un prompt ?",
            "choices": ["Un type d'ordinateur.", "Une erreur informatique.", "Une consigne donnée à l'IA.", "Une donnée d'entraînement."],
            "answer": 2,
        },
        {
            "question": "Une IA générative produit une réponse à partir :",
            "choices": [
                "D'un modèle entraîné et d'une consigne.",
                "D'une imprimante connectée.",
                "D'un antivirus.",
                "D'un disque dur externe.",
            ],
            "answer": 0,
        },
        {
            "question": "Quelle affirmation est correcte ?",
            "choices": [
                "Une IA ne peut jamais se tromper.",
                "Une IA remplace toujours le jugement humain.",
                "Une IA vérifie automatiquement toutes ses réponses.",
                "Une IA peut produire des informations inexactes.",
            ],
            "answer": 3,
        },
        {
            "question": "Quelle bonne pratique faut-il adopter ?",
            "choices": [
                "Partager ses mots de passe avec l'IA.",
                "Vérifier les informations obtenues.",
                "Accepter toutes les réponses sans contrôle.",
                "Désactiver les sources d'information.",
            ],
            "answer": 1,
        },
        {
            "question": "Que faut-il éviter de transmettre à une IA publique ?",
            "choices": ["Des données personnelles sensibles.", "Une question de cours.", "Une demande de résumé.", "Un texte public."],
            "answer": 0,
        },
    ],
}

SCAM_SCENARIOS = [
    {
        "id": "sms-carte-vitale",
        "kind": "Faux SMS administratif",
        "message": "AMELI - Votre carte Vitale expire ce soir. Dernier rappel avant amende : validez vos droits sur https://ameli-droits-securite.info",
        "correct_signs": ["urgence", "menace", "lien-non-officiel"],
        "signs": [
            {"key": "urgence", "label": "Urgence artificielle"},
            {"key": "menace", "label": "Menace d'amende"},
            {"key": "lien-non-officiel", "label": "Adresse non officielle"},
            {"key": "politesse", "label": "Formule de politesse"},
        ],
        "explanation": "Les services publics ne demandent pas de valider des droits via un lien étrange reçu par SMS. Ouvrez vous-même le site officiel depuis votre navigateur.",
    },
    {
        "id": "mail-banque-ia",
        "kind": "Faux courriel bancaire",
        "message": "Votre conseiller détecte une fraude IA. Répondez avec votre identifiant, mot de passe et code reçu par SMS afin de bloquer l'opération.",
        "correct_signs": ["demande-codes", "pression", "pretexte-technique"],
        "signs": [
            {"key": "demande-codes", "label": "Demande de codes secrets"},
            {"key": "pression", "label": "Pression pour répondre vite"},
            {"key": "pretexte-technique", "label": "Prétexte technique flou"},
            {"key": "bonjour", "label": "Présence d'un bonjour"},
        ],
        "explanation": "Une banque ne demande jamais le mot de passe ni le code SMS. Contactez-la via son application ou son numéro officiel.",
    },
    {
        "id": "appel-voix-proche",
        "kind": "Faux appel vocal cloné",
        "message": "Une voix qui ressemble à votre frère dit : « Je suis au commissariat, envoie 480 € maintenant et ne préviens personne. »",
        "correct_signs": ["voix-imitee", "demande-argent", "secret"],
        "signs": [
            {"key": "voix-imitee", "label": "Voix possiblement imitée"},
            {"key": "demande-argent", "label": "Demande d'argent"},
            {"key": "secret", "label": "Demande de garder le secret"},
            {"key": "montant", "label": "Montant précis"},
        ],
        "explanation": "Raccrochez et rappelez la personne avec son numéro habituel. Les fraudeurs exploitent l'émotion et l'urgence.",
    },
]

IMAGE_EXERCISES = [
    {
        "id": "portrait-main-six-doigts",
        "title": "Photo synthétique : portrait avec anomalie de main",
        "image": "/static/img/exercice-main-six-doigts.svg",
        "prompt_hint": "Image pédagogique inspirée des générateurs d'images IA.",
        "correct_signs": ["six-doigts", "texte-incoherent", "ombres-incoherentes"],
        "signs": [
            {"key": "six-doigts", "label": "Main avec trop de doigts"},
            {"key": "texte-incoherent", "label": "Texte flou ou incohérent"},
            {"key": "ombres-incoherentes", "label": "Ombres et lumière contradictoires"},
            {"key": "fond-bleu", "label": "Fond bleu"},
        ],
        "explanation": "Les détails fins, les mains, les textes et les ombres restent de bons indices, même si les générateurs progressent vite.",
    },
    {
        "id": "fausse-annonce-ia",
        "title": "Fausse publicité IA : générateur miracle",
        "image": "/static/img/exercice-fausse-annonce.svg",
        "prompt_hint": "Annonce fictive créée pour entraîner la vigilance.",
        "correct_signs": ["promesse-impossible", "url-bizarre", "badge-faux"],
        "signs": [
            {"key": "promesse-impossible", "label": "Promesse impossible ou trop belle"},
            {"key": "url-bizarre", "label": "URL étrange"},
            {"key": "badge-faux", "label": "Badge officiel non vérifiable"},
            {"key": "couleur-rouge", "label": "Couleur rouge"},
        ],
        "explanation": "Une promesse irréaliste, un faux badge et une URL douteuse indiquent souvent une arnaque ou une collecte de données.",
    },
]

PROMPT_EXAMPLES = [
    {
        "level": "Faible",
        "prompt": "Explique l'IA",
        "explanation": "Le sujet est trop large et aucun public ni format n'est indiqué.",
    },
    {
        "level": "Moyen",
        "prompt": "Explique l'IA à un collégien avec quelques exemples.",
        "explanation": "Le public et les exemples sont précisés, mais le format et les critères de vérification manquent.",
    },
    {
        "level": "Excellent",
        "prompt": "Explique l'intelligence artificielle à un élève de 3e en 5 points simples. Ajoute deux exemples du quotidien, une limite importante et trois informations à vérifier dans des sources fiables.",
        "explanation": "Objectif, public, structure, exemples et vérification sont clairement définis.",
    },
]


def public_video_payload(video: dict) -> dict:
    payload = dict(video)
    quiz = VIDEO_QUIZZES.get(video["id"], [])
    payload["quiz"] = [
        {"question": item["question"], "choices": item["choices"]}
        for item in quiz
    ]
    return payload
