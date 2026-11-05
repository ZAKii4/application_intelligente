# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** …  ·  **Membres :** …  ·  **Date :** 04/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP2.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---|---|
| 1 | champ manquant : `{"temperature_c": 60, "vibration_mm_s": 2, "runtime_hours": 5000}` (sans `load_pct`) | 422 | 422 |
| 2 | valeur absurde : `load_pct: 250` | 422 | 422 |
| 3 | texte au lieu d'un nombre : `temperature_c: "chaud"` | 422 | 422 |
| 4 | champ en trop : `"humidite": 40` en plus des 4 champs | 422 | 422 |
| 5 | mauvaise route : `POST /v1/predicte` | 404 | 404 |

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

Non, les cinq codes obtenus correspondent aux prévisions. Point d'attention pour le cas 3 : si l'on envoie le texte `"60"` au lieu de `"chaud"`, Pydantic le convertit automatiquement en nombre (mode « lax ») et la requête est acceptée (200). Il faut donc un texte qui ne représente pas un nombre pour obtenir 422. Pour la mauvaise route, le 404 est renvoyé par FastAPI avant toute validation : le corps n'est même pas lu.

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```
========================== 18 passed, 1 warning in 0.79s ==========================
```

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

`parametrize` permet d'exécuter **une seule fonction de test** avec plusieurs jeux de paramètres : pytest la lance une fois par ligne de la liste `CAS_REFUSES`. Il compte donc **5 tests** pour `test_requete_refusee` (13 + 5 = 18), chacun nommé dans le rapport (`test_requete_refusee[champ manquant-...]`, etc.). On évite de copier-coller cinq fonctions presque identiques, et si un cas échoue, on sait immédiatement lequel.

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :

```
I001 [*] Import block is un-sorted or un-formatted
 --> demo_api.py:1:1
UP017 [*] Use `datetime.UTC` alias
  --> maintai/train.py:58:36
Found 2 errors.
[*] 2 fixable with `--fix`.
```

Après `ruff check . --fix` (« Found 4 errors (4 fixed, 0 remaining) ») et `ruff format .` (« 12 files reformatted, 6 files left unchanged ») :

```
All checks passed!
```

Puis `python -m pytest` : `18 passed`, rien n'est cassé.

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

- `ruff check .` est une **analyse statique** : il lit le code **sans l'exécuter** et signale ce qui est mal écrit (imports inutiles ou mal triés, variables non utilisées, syntaxe obsolète…). Il vérifie la **forme** et la qualité du code.
- `python -m pytest` **exécute** le code et vérifie qu'il fait ce qu'on attend (le bon code HTTP, la bonne prédiction…). Il vérifie le **comportement**.

Un code peut passer ruff et être faux, ou passer les tests et être mal écrit : les deux sont complémentaires.

## 3. Mise en place du TP2 (dans `TP/TP2`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
===================== 2 failed, 16 passed, 1 warning in 0.78s =====================
```

Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

`tests/test_security.py::test_missing_key_is_rejected` (requête sans clé) et `tests/test_security.py::test_wrong_key_is_rejected` (requête avec la clé `wrong`). Tous deux reçoivent **200** au lieu de 401 : la clé n'est pas encore vérifiée, l'API répond à tout le monde.

## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    expected = get_settings().api_key
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La clé API du serveur n'est pas configurée",
        )
    if x_api_key is None or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente ou invalide",
        )
```

Votre ligne `router = ...` dans `maintai/api/main.py` :

```python
router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
```

Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

Toujours **2 tests** échouent (`2 failed, 16 passed`), avec 200 au lieu de 401. La fonction `require_api_key` existe, mais **rien ne l'appelle** : tant qu'elle n'est pas déclarée comme dépendance du router, FastAPI ne l'exécute jamais avant `predict()`.

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
========================== 18 passed, 1 warning in 0.81s ==========================
```

Lancez `uvicorn maintai.api.main:app --reload --env-file .env`, puis envoyez ces requêtes (avec `/docs` ou `curl`) :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health`, sans clé | 200 | `{"status": "ok", "model_loaded": true}` |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail": "Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | `{"detail": "Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | `{"failure_probability": …, "alert": false, "threshold": 0.3, "model_version": "…"}` |
| `POST /v1/predict`, 500 °C, sans clé | 401 | `{"detail": "Clé API absente ou invalide"}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | `{"detail": [{"type": "less_than_equal", "loc": ["body", "temperature_c"], "msg": "Input should be less than or equal to 150", "input": 500, "ctx": {"le": 150.0}}]}` |

500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

Parce que les contrôles s'enchaînent dans un ordre fixe, et le premier qui échoue donne la réponse : **route (404) → clé (401) → données (422) → modèle (503)**. Sans clé, la requête est arrêtée à l'étape 2 : l'API ne regarde même pas les données, d'où 401. Avec la bonne clé, la requête passe le contrôle de la clé et arrive à la validation Pydantic, qui refuse 500 °C (> 150), d'où 422.

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

On obtient **500** avec `{"detail": "La clé API du serveur n'est pas configurée"}`. Sans `--env-file .env`, la variable `MAINTAI_API_KEY` n'est pas chargée : `get_settings().api_key` vaut `None`. Ce n'est pas le client qui est en faute (401), c'est le **serveur** qui est mal configuré, d'où une erreur 500. On refuse aussi toute requête plutôt que de laisser l'API ouverte sans protection.

## 5. La page web (sprint 2)

Votre code `fetch` (le contenu du `addEventListener` dans `web/index.html`) :

