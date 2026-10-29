# Compte rendu · TP1 : une API de prédiction pour MaintAI

> Version complétée à partir du code présent et des vérifications effectuées dans le terminal.  
> Le fichier `COMPTE_RENDU.md` d'origine est conservé sans modification. Les informations de groupe et celles du dépôt distant ne sont pas disponibles ici.

**Groupe :** à compléter · **Membres :** à compléter · **Date :** 28/10/2026

## 1. Mise en place

La sortie du lancement initial de `python -m pytest`, avant l'implémentation, n'est pas conservée dans le terminal consultable. Je ne peux donc pas identifier avec certitude les quatre tests qui passaient à cette étape ni reproduire cette sortie sans revenir à l'état initial du projet.

Les deux tests qui attendent une réponse 422 vérifient respectivement une valeur hors limites et un champ manquant. `extra="forbid"` rejette les clés inconnues, mais ne définit pas à lui seul les champs autorisés, leurs types, les champs obligatoires ou leurs bornes. Si les champs attendus n'étaient pas encore déclarés dans le schéma, les clés envoyées par les tests pouvaient être rejetées comme « extras » : le code 422 était alors obtenu pour la mauvaise raison, et non grâce à une validation correcte de la valeur ou du champ manquant.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique |
|---|---:|---:|---:|---|
| `temperature_c` | `float` | -40 °C | 150 °C | Plage étendue couvrant des environnements froids et la chaleur d'une machine industrielle. |
| `vibration_mm_s` | `float` | 0 mm/s | 100 mm/s | Une vitesse vibratoire ne peut pas être négative; 100 mm/s laisse une marge pour signaler des vibrations extrêmes. |
| `load_pct` | `float` | 0 % | 100 % | La charge est une proportion de la capacité nominale, de zéro à la capacité maximale. |
| `runtime_hours` | `float` | 0 h | 100 000 h | Le compteur d'heures ne peut pas être négatif; 100 000 h représente environ 11,4 années de fonctionnement continu. |

Ces limites décrivent des plages de validation plausibles pour les capteurs et la machine; elles ne sont pas déduites des valeurs minimales et maximales d'un échantillon de données.

La sortie historique de `python -m pytest` après la modification de `schemas.py` seul n'est pas disponible. Dans l'état actuel du projet, qui comprend également l'API et les autres éléments du TP, l'exécution vérifiée est :

```text
.............                                                            [100%]
13 passed in 5.38s
```

Il n'est donc pas possible d'attribuer honnêtement un message d'erreur à l'étape intermédiaire « schéma seul » à partir des informations présentes.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Corps actuel de la fonction :

```python
predictor = state.get("predictor")
if predictor is None:
    raise HTTPException(status_code=503, detail="Modèle non disponible")
return predictor.predict(reading.model_dump())
```

Le code 503 indique que le service est temporairement incapable de répondre parce que son modèle n'est pas disponible. Un code 500 signalerait plutôt une erreur interne inattendue. L'API est conçue pour pouvoir démarrer sans modèle; `/health` expose alors son état et la route de prédiction répond 503.

Le modèle est chargé une fois au démarrage par le gestionnaire `lifespan`. Cela évite de relire le fichier et de reconstruire le prédicteur à chaque requête, réduit le coût et la latence des appels et conserve le même modèle durant la vie de l'application.

## 4. Les tests

Dernière ligne de `python -m pytest -q` à la fin de la vérification :

```text
13 passed in 5.38s
```

## 5. L'API en marche

Les réponses ci-dessous ont été vérifiées avec un modèle entraîné dans un dossier temporaire, sans générer ni remplacer les données ou les modèles du projet.

| Requête | Code obtenu | Réponse (corps JSON) |
|---|---:|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c":72.5,"vibration_mm_s":6.1,"load_pct":85,"runtime_hours":15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-28T17:58:58Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail":"Not Found"}` |

Les prédictions dépendent du modèle effectivement chargé; `model_version` correspond au modèle créé pendant cette vérification.

Dans `/docs`, les bornes apparaissent dans le schéma de la requête `POST /v1/predict`, dans les détails de chacun des champs. Elles sont aussi publiées dans le schéma OpenAPI.

## 6. Questions de compréhension

1. **REST et FastAPI : quelle est la différence ?**  
   REST est un style d'architecture pour concevoir des interfaces HTTP autour de ressources et de verbes tels que `GET` et `POST`. FastAPI est un framework Python qui permet notamment d'implémenter une API HTTP suivant ces principes; il n'est pas lui-même REST.

2. **Le schéma Pydantic sert à trois choses. Lesquelles ?**  
   Il décrit les données attendues, valide et convertit les entrées (types, champs obligatoires et contraintes), et fournit les modèles utilisés par FastAPI pour documenter l'API dans OpenAPI et `/docs`.

3. **Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?**  
   `localhost` désigne la machine locale, `8000` le port du serveur HTTP et `/v1/predict` le chemin de la route de prédiction versionnée.

4. **Pourquoi `/v1` dans l'adresse ?**  
   Il identifie la version de l'API. Une évolution incompatible peut être proposée sous une autre version, par exemple `/v2`, en limitant les ruptures pour les clients qui utilisent `/v1`.

5. **Dans `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?**  
   `maintai.api.main` est le chemin Python du module à importer; `app` est l'objet FastAPI exposé par ce module et servi par Uvicorn.

## 7. Le rendu Git

- **Lien de la pull request :** non disponible dans les informations consultées.
- **Le tag `tp1` existe sur GitHub :** non vérifiable depuis les informations disponibles.
- **Relecture de la pull request et commentaire :** non disponibles; à compléter après consultation de la pull request.

## 8. Ce qui reste flou

Les sorties historiques des étapes intermédiaires, l'identité des quatre tests passés au démarrage, les membres du groupe, le lien de la pull request, le tag distant et le commentaire de relecture ne figurent pas dans les informations disponibles. Ils restent à confirmer par le groupe plutôt que d'être devinés.
