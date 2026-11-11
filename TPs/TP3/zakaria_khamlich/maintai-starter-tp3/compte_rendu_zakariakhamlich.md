# Compte rendu · TP3 : interface Streamlit pour MaintAI

**Groupe :** …  ·  **Auteur :** Zakaria Khamlich  ·  **Date :** 11/11/2026
**Environnement :** macOS (Apple Silicon), Python 3.14, environnement virtuel du TP1 réutilisé, Streamlit 1.66.1

---

## 1. Objectif

Ajouter à MaintAI une interface utilisable par un technicien de maintenance, sans écrire de requête HTTP :

- un onglet **« Données »** pour explorer le jeu de données (indicateurs, taux de panne par tranche, nuage de points) ;
- un onglet **« Prédiction »** qui envoie un relevé à l'API du TP2 (protégée par clé) et affiche la probabilité de panne.

L'interface est un **troisième client** de l'API, après la page web (TP2) et le programme Java. Elle passe par une classe Python réutilisable, `MaintaiClient` (`maintai/client.py`).

## 2. Mise en place

Le starter a été copié dans `TPs/TP3/zakaria_khamlich/maintai-starter-tp3`, sur une branche `tp3` créée depuis `main` après la fusion du TP2.

```bash
source ~/Downloads/S4_maintai-starter-tp1/.venv/bin/activate
pip install -r requirements.txt          # ajoute streamlit 1.66.1 et ses dépendances (pyarrow, altair…)
python -m maintai.dataset                # 5000 relevés, taux de panne 13.6 %
python -m maintai.train                  # recall 0.75 au seuil 0.3 (baseline : 0.0)
cp <TP2>/.env .env                       # le .env n'est pas versionné
python -m pytest
```

Résultat après la mise en place :

```
=========== 5 failed, 18 passed, 1 warning in 4.74s ============
```

| Fichier de test | Échecs | Cause |
|---|---|---|
| `tests/test_client.py` | 3 | `NotImplementedError: TP3 sprint 2 : MaintaiClient.predict` |
| `tests/test_ui.py` | 2 | `IndexError: list index out of range` sur `at.metric[...]` : la page n'affiche aucun indicateur |

Les 18 tests des TP précédents (API, données, entraînement, sécurité) passent toujours : le starter n'a rien cassé.

Le warning `StarletteDeprecationWarning` (httpx et TestClient) vient de la bibliothèque et non de notre code ; il a été ignoré.

## 3. Lancement de la page : `streamlit run` contre `python -m streamlit run`

| Commande (depuis la racine du TP3) | Résultat |
|---|---|
| `streamlit run ui/app.py` | `ModuleNotFoundError: No module named 'maintai'` |
| `python -m streamlit run ui/app.py` | la page s'ouvre sur http://localhost:8501 |

Explication : `import maintai` est résolu à partir de `sys.path`. `streamlit run ui/app.py` y place le dossier du script (`ui/`), qui ne contient pas `maintai/`. `python -m` y ajoute le dossier courant, c'est-à-dire la racine du projet. Ce comportement dépend donc de la façon de lancer ; le TP4 le règle en installant le projet comme package (`pip install -e .`).

## 4. Sprint 2 en premier : le client Python

J'ai commencé par `MaintaiClient.predict`, parce que les trois tests du client sont indépendants de la page :

```python
def predict(self, reading: dict) -> dict:
    headers = {"X-API-Key": self.api_key} if self.api_key else {}
    r = self.http.post("/v1/predict", json=reading, headers=headers)
    if r.status_code != 200:
        raise APIError(r.status_code, r.json().get("detail"))
    return r.json()
```

C'est l'équivalent du `fetch` du TP2. Deux points méritent d'être notés :

- on appelle `self.http.post(...)` et non `httpx.post(...)`. En production, `self.http` est un `httpx.Client` pointant vers `http://localhost:8000` ; dans les tests, c'est le `TestClient` FastAPI, ce qui permet de tester le client contre l'application réelle **sans lancer uvicorn** ;
- l'en-tête n'est envoyé que si une clé est fournie : une clé vide donne donc un 401 côté API, pas une erreur côté client.

Résultat :

```
2 failed, 21 passed
```

Les 3 tests du client passent (cas 200, mauvaise clé → `APIError` 401, relevé à 500 °C → `APIError` 422). Il reste les 2 tests de l'interface.

