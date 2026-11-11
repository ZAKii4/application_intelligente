# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :** …  ·  **Membres :** Zakaria Khamlich, …  ·  **Date :** 11/11/2026

---

## 1. Mise en place (`TPs/TP3/zakaria_khamlich/maintai-starter-tp3`)

Commandes (macOS, environnement du TP1 réutilisé) :

```bash
git switch main && git pull
git switch -c tp3
# contenu du starter copié dans TPs/TP3/zakaria_khamlich/maintai-starter-tp3
source ~/Downloads/S4_maintai-starter-tp1/.venv/bin/activate
pip install -r requirements.txt      # ajoute streamlit 1.66.1
python -m maintai.dataset            # 5000 relevés (taux de panne : 13.6 %)
python -m maintai.train
cp <dossier TP2>/.env .env           # .env n'est pas dans Git
python -m pytest
```

Dernière ligne de `python -m pytest` juste après la mise en place :

```
=========== 5 failed, 18 passed, 1 warning in 4.74s ============
```

Les 5 échecs :

- `tests/test_client.py` (3 tests) : `NotImplementedError: TP3 sprint 2 : MaintaiClient.predict`, le client n'envoie encore rien ;
- `tests/test_ui.py` (2 tests) : `IndexError: list index out of range` sur `at.metric[...]`, la page n'affiche encore aucun indicateur.

## 2. Lancer la page de deux façons

| Commande | Ce qu'on voit dans le navigateur |
|---|---|
| `streamlit run ui/app.py` | une erreur `ModuleNotFoundError: No module named 'maintai'` |
| `python -m streamlit run ui/app.py` | la page MaintAI s'affiche sur http://localhost:8501, avec les onglets « Données » et « Prédiction » |

Pourquoi cette différence ? `import maintai` cherche le module dans une liste de dossiers (`sys.path`). Avec `streamlit run ui/app.py`, Python ajoute le dossier **du script** (`ui/`), où il n'y a pas de `maintai/`. Avec `python -m`, Python ajoute le **dossier courant** (la racine du projet), qui contient `maintai/`. Le TP4 règle le problème pour de bon en installant le projet comme package (`pip install -e .`).

## 3. Sprint 1 : l'onglet « Données »

Code ajouté dans `ui/app.py`, sous `with onglet_donnees:` :

```python
df = charger(get_settings().data_path)

c1, c2, c3 = st.columns(3)
c1.metric("Relevés", len(df))
c2.metric("Taux de panne", f"{df.failure.mean():.1%}")
c3.metric("Température moyenne", f"{df.temperature_c.mean():.1f} °C")

variable = st.selectbox("Variable", FEATURES)

tranches = pd.cut(df[variable], bins=10)
taux = df.groupby(tranches, observed=True).failure.mean()
taux.index = [round(i.mid, 1) for i in taux.index]  # des nombres, pas du texte
st.subheader(f"Taux de panne par tranche de {variable}")
st.bar_chart(taux)

nuage = df.assign(panne=df.failure.map({0: "non", 1: "oui"}))
st.subheader("Température et vibration")
st.scatter_chart(nuage, x="temperature_c", y="vibration_mm_s", color="panne")
```

Explications :

- `failure` vaut 0 ou 1 : sa **moyenne** est donc la part de pannes, affichée en pourcentage avec `:.1%` ;
- `pd.cut(..., bins=10)` range chaque valeur dans l'une des 10 tranches de même largeur ; `groupby(...).failure.mean()` donne le taux de panne de chaque tranche ;
- l'étiquette de chaque barre est le **milieu** de la tranche (`i.mid`), gardé comme **nombre** : avec du texte, les barres seraient triées comme du texte (« 10 » avant « 2 ») ; une décimale est gardée car les valeurs de vibration sont petites (un arrondi à l'entier créerait des étiquettes en double) ;
- `color=` attend le nom d'une colonne : une colonne « oui / non » donne une légende plus lisible que 0 / 1.

Valeurs affichées : **5000** relevés, taux de panne **13,6 %**, température moyenne **≈ 60 °C**.

Choisissez `vibration_mm_s`. Comment évolue le taux de panne ? Laquelle des deux variables compte le plus ?

Le taux de panne **augmente fortement avec la vibration** : quasi nul dans les premières tranches (vibration faible), il dépasse la moitié des relevés dans les tranches les plus hautes. Avec la température, la hausse existe mais elle est plus progressive. **La vibration compte le plus** : dans `dataset.py`, le risque augmente de 0,6 par mm/s contre 0,08 par °C ; même rapporté à l'écart-type de chaque variable (environ 2 mm/s contre 10 °C), l'effet d'un écart-type de vibration (≈ 1,2) dépasse celui d'un écart-type de température (≈ 0,8).

