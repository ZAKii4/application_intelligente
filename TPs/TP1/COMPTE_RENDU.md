# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** à compléter  ·  **Membres :** zakaria khamlich - malak zaoufy ·  **Date :** 28 octobre 2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
3 failed, 10 passed, 1 warning
```

Dans `tests/test_api.py`, les quatre tests qui passent sont `test_health`, `test_out_of_range_value_is_rejected`, `test_missing_field_is_rejected` et `test_openapi_documents_predict`. Les deux tests qui attendent 422 passent pour une mauvaise raison : comme le schéma ne déclare encore aucun champ, `extra="forbid"` rejette tous les champs envoyés comme inconnus. La température hors limites n'est donc pas réellement contrôlée, et le test du champ manquant ne vérifie pas encore un schéma complet.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | `float` | -50 °C | 200 °C | Plage large couvrant les températures ambiantes et des conditions extrêmes d'une machine. |
| `vibration_mm_s` | `float` | 0 mm/s | 50 mm/s | Une amplitude de vibration ne peut pas être négative ; 50 mm/s constitue une limite haute de sécurité. |
| `load_pct` | `float` | 0 % | 100 % | Pourcentage de charge physique, de l'arrêt à la capacité nominale. |
| `runtime_hours` | `float` | 0 h | 100 000 h | Une durée cumulée ne peut pas être négative ; 100 000 h couvre une longue durée de vie industrielle. |

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

`python -m pytest` donne alors 3 échecs et 10 réussites : les trois tests qui exercent la route de prédiction échouent sur `NotImplementedError`, car `predict()` n'est pas encore implémentée.

C'est un bon signe : les entrées sont désormais validées et les valeurs invalides sont rejetées ; les erreurs restantes concernent l'étape suivante, la logique de prédiction.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
predictor = state.get("predictor")
if predictor is None:
    raise HTTPException(status_code=503, detail="Le modèle de prédiction n'est pas disponible.")
return PredictionOut(**predictor.predict(reading.model_dump()))
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

503 signifie que le service est temporairement indisponible parce que sa dépendance (le modèle) manque. 500 désigne plutôt une erreur interne inattendue du serveur.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Le chargement du fichier modèle est coûteux. Le faire au démarrage évite cette opération à chaque requête, réduit la latence et réutilise la même instance du modèle tant que l'API tourne.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
13 passed, 1 warning
```

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-29T00:14:50Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 200","input":500,"ctx":{"le":200.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail":"Not Found"}` |

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Dans le schéma `SensorReading` associé à `POST /v1/predict`, sous les paramètres du corps de requête ; les bornes apparaissent comme valeurs `minimum` et `maximum` pour chaque champ.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est un style architectural pour concevoir des API HTTP. FastAPI est un framework Python qui permet de construire une API, notamment en suivant les conventions REST.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   Il valide les données reçues, produit une documentation OpenAPI (visible dans `/docs`) et structure/sérialise les données d'entrée et de sortie.
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost` désigne la machine locale, `8000` le port du serveur, et `/v1/predict` le chemin de la route de prédiction versionnée.
4. Pourquoi `/v1` dans l'adresse ?
   Pour identifier la version de l'API et pouvoir faire évoluer son contrat plus tard sans casser les clients qui utilisent la version précédente.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` est le chemin Python du module qui contient l'API ; `app` est l'objet FastAPI exposé par ce module.

## 7. Le rendu Git

- Lien de la pull request : https://github.com/ZAKii4/application_intelligente/pull/1
- Le tag `tp1` existe sur GitHub : non (vérifié le 29 octobre 2026)
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  Aucune relecture pour le moment.

## 8. Ce qui reste flou

À vérifier avec les données réelles : les bornes physiques choisies et le seuil d'alerte (0,3) doivent être confirmés par le métier. Le jeu de données utilisé ici est synthétique ; les résultats de prédiction ne remplacent pas une validation sur des relevés industriels.