```javascript
document.getElementById("go").addEventListener("click", async () => {
  const reading = Object.fromEntries(FEATURES.map(f => [f, Number(document.getElementById(f).value)]));
  const url = document.getElementById("url").value.replace(/\/+$/, "");
  const cle = document.getElementById("key").value;
  try {
    const resp = await fetch(`${url}/v1/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": cle },
      body: JSON.stringify(reading),
    });
    const data = await resp.json();
    if (!resp.ok) {
      const detail = typeof data.detail === "string" ? data.detail : data.detail?.[0]?.msg ?? "";
      show("err", `Erreur ${resp.status} : ${detail}`);
      return;
    }
    const pct = (data.failure_probability * 100).toFixed(1);
    if (data.alert) {
      show("alert", `ALERTE : probabilité de panne ${pct} % (seuil ${data.threshold})`);
    } else {
      show("ok", `Pas d'alerte : probabilité de panne ${pct} % (seuil ${data.threshold})`);
    }
  } catch (e) {
    show("err", "API injoignable : uvicorn est arrêté, ou cette origine est refusée (CORS)");
  }
});
```

Ce qu'affiche la page (servie sur le port 5500) :

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | `ALERTE : probabilité de panne … % (seuil 0.3)` (fond rouge) avec les valeurs par défaut 72 °C, 6 mm/s, 85 %, 15 000 h |
| 500 °C, bonne clé | `Erreur 422 : Input should be less than or equal to 150` (fond orange) |
| relevé normal, fausse clé | `Erreur 401 : Clé API absente ou invalide` (fond orange) |

**Expérience CORS.** Servez la page sur le port 5501. Que dit la page, et que dit la console (F12) ?

La page affiche `API injoignable : uvicorn est arrêté, ou cette origine est refusée (CORS)` : le `fetch` lève une exception et on passe dans le `catch`. La console du navigateur indique que la requête vers `http://localhost:8000/v1/predict` depuis l'origine `http://localhost:5501` a été **bloquée par la politique CORS**, car la réponse ne contient pas d'en-tête `Access-Control-Allow-Origin`. L'origine 5501 n'est pas dans `MAINTAI_CORS_ORIGINS` (qui ne contient que `http://localhost:5500` et `http://127.0.0.1:5500`).

Pourquoi `curl` obtient-il une réponse alors que la page du port 5501 est bloquée ?

CORS est une règle appliquée **par le navigateur**, pas par l'API. Avant d'envoyer le POST, le navigateur fait une requête `OPTIONS` (« puis-je ? ») ; l'API ne renvoie pas d'autorisation pour 5501, donc le navigateur bloque. `curl` n'est pas un navigateur : il n'a pas de notion d'origine et ne fait pas cette vérification, il envoie directement la requête. Pour `curl`, seule la clé API compte. CORS protège l'utilisateur contre une page malveillante qui utiliserait son navigateur ; ce n'est pas une protection de l'API, d'où la nécessité de la clé.

## 6. Les tests de l'activité 1 dans le TP2

Copiez `test_casser.py` dans `TP/TP2/tests`. Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

Sans `headers=HEADERS`, **4 tests** échouent : les quatre cas qui attendent 422 reçoivent **401**, car la clé est vérifiée avant les données. Le cas **« mauvaise route »** passe quand même : la route `/v1/predicte` n'existe pas, FastAPI répond 404 dès l'étape 1, avant même la vérification de la clé (la dépendance `require_api_key` n'est attachée qu'aux routes existantes du router).

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

```
========================== 23 passed, 1 warning in 0.76s ==========================
```

## 7. Questions de compréhension

1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?
   **401 Unauthorized** : on ne sait pas qui appelle (clé absente ou invalide), c'est un problème d'**authentification**. **422 Unprocessable Content** : le client est identifié, mais les **données** envoyées ne respectent pas le schéma (champ manquant, valeur hors bornes…). **403 Forbidden** : le client est bien identifié, mais **n'a pas le droit** d'accéder à cette ressource ; c'est un problème d'**autorisation**.

2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?
   Tout ce qui est commité finit sur GitHub et reste dans l'**historique** de Git pour toujours, même si on supprime le fichier ensuite : une clé commitée une fois est compromise et doit être changée. `.env` contient les **vraies valeurs** (la clé, les origines CORS) ; il est dans `.gitignore` et n'est **jamais commité**. `.env.example` contient les **noms des variables avec de fausses valeurs** (`changez-moi`) : il est **commité** et indique à chacun quoi configurer.

3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?
   Une URL est enregistrée partout : journaux du serveur et des proxys, historique et favoris du navigateur, en-tête `Referer` envoyé à d'autres sites. Une clé dans l'URL fuiterait facilement. Les en-têtes ne sont pas journalisés par défaut ni affichés dans la barre d'adresse.

4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?
   `==` compare les chaînes caractère par caractère et **s'arrête au premier caractère différent** : la durée de la réponse révèle combien de caractères étaient justes, ce qui permet de deviner la clé caractère par caractère (**attaque temporelle**). `secrets.compare_digest` compare toujours en **temps constant**, quelle que soit la position de la différence.

5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?
   Une origine est le triplet **schéma + domaine + port** (par exemple `http` + `localhost` + `5500`). `http://localhost:5500` et `http://localhost:8000` sont **deux origines différentes**, car le port diffère. C'est pourquoi la page servie sur 5500 doit être explicitement autorisée par l'API (CORS) pour l'appeler sur 8000.

## 8. Le rendu Git

- Lien de la pull request : …
- Le tag `tp2` existe sur GitHub : oui / non
- `git status` avant le commit : le fichier `.env` apparaissait-il ? non (il est listé dans `.gitignore`)
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  …

## 9. Ce qui reste flou

…