## 5. Sprint 1 et fin du sprint 2 : la page

### 5.1 Onglet « Données »

```python
df = charger(get_settings().data_path)          # @st.cache_data : CSV lu une seule fois

c1, c2, c3 = st.columns(3)
c1.metric("Relevés", len(df))
c2.metric("Taux de panne", f"{df.failure.mean():.1%}")
c3.metric("Température moyenne", f"{df.temperature_c.mean():.1f} °C")

variable = st.selectbox("Variable", FEATURES)
tranches = pd.cut(df[variable], bins=10)
taux = df.groupby(tranches, observed=True).failure.mean()
taux.index = [round(i.mid, 1) for i in taux.index]
st.bar_chart(taux)

nuage = df.assign(panne=df.failure.map({0: "non", 1: "oui"}))
st.scatter_chart(nuage, x="temperature_c", y="vibration_mm_s", color="panne")
```

Choix faits :

- `failure` vaut 0 ou 1 : sa moyenne est directement le taux de panne ;
- les étiquettes des barres sont les **milieux** des tranches, gardés en nombres. J'ai gardé une décimale (`round(i.mid, 1)`), et non un arrondi à l'entier comme dans l'indication du sujet : pour `vibration_mm_s`, dont les valeurs sont petites, plusieurs tranches auraient eu la même étiquette ;
- le nuage est coloré par une colonne texte « oui / non », plus lisible dans la légende que 0 / 1 ;
- l'ordre des indicateurs n'est pas libre : `test_ui.py` lit `at.metric[0]` et attend le nombre de relevés.

Valeurs affichées avec les données complètes : 5000 relevés, taux de panne 13,6 %, température moyenne d'environ 60 °C.

**Lecture du graphique pour `vibration_mm_s`.** Le taux de panne augmente nettement avec la vibration : il est presque nul pour les vibrations faibles, puis monte très vite dans les tranches hautes. La hausse avec la température est plus progressive. **La vibration est la variable la plus déterminante.** C'est cohérent avec la génération des données (`dataset.py`), où le risque augmente de 0,6 par mm/s contre 0,08 par °C ; même rapporté à la dispersion de chaque variable (environ 2 mm/s contre 10 °C d'écart-type), l'effet de la vibration reste supérieur (≈ 1,2 contre ≈ 0,8 par écart-type).

### 5.2 Onglet « Prédiction »

```python
if envoye:
    try:
        res = MaintaiClient(url, api_key=cle).predict(releve)
    except APIError as e:
        detail = e.detail[0]["msg"] if isinstance(e.detail, list) else e.detail
        st.warning(f"Erreur {e.status_code} : {detail}")
    except httpx.HTTPError:
        st.error("API injoignable : uvicorn est-il lancé ? Vérifiez l'URL dans la barre latérale.")
    else:
        pct = round(res["failure_probability"] * 100)
        st.metric("Probabilité de panne", f"{pct} %")
        if res["alert"]:
            st.error(f"ALERTE : au-dessus du seuil {res['threshold']}")
        else:
            st.success(f"Pas d'alerte : sous le seuil {res['threshold']}")
```

Trois cas sont distingués :

1. l'API **refuse** la requête (401, 422, 503) : `APIError`, affichée en jaune ;
2. l'API **ne répond pas** : `httpx.HTTPError`, affichée en rouge ;
3. l'API **répond 200** : probabilité et alerte.

Pour une 422, FastAPI renvoie dans `detail` une liste d'erreurs et non une chaîne : j'affiche le message de la première.

Le formulaire (`st.form`) empêche les curseurs de relancer le script à chaque mouvement ; seul le bouton « Prédire » déclenche une relance, et `envoye` ne vaut `True` que pendant celle-ci. Le résultat disparaît donc dès qu'on touche un autre widget, ce qui est le comportement attendu.

Résultat final :

```
23 passed, 1 warning in 2.91s
```

Je n'ai pas relevé l'état intermédiaire « 4 failed, 19 passed » prévu par le sujet, puisque j'ai écrit le client avant l'onglet « Données ».

## 6. Essais avec l'API réelle

Terminal 1 : `uvicorn maintai.api.main:app --reload --env-file .env`. Terminal 2 : `python -m streamlit run ui/app.py`. Relevé par défaut : 72 °C, 6 mm/s, 85 %, 15 000 h.

