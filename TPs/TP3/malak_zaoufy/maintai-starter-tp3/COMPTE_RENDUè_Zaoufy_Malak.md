# Compte rendu · TP3 · Une interface Streamlit pour MaintAI

**Nom :** Malak Zaoufy
**Séance :** 6 · thème 2.5
**Date :** 11/11/2026

---

## 1. Mise en place

- Starter du TP3 copié, environnement Python 3.13 activé, `pip install -r requirements.txt` (ajoute Streamlit 1.66.1).
  Le premier essai a échoué sur un `ReadTimeoutError` (connexion lente pendant le téléchargement de Streamlit) ;
  relancé avec `pip install --default-timeout=300 --retries 10 -r requirements.txt`.
- `python -m maintai.dataset` puis `python -m maintai.train` :

| Modèle | Accuracy | Recall | Precision | Seuil |
|---|---|---|---|---|
| Modèle entraîné | 0.904 | 0.75 | 0.622 | 0.3 |
| Baseline (toujours « pas de panne ») | 0.864 | 0.0 | – | – |

  4000 relevés d'entraînement, 1000 de test. La baseline a une bonne accuracy mais ne détecte aucune panne
  (recall 0) : c'est pour ça qu'on regarde le recall et qu'on a choisi un seuil bas (0.3).
- `.env` recréé à partir de celui du TP2 (il n'est pas dans Git).
- `python -m pytest` au départ : **5 failed, 18 passed**.

## 2. Lancer la page

| Commande | Ce qu'on voit dans le navigateur |
|---|---|
| `streamlit run ui/app.py` | la page s'ouvre mais affiche `ModuleNotFoundError: No module named 'maintai'` |
| `python -m streamlit run ui/app.py` | la page fonctionne |

**Pourquoi ?** Python cherche les modules dans une liste de dossiers qui dépend de la façon de lancer.
Avec `python -m`, le dossier courant (la racine du projet, qui contient `maintai/`) est ajouté à cette liste.
Avec `streamlit run`, seul le dossier du script (`ui/`) y est : `maintai` est introuvable.
Le TP4 règle le problème en installant MaintAI comme un package.

## 3. Sprint 1 · L'onglet « Données »

Ajouté dans `ui/app.py`, sous `with onglet_donnees:` :

1. trois indicateurs avec `st.columns(3)` et `.metric` : nombre de relevés, taux de panne (`df.failure.mean()`
   affiché avec `:.1%`), température moyenne ;
2. une liste déroulante `st.selectbox("Variable", FEATURES)` ;
3. le taux de panne par tranche : `pd.cut(df[variable], bins=10)`, puis `groupby(...).failure.mean()`.
   Les étiquettes sont le milieu de chaque tranche (`round(i.mid, 1)`), gardé en nombre pour que les barres
   restent dans l'ordre ;
4. un nuage `st.scatter_chart` température / vibration, coloré par une colonne « oui / non » plus lisible que 0 / 1.

**Observation avec `vibration_mm_s` :** le taux de panne augmente avec la vibration, de [à compléter] % pour
les vibrations faibles à [à compléter] % pour les plus fortes.
Pour la température, il passe d'environ 0 % (vers 27 °C) à environ 37 % (vers 91 °C).
La variable dont les barres montent le plus est celle qui compte le plus : [à compléter : vibration ou température].

Après le sprint 1 : **4 failed, 19 passed**.

## 4. Sprint 2 · L'onglet « Prédiction »

**`maintai/client.py`, méthode `predict` :** un POST JSON vers `/v1/predict` avec l'en-tête `X-API-Key`
(seulement si une clé est donnée). On utilise `self.http.post` et non `httpx.post`, pour que les tests puissent
fournir leur propre client. Si le code n'est pas 200, on lève `APIError(code, detail)`.
→ **1 failed, 22 passed**.

**`ui/app.py`, sous `if envoye:` :** on crée `MaintaiClient(url, api_key=cle)`, puis :
- `try` : appel de `predict(releve)` ;
- `except APIError` : `st.warning` avec le code et le message ;
- `except httpx.HTTPError` : `st.error("API injoignable : uvicorn est-il lancé ?")` ;
- `else` : `st.metric` avec la probabilité en %, puis `st.error` (alerte) ou `st.success` (normal).

Lancement : terminal 1 `uvicorn maintai.api.main:app --reload --env-file .env`,
terminal 2 `python -m streamlit run ui/app.py`, clé saisie dans la barre latérale.

| Essai | Ce qui s'affiche |
|---|---|
| valeurs par défaut (72 °C, 6 mm/s, 85 %, 15000 h), bonne clé | Probabilité de panne : 95 %, message rouge « ALERTE : au-dessus du seuil 0.3 » |
| valeurs par défaut, fausse clé | message jaune « Erreur 401 : Clé API absente ou invalide » |
| API arrêtée (Ctrl+C dans le terminal 1) | message rouge « API injoignable : uvicorn est-il lancé ? » |
| essai libre : température 26 °C, autres valeurs par défaut | Probabilité de panne : 3 %, message vert « Fonctionnement normal (seuil 0.3) » |

Le résultat disparaît après un autre clic : c'est normal, `envoye` ne vaut `True` que pendant la relance
provoquée par le bouton.

Après le sprint 2 : **23 passed**.

## 5. Pourquoi pas de CORS ?

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, pourtant tout marche.
CORS est une règle appliquée **par le navigateur** quand du JavaScript d'une origine (en TP2, la page du port 5501)
appelle une autre origine (l'API, port 8000).
Avec Streamlit, le navigateur ne parle qu'au serveur Streamlit (8501). C'est le **serveur Python** qui appelle
l'API avec httpx, et aucun navigateur ne vérifie cet appel, donc pas de CORS.
La clé API reste nécessaire : c'est elle, pas CORS, qui protège l'API.

## 6. Tester sans serveur

- `tests/test_client.py` donne à `MaintaiClient` le `TestClient` de la séance 5 (`http=client`) :
  la requête va directement à l'application, sans uvicorn.
- `tests/test_ui.py` exécute la page avec `AppTest`, sans navigateur, et remplace l'appel à l'API par une réponse
  connue (`monkeypatch`) : il vérifie la page, pas l'API.

## 7. Résultat final

```
python -m pytest
23 passed, 1 warning
```
(Le warning `StarletteDeprecationWarning` vient de la bibliothèque FastAPI/Starlette, pas de notre code.)

Critères de réussite :
- [x] 23 tests passent
- [x] onglet « Données » : trois indicateurs, les barres et le nuage
- [x] onglet « Prédiction » : la probabilité, l'erreur 401 et « API injoignable » selon le cas
- [ ] pull request fusionnée et tag `tp3`

## 8. Difficultés rencontrées

- Timeout de pip pendant le téléchargement de Streamlit : réglé avec `--default-timeout=300 --retries 10`.
- Création du `.env` à la main : attention à ce que Windows ne le nomme pas `.env.txt`.