Le rôle de `@st.cache_data` : Streamlit relance **tout le script** à chaque clic ; sans cache, le CSV serait relu à chaque changement de la liste déroulante. Avec `@st.cache_data`, il est lu une seule fois et gardé en mémoire.

Après le sprint 1, `python -m pytest` :

```
4 failed, 19 passed
```

## 4. Sprint 2 : l'onglet « Prédiction »

`MaintaiClient.predict` (`maintai/client.py`) :

```python
def predict(self, reading: dict) -> dict:
    headers = {"X-API-Key": self.api_key} if self.api_key else {}
    r = self.http.post("/v1/predict", json=reading, headers=headers)
    if r.status_code != 200:
        raise APIError(r.status_code, r.json().get("detail"))
    return r.json()
```

C'est le `fetch` du TP2, en Python : un POST JSON vers `/v1/predict` avec l'en-tête `X-API-Key`. On utilise `self.http.post(...)` et non `httpx.post(...)` : les tests passent leur propre client (`http=client`) et peuvent ainsi appeler l'application directement, sans serveur.

Après `client.py`, `python -m pytest` :

```
1 failed, 22 passed
```

Le bloc `if envoye:` (`ui/app.py`) :

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

Trois issues possibles : l'API **refuse** (`APIError` : 401, 422, 503 → avertissement jaune), l'API est **injoignable** (`httpx.HTTPError` → erreur rouge), ou l'API **répond 200** (probabilité et alerte). Pour une erreur 422, `detail` est une liste : on affiche le premier message.

Le formulaire (`st.form`) : déplacer un curseur ne relance rien ; seul le bouton « Prédire » relance le script, et `envoye` ne vaut `True` que pendant cette relance. C'est pourquoi le résultat disparaît si l'on touche ensuite un autre widget.

Dernière ligne de `python -m pytest` à la fin du TP :

```
23 passed
```

## 5. Essais réels

Terminal 1 : `uvicorn maintai.api.main:app --reload --env-file .env`. Terminal 2 : `python -m streamlit run ui/app.py`. Clé de `.env` saisie dans la barre latérale.

| Essai | Ce qui s'affiche |
|---|---|
| valeurs par défaut (72 °C, 6 mm/s, 85 %, 15 000 h), bonne clé | « Probabilité de panne : 95 % » puis, en rouge, « ALERTE : au-dessus du seuil 0.3 » |
| valeurs par défaut, fausse clé | en jaune : « Erreur 401 : Clé API absente ou invalide » |
| API arrêtée (Ctrl+C dans le terminal 1) | en rouge : « API injoignable : uvicorn est-il lancé ? Vérifiez l'URL dans la barre latérale. » |

## 6. Pourquoi pas de CORS ?

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant tout marche. En TP2, le `fetch` s'exécutait **dans le navigateur** : la page de `localhost:5500` appelait `localhost:8000`, une autre origine ; le navigateur demandait donc la permission (requête `OPTIONS` avec l'en-tête `Origin`) et bloquait la page du port 5501. En TP3, le navigateur ne fait qu'**afficher** la page envoyée par Streamlit et n'appelle jamais l'API. C'est le **serveur Streamlit, en Python** (`httpx`), qui envoie le POST, comme `curl` ou le programme Java : pas de navigateur, donc pas d'origine ni de demande de permission. CORS ne s'applique pas ; la **clé API**, elle, est toujours vérifiée.

## 7. Tester sans serveur

- `tests/test_client.py` crée `MaintaiClient(api_key="test-key", http=client)` avec le `TestClient` de la séance 5 : la requête va directement à l'application, sans uvicorn ni port. Il vérifie le cas 200, la mauvaise clé (401) et le relevé invalide (422).
- `tests/test_ui.py` exécute la page avec `AppTest`, sans navigateur. Pour la prédiction, il remplace `MaintaiClient.predict` par une réponse connue (`monkeypatch`, probabilité 0,9475) : il vérifie que **la page** affiche « 95 % », pas que l'API fonctionne. Le premier indicateur doit être le nombre de relevés (`"2000"` avec les données de test), d'où l'ordre imposé des trois indicateurs.

## 8. Le rendu Git

- `git status` avant le commit : ni `.env`, ni `data/*.csv`, ni `models/` : oui, vérifié
- Lien de la pull request : …
- Le tag `tp3` existe sur GitHub : oui / non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  …

## 9. Ce qui reste flou

…
