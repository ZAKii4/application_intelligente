# ADR 003 : clé API dans un en-tête et liste d'origines CORS dans .env

Date : 04/11/2026 · Auteurs : [noms]

## Contexte
L'API MaintAI ne doit répondre qu'aux programmes autorisés, et une page web servie sur http://localhost:5500 doit pouvoir l'appeler, mais pas une page servie ailleurs. Il faut donc décider où le client transmet sa clé, et quelles origines le navigateur a le droit d'utiliser pour appeler l'API, sans jamais mettre de secret dans le code ni dans Git.

## Options étudiées

### Décision 1 : où transmettre la clé ?
1. Dans l'URL (`/v1/predict?api_key=...`) : très simple à tester dans un navigateur ; mais l'URL est enregistrée partout (journaux du serveur et des proxys, historique du navigateur, en-tête Referer), la clé fuiterait.
2. Dans le corps JSON : n'apparaît pas dans l'URL ; mais mélange authentification et données métier, oblige à modifier le schéma `SensorReading` (incompatible avec `extra="forbid"`), et ne fonctionne pas pour les requêtes GET qui n'ont pas de corps.
3. Dans un en-tête `X-API-Key` : séparé des données, non journalisé par défaut, valable pour toutes les méthodes HTTP, lu facilement par FastAPI avec `Header()` et documenté dans `/docs` ; inconvénient : on ne peut pas tester en tapant simplement l'URL dans le navigateur, il faut `/docs`, `curl` ou du code.

### Décision 2 : quelles origines autoriser (CORS) ?
1. `allow_origins=["*"]` : tout site peut appeler l'API depuis un navigateur, aucune configuration ; mais n'importe quelle page malveillante pourrait utiliser le navigateur d'un utilisateur pour appeler l'API.
2. Une liste écrite en dur dans `main.py` : explicite ; mais il faut modifier le code et redéployer pour chaque nouvel environnement (local, test, production).
3. Une liste explicite lue dans `.env` (`MAINTAI_CORS_ORIGINS`) : seules les origines prévues sont acceptées, et la liste change selon l'environnement sans toucher au code ; inconvénient : il faut relancer uvicorn après chaque modification.

## Décision
- La clé est transmise dans l'en-tête **`X-API-Key`**. C'est la seule option qui garde la clé hors des journaux et de l'historique, sans toucher au contrat d'entrée du modèle. Elle est comparée avec `secrets.compare_digest` (temps constant) dans `require_api_key()`, ajoutée comme dépendance de tout le router `/v1` ; `/health` reste public.
- La clé attendue et les origines autorisées sont lues dans **`.env`** (`MAINTAI_API_KEY`, `MAINTAI_CORS_ORIGINS`), chargé avec `--env-file .env`. `.env` est dans `.gitignore` ; seul `.env.example`, avec de fausses valeurs, est commité.
- Origines autorisées : **une liste explicite**, `http://localhost:5500` et `http://127.0.0.1:5500`, et non `*`, car seule la page du projet doit pouvoir appeler l'API depuis un navigateur.

## Conséquences
- Facilite : la clé n'apparaît ni dans le code, ni dans Git, ni dans les URL ; chaque membre et chaque environnement a sa propre clé et sa propre liste d'origines ; l'ordre des contrôles est clair (404 → 401 → 422 → 503).
- Rend plus difficile : chaque client (page web, curl, Java, tests) doit ajouter l'en-tête ; toute nouvelle origine (autre port, déploiement) doit être ajoutée dans `.env`, puis uvicorn relancé ; sans `.env`, l'API répond 500 à toutes les requêtes `/v1`.
- À surveiller : vérifier avec `git status` avant chaque commit que `.env` n'apparaît pas ; si une clé est commitée par erreur, la changer (elle reste dans l'historique). CORS ne protège que contre les navigateurs : curl et les programmes passent, la clé reste donc indispensable. Une clé unique partagée ne distingue pas les clients ; plus tard, il faudra des clés par client et une gestion des droits (403).
