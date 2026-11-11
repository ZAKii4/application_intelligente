# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** 9 · **Membres :** Zaoufy Malak et Khamlich Zakaria · **Date :** 04/11/2026

> Ce compte rendu est complété à partir des fichiers présents dans les projets TP1 et TP2, des vérifications effectuées dans le terminal pendant le travail et du tableau fourni par le groupe. Les résultats d'étapes intermédiaires qui n'étaient pas conservés sont indiqués comme tels plutôt que reconstitués.

## 1. Activité 1 : casser son API (dans `TP/TP1`)

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---:|---:|
| 1 | Champ manquant : `load_pct` absent | 422 | 422 |
| 2 | Valeur absurde : `temperature_c = 500` | 422 | 422 |
| 3 | Texte au lieu d'un nombre : `load_pct = "bonjour"` | 422 | 422 |
| 4 | Champ en trop : `couleur = "rouge"` | 422 | 422 |
| 5 | Mauvaise route : `/v1/predicte` au lieu de `/v1/predict` | 404 | 404 |

Les cinq codes obtenus correspondent aux prévisions données. Le tableau est celui fourni pour le compte rendu; les requêtes de validation ont aussi été rejouées sur l'API TP2 avec la bonne clé, où les quatre premières renvoient 422 et la route incorrecte renvoie 404.

La sortie historique de `python -m pytest` avec `tests/test_casser.py` dans le TP1 n'est pas conservée. Le fichier `test_casser.py` n'est pas présent dans les fichiers TP1/TP2 actuellement disponibles, donc sa dernière ligne de sortie ne peut pas être rapportée de façon fiable.

`@pytest.mark.parametrize` permet d'exécuter la même fonction de test avec plusieurs jeux de paramètres. Un jeu de paramètres correspond à une exécution de test distincte; avec les cinq cas du tableau, cela représente cinq cas paramétrés. Le nombre total de tests pytest de la suite historique ne peut pas être confirmé sans le fichier et sa sortie.

## 2. ruff

Sortie historique de `ruff check .` dans `TP/TP1` : non disponible dans les éléments consultés.

`ruff check .` analyse statiquement les fichiers Python du dossier courant pour signaler des problèmes de style, des erreurs détectables et certaines erreurs probables. `python -m pytest` exécute les tests pour vérifier le comportement du code. Un contrôle Ruff réussi ne prouve donc pas que les tests fonctionnent, et des tests réussis ne garantissent pas l'absence de problèmes de style.

## 3. Mise en place du TP2 (dans `TP/TP2`)

La sortie de `python -m pytest` juste après la mise en place initiale n'est pas conservée. Dans l'état TP2 actuellement présent, la suite complète a été exécutée le 04/11/2026 :

```text
18 passed, 1 warning in 13.32s
```

Le seul avertissement est une dépréciation de `starlette.testclient` indiquant que l'utilisation actuelle avec `httpx` sera à remplacer par `httpx2`; il n'empêche pas les tests de réussir.

La question demandant quels étaient les deux tests en échec au démarrage et le code reçu à la place de 401 concerne un état intermédiaire qui n'est plus disponible. On ne peut pas identifier précisément ces deux tests à partir du dépôt actuel. Le comportement actuel est différent : les tests d'authentification réussissent et les routes `/v1` utilisent bien `require_api_key`.

## 4. La clé API (sprint 1)

Corps actuel de `require_api_key()` dans `maintai/api/security.py` :

```python
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

L'authentification est rattachée au router `/v1` avec :

```python
router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(require_api_key)]
)
```

Écrire `security.py` seul ne protège pas automatiquement les routes : FastAPI doit aussi appeler cette dépendance, ici en l'ajoutant au router. Le nombre de tests échouant à l'étape intermédiaire où seul `security.py` avait été écrit n'est pas documenté; l'état du code ne permet pas de reconstituer cette exécution passée.

Dernière ligne de `python -m pytest` à la fin du sprint 1 : sortie historique non disponible. La suite actuelle complète réussit (18 tests).

Les réponses ci-dessous ont été consignées dans le compte rendu TP1 déjà complété, lors d'une vérification du 28/10/2026. La prédiction dépend du modèle chargé à cette date.

| Requête | Code obtenu | Réponse (corps JSON) |
|---|---:|---|
| `GET /health`, sans clé | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | Une prédiction JSON avec `failure_probability`, `alert`, `threshold` et `model_version`. La réponse enregistrée pour le relevé fourni était `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-28T17:58:58Z"}`. |
| `POST /v1/predict`, 500 °C, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | Erreur de validation Pydantic : `temperature_c` doit être inférieur ou égal à 150. |

À 500 °C, la requête sans clé est refusée par la dépendance d'authentification avant d'atteindre la validation de la route : elle donne 401. Avec la bonne clé, la validation du schéma s'applique et refuse la température hors limites avec 422.

Si Uvicorn est lancé sans `--env-file .env`, le résultat dépend de la présence éventuelle de `MAINTAI_API_KEY` dans l'environnement du terminal. Si aucune clé serveur n'est configurée, la fonction répond 500 (`La clé API du serveur n'est pas configurée`) au lieu de 401 : le problème est la configuration serveur, et non une clé client incorrecte. La commande exécutée sans cette option et son résultat ne sont pas conservés.

## 5. La page web (sprint 2)

Le code `fetch` présent dans `web/index.html` :

