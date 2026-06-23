# Audit technique MEPA - version corrigée

## Problèmes constatés dans la version reçue

1. **Le testeur de prompts ne répondait pas réellement au prompt en mode local.** La réponse de secours était identique quel que soit le texte saisi.
2. **Deux appels Gemini étaient effectués pour un seul essai**, ce qui doublait la consommation de requêtes et de jetons.
3. **Aucune limite serveur n'était appliquée au laboratoire de prompts.** Une simple limitation dans le navigateur aurait été contournable.
4. **Les réponses correctes du quiz étaient envoyées au navigateur** dans `/api/content`, ce qui permettait de les lire sans répondre.
5. **Les vidéos pouvaient être validées directement** sans ouverture préalable.
6. **Les six anciennes vidéos et le quiz général ne correspondaient plus au contenu demandé.**
7. **Protection CSRF absente** sur les routes modifiant les données.
8. **Limitation des tentatives de connexion absente.**
9. **Clé secrète de développement utilisée par défaut** et mode debug activé dans `python app.py`.
10. **Validation des entrées fragile**, notamment la conversion directe de l'âge pouvant provoquer une erreur serveur.
11. **Les prompts étaient stockés en clair dans l'historique d'activité**, ce qui est contraire au principe de minimisation.
12. **Suppression de compte incomplète** : l'ancien compte restait en base avec son adresse e-mail.
13. **Certificat téléchargé en HTML et non en PDF.**
14. **Architecture monolithique** : contenu, sécurité, base, routes et service IA étaient mélangés dans un seul fichier.
15. **En-têtes HTTP de sécurité insuffisants** et absence de politique CSP.

## Corrections appliquées

- Architecture en modules : `config`, `db`, `security`, `content`, `ai_service`, `pdf_service`, `routes`.
- Gemini `gemini-2.5-flash-lite` avec **une seule requête structurée par essai**.
- Limite de **3 essais par compte**, imposée et comptée côté serveur.
- Réponse initiale, diagnostic, prompt amélioré, réponse améliorée et conseils retournés dans un JSON structuré.
- Aucun prompt conservé en clair ; seule une empreinte SHA-256 et le statut de la tentative sont stockés.
- Trois cartes vidéo : deux disponibles et une indiquée « Arrive bientôt ».
- QCM de 8 questions pour chacune des deux vidéos disponibles, corrigés uniquement côté serveur.
- Ouverture enregistrée en base avant toute validation de vidéo ou de QCM.
- Vidéo HeyGen intégrée dans un lecteur responsive.
- Vidéo locale servie par une route authentifiée avec prise en charge des requêtes partielles du navigateur.
- CSRF sur toutes les requêtes d'écriture, sessions durcies, cookies `HttpOnly` et `SameSite=Lax`.
- Limitation des inscriptions et connexions par clé hachée.
- Hachage des mots de passe avec scrypt.
- CSP, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy` et anti-framing.
- Export RGPD, suppression réelle en cascade et certificat PDF enregistré en base.
- Conservation de la meilleure note obtenue pour chaque activité.
- Tests automatisés des flux critiques.