| Essai | Affichage obtenu |
|---|---|
| API arrêtée | encadré rouge « API injoignable : uvicorn est-il lancé ? Vérifiez l'URL dans la barre latérale. » |
| API lancée, champ « Clé API » vide | encadré jaune « Erreur 401 : Clé API absente ou invalide » |
| API lancée, clé de `.env` | « Probabilité de panne : 95 % » puis encadré rouge « ALERTE : au-dessus du seuil 0.3 » |

Remarque pratique : un `st.text_input` n'est pris en compte qu'après Entrée (ou un clic ailleurs). Si l'on tape la clé puis qu'on clique directement sur « Prédire », l'ancienne valeur, vide, peut encore être envoyée.

## 7. Pourquoi CORS ne bloque pas Streamlit

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la page fonctionne. En TP2, le `fetch` s'exécutait **dans le navigateur** : la page de `localhost:5500` appelait une autre origine (`localhost:8000`), et le navigateur demandait d'abord l'autorisation (requête `OPTIONS` avec `Origin`).

Avec Streamlit, le navigateur n'appelle jamais l'API : il affiche seulement ce que le serveur Streamlit lui envoie. La requête vers `/v1/predict` part du **processus Python** (httpx), comme avec `curl` ou Java. Sans navigateur, il n'y a ni origine ni demande d'autorisation : CORS ne s'applique pas. En revanche, la clé API est toujours vérifiée, comme le montre l'essai à 401.

## 8. Tester sans serveur

- `test_client.py` injecte le `TestClient` dans `MaintaiClient(http=...)` : on teste le vrai client contre la vraie application, sans réseau ni uvicorn.
- `test_ui.py` exécute `ui/app.py` avec `AppTest`, sans navigateur. Pour l'onglet « Prédiction », il remplace `MaintaiClient.predict` par une réponse fixe (`monkeypatch`, probabilité 0,9475) : il vérifie **l'affichage** (« 95 % »), pas l'API. Chaque couche est ainsi testée séparément.

## 9. Difficultés rencontrées

| Problème | Cause | Solution |
|---|---|---|
| Starter du TP2 décompressé en fichiers à plat (`maintai-starter-tp2\maintai\api\main.py`) | archive créée sous Windows, séparateurs `\` non interprétés par macOS | script shell remplaçant `\` par `/` ; pour le TP3, utilisation de `unzip`, qui fait la conversion |
| Tests de l'UI qui échouent alors que le code semblait correct | `ui/app.py` modifié dans le dossier téléchargé, et non dans celui du dépôt | copie des fichiers dans `TPs/TP3/zakaria_khamlich/maintai-starter-tp3` ; vérification du `rootdir` affiché par pytest |
| Chemins de Streamlit pointant vers `miniforge/python3.13` | environnement conda `(base)` actif à la place du venv | `conda deactivate`, puis activation du venv du TP1 |
| `NotImplementedError` affichée dans la page alors que `client.py` était corrigé | Streamlit relance `app.py` à chaque modification, mais garde en mémoire les modules déjà importés (`maintai.client`) | redémarrage de Streamlit (Ctrl+C puis relance) |
| Erreur 401 avec l'API pourtant lancée | champ « Clé API » vide | saisie de la clé de `.env`, validée par Entrée |
| `Address already in use` au lancement d'uvicorn | un ancien uvicorn tournait encore sur le port 8000 | `lsof -ti :8000 \| xargs kill` |

## 10. Rendu Git

- Architecture du dépôt respectée : `TPs/TP3/zakaria_khamlich/maintai-starter-tp3`, comme pour le TP2
- `git status` avant commit : ni `.env`, ni `data/sensors.csv`, ni `models/` (exclus par le `.gitignore`)
- Lien de la pull request : …
- Tag `tp3` présent sur GitHub : oui / non
- Relecture : …

## 11. Ce qui reste flou

- Le rechargement partiel de Streamlit : savoir précisément ce qui est relu (le script) et ce qui ne l'est pas (les modules importés, le cache `@st.cache_data`).
- L'URL de l'API est saisie dans la barre latérale ; en déploiement réel, elle devrait plutôt venir de la configuration (`.env`), comme la clé côté serveur.