```javascript
const FEATURES = ["temperature_c", "vibration_mm_s", "load_pct", "runtime_hours"];
const show = (cls, text) => {
  const r = document.getElementById("result");
  r.className = cls;
  r.textContent = text;
};

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

Le comportement déterminé par le code et l'API est :

| Essai | Ce qu'affiche la page |
|---|---|
| Relevé normal, bonne clé | Message « ALERTE » ou « Pas d'alerte » avec la probabilité et le seuil; le résultat dépend de la prédiction du modèle. |
| 500 °C, bonne clé | `Erreur 422` avec le message de validation indiquant que la température maximale est 150. |
| Relevé normal, fausse clé | `Erreur 401 : Clé API absente ou invalide`. |

**Expérience CORS.** La configuration actuelle n'autorise que `http://localhost:5500` et `http://127.0.0.1:5500`. Le contrôle CORS avec le client de test a confirmé que `http://localhost:5500` est autorisé et que `http://localhost:5501` ne reçoit pas d'en-tête `access-control-allow-origin`. Le navigateur devrait donc bloquer la requête lorsque la page vient du port 5501; le JavaScript affiche alors `API injoignable : uvicorn est arrêté, ou cette origine est refusée (CORS)`. La console du navigateur n'a pas été consultée, le message exact de sa console n'est donc pas rapporté.

Lors de l'essai du serveur local, le port 5500 était déjà écouté par le processus Windows `tnslsnr` (PID 4824), et Python a reçu `PermissionError: [WinError 10013]`. Le test de disponibilité a confirmé que le port 5501 pouvait être ouvert. Le serveur HTTP sur 5501 n'a toutefois pas été confirmé comme lancé dans le terminal.

`curl.exe` n'est pas soumis à la politique CORS du navigateur : CORS est une restriction appliquée par les navigateurs aux scripts web. Une réponse de `curl.exe` ne prouve donc pas qu'un `fetch` depuis une origine non autorisée sera accepté.

## 6. Les tests de l'activité 1 dans le TP2

Le fichier `test_casser.py` copié dans TP2 n'est pas présent dans l'arborescence actuelle. Les cinq requêtes ont cependant été vérifiées avec le client de test de FastAPI, en envoyant les mêmes requêtes sans clé :

| Cas sans `headers=HEADERS` | Code obtenu |
|---|---:|
| Champ manquant | 401 |
| Valeur hors limites | 401 |
| Texte à la place d'un nombre | 401 |
| Champ supplémentaire | 401 |
| Route `/v1/predicte` inexistante | 404 |

Ainsi, les quatre tests qui appellent la route `/v1/predict` sans clé échouent s'ils attendent les codes 422 : l'authentification les arrête d'abord avec 401. Le cas de la mauvaise route passe encore avec 404, car cette route n'existe pas et n'atteint pas le router `/v1`.

Avec la clé de test configurée (`test-key`), les cinq codes observés sont `422, 422, 422, 422, 404`, conformément au tableau de l'activité 1.

Dernière ligne de `python -m pytest` dans TP2, vérifiée le 04/11/2026 :

```text
18 passed, 1 warning in 13.32s
```

## 7. Questions de compréhension

1. **Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?**  
   401 signifie que l'authentification est absente ou invalide. 422 signifie que la requête a été comprise, mais que ses données ne respectent pas le schéma (champ manquant, type incorrect ou valeur hors limites). 403 signifie que le client est identifié mais n'a pas l'autorisation d'effectuer l'action.

2. **Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?**  
   Une clé dans le code ou le dépôt serait visible par toute personne ayant accès à ces fichiers et à leur historique Git. `.env` contient la configuration locale et la vraie clé; il est ignoré par Git dans le `.gitignore` actuel. `.env.example` fournit un exemple sans secret réel (`MAINTAI_API_KEY=changez-moi`) et les origines CORS par défaut; c'est ce fichier d'exemple qui est destiné à être versionné. Il faut remplacer la valeur d'exemple avant utilisation.

3. **Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?**  
   Les URL peuvent être enregistrées dans l'historique du navigateur, les journaux de serveurs, les outils d'analyse et les traces réseau. L'en-tête `X-API-Key` évite d'exposer la clé dans ces URL et permet au serveur de l'extraire explicitement. En production, HTTPS reste nécessaire pour protéger les échanges.

4. **Que fait `secrets.compare_digest` de plus qu'un simple `==` ?**  
   Il effectue une comparaison conçue pour réduire les différences de temps d'exécution qui pourraient révéler progressivement des informations sur les caractères comparés. Il ne chiffre pas la clé et ne remplace pas HTTPS.

5. **Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?**  
   Une origine comprend le schéma, l'hôte et le port. Ces deux adresses ont le même schéma et le même hôte, mais des ports différents; elles sont donc d'origines différentes et la politique CORS s'applique.

## 8. Le rendu Git

- **Lien de la pull request :** non disponible dans les informations consultées.
- **Le tag `tp2` existe sur GitHub :** non vérifiable localement.
- **`git status` avant le commit : le fichier `.env` apparaissait-il ?** `.env` est bien couvert par le `.gitignore` du projet; la sortie historique de `git status` avant commit n'est pas disponible pour confirmer ce qu'elle affichait à ce moment.
- **Qui a relu la pull request, et quel commentaire a-t-il laissé ?** non disponible; à compléter après consultation de la pull request.

## 9. Ce qui reste flou

Les sorties historiques des premières exécutions pytest, de `ruff check .`, des étapes intermédiaires du sprint 1 et du test `test_casser.py` ne sont pas conservées dans les fichiers consultés. Le lien et le commentaire de la pull request, l'existence du tag distant `tp2` et le résultat d'une ouverture réelle de la page dans le navigateur restent également à confirmer. Les observations présentes distinguent ces inconnues des vérifications reproduites le 04/11/2026.
