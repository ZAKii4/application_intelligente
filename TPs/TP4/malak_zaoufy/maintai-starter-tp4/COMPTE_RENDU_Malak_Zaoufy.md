# Compte rendu · TP4 : MaintAI devient un package Python

**Groupe :** …  ·  **Membres :** Malak Zaoufy  ·  **Date :** 12/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP4.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP4`, avec son propre `.venv`)

Dernière ligne de `python -m pytest` juste après `pip install -r requirements.txt` :

```
2 failed, 25 passed
```

Quels sont les deux tests qui échouent, et pourquoi ?

Les deux tests de `tests/test_package.py`. Ils vérifient que `maintai` est installé comme un package
(version lisible par `pip show`, commande `maintai-predict` disponible). Au départ, `pyproject.toml`
contient encore les TODO et le projet n'a pas été installé avec `pip install -e .` : ces tests échouent donc.

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

Vos sections `dependencies` et `[project.scripts]` :

```toml
dependencies = [
    "numpy>=2.4",
    "pandas>=3.0",
    "scikit-learn>=1.8",
    "joblib>=1.5",
    "httpx>=0.28",
]

[project.scripts]
maintai-predict = "maintai.cli:main"
```

Pourquoi `pytest` et `fastapi` ne sont-ils pas dans `dependencies` ?

`dependencies` ne contient que ce dont le cœur du package (`config.py`, `data.py`, `train.py`, `predict.py`,
`client.py`) a besoin pour fonctionner. `pytest` ne sert qu'aux développeurs pour lancer les tests, et
`fastapi` qu'à ceux qui veulent servir l'API. Ils sont donc dans les groupes optionnels `dev` et `api`
(et `streamlit` dans `ui`), installés sur demande : `pip install -e ".[api,dev]"`. Un collègue qui veut
seulement la commande `maintai-predict` n'a pas à les installer.

Sortie de `pip show maintai` (les quatre premières lignes) :

```
Name: maintai
Version: 0.2.0
Summary: MaintAI : prédiction de panne de machines industrielles à partir de relevés de capteurs
Home-page:
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
27 passed, 1 warning in 37.58s
```

(Le warning `StarletteDeprecationWarning` vient de la bibliothèque FastAPI/Starlette, pas de notre code.)

Placez-vous dans un autre dossier (`cd %TEMP%`) et lancez `maintai-predict 72 6 85 15000`, puis `python -c "import maintai; print(maintai.__file__)"`. Qu'affichent ces deux commandes ? Où Python trouve-t-il le code de `maintai` ?

```
PS C:\Users\PC\AppData\Local\Temp> maintai-predict 72 6 85 15000
Probabilité de panne : 95 % (ALERTE)
PS C:\Users\PC\AppData\Local\Temp> python -c "import maintai; print(maintai.__file__)"
C:\Users\PC\Downloads\TP4\maintai-starter-tp4\maintai\__init__.py
```

La commande fonctionne depuis n'importe quel dossier. Python trouve le code **dans mon dossier de projet**
(`TP4\maintai-starter-tp4\maintai\`), pas dans une copie : `pip install -e .` a seulement posé un lien
(`__editable__.maintai-0.2.0.pth`) dans `site-packages`. `pip show maintai` le confirme avec
`Editable project location: C:\Users\PC\Downloads\TP4\maintai-starter-tp4`.

Conséquence : `streamlit run ui/app.py` fonctionne maintenant sans `python -m`, alors qu'au TP3 il donnait
`ModuleNotFoundError: No module named 'maintai'`.

Modifiez le message affiché par `maintai/cli.py`, puis relancez `maintai-predict` sans réinstaller. Le changement est-il visible ? Pourquoi ?

Oui : après avoir remplacé « Probabilité de panne » par « Risque de panne » dans `cli.py`, la commande
affiche le nouveau texte tout de suite, sans `pip install`. L'installation éditable est un lien vers mon
dossier : Python relit mes fichiers à chaque lancement. (Message d'origine remis ensuite, 27 tests verts.)

## 3. Sprint 2 : construire et installer le wheel

Sortie de `dir dist` après `python -m build` :

```
    Répertoire : C:\Users\PC\Downloads\TP4\maintai-starter-tp4\dist

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----        11/12/2026  11:19 AM          11635 maintai-0.2.0-py3-none-any.whl
-a----        11/12/2026  11:18 AM          12438 maintai-0.2.0.tar.gz
```

Contenu du wheel (`tar -tf dist\maintai-0.2.0-py3-none-any.whl`). Le modèle, les tests et `ui/` y sont-ils ? Pourquoi ?

```
maintai/__init__.py
maintai/cli.py
maintai/client.py
maintai/config.py
maintai/data.py
maintai/dataset.py
maintai/predict.py
maintai/train.py
maintai/api/__init__.py
maintai/api/main.py
maintai/api/schemas.py
maintai/api/security.py
maintai-0.2.0.dist-info/METADATA
maintai-0.2.0.dist-info/WHEEL
maintai-0.2.0.dist-info/entry_points.txt
maintai-0.2.0.dist-info/top_level.txt
maintai-0.2.0.dist-info/RECORD
```

**Non** : ni le modèle (`models/`), ni les tests (`tests/`), ni `ui/`. La section `packages.find` de
`pyproject.toml` ne retient que le dossier `maintai/` (et son sous-package `api/`). Le wheel contient le code
à installer, plus ses métadonnées (`METADATA` : nom, version, dépendances ; `entry_points.txt` : la commande
`maintai-predict`). Le modèle est un fichier produit par l'entraînement, qui change sans que le code change,
et les tests et l'interface ne servent pas à l'utilisateur de la commande.

Dans un environnement neuf (`%TEMP%\essai`), installez le wheel et lancez `maintai-predict` :

| Étape | Ce qui s'affiche |
|---|---|
| sans `MAINTAI_MODELS_DIR` | `Modèle introuvable : C:\Users\PC\AppData\Local\Temp\essai\.venv\Lib\site-packages\models\model.joblib` puis « Entraînez-le (python -m maintai.train) ou indiquez son dossier dans MAINTAI_MODELS_DIR. » |
| avec `MAINTAI_MODELS_DIR` vers vos `models` | trois `InconsistentVersionWarning` (« Trying to unpickle estimator StandardScaler / LogisticRegression / Pipeline from version 1.8.0 when using version 1.9.1 »), puis `Probabilité de panne : 95 % (ALERTE)` |
| après `pip install scikit-learn==1.8.0` | `Probabilité de panne : 95 % (ALERTE)`, sans avertissement |

Commande utilisée pour la variable sous PowerShell :
`$env:MAINTAI_MODELS_DIR="C:\Users\PC\Downloads\TP4\maintai-starter-tp4\models"`.

D'où vient l'avertissement `InconsistentVersionWarning` ? Quelle ligne de `models/model_info.json` permet de le comprendre ?

`pyproject.toml` demande seulement `scikit-learn>=1.8` : dans l'environnement neuf, pip a donc installé la
version la plus récente, **1.9.1**. Or le modèle a été enregistré (pickle avec joblib) par la version 1.8.0.
scikit-learn prévient qu'il relit des objets écrits par une autre version, ce qui peut donner des erreurs ou
des résultats faux. La ligne qui l'explique :

```json
"sklearn_version": "1.8.0"
```

Installer exactement cette version (`scikit-learn==1.8.0`, celle de `requirements.txt`) fait disparaître
l'avertissement.

## 4. Questions de compréhension

1. Quelle différence entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?

   `requirements.txt` fixe des versions **exactes** (`==`) de tout l'environnement de travail, outils compris
   (pytest, fastapi, streamlit…) : il sert à reproduire à l'identique l'environnement qui a entraîné le
   modèle. `dependencies` donne des versions **minimales** (`>=`) des seules bibliothèques importées par le
   package : un package doit pouvoir s'installer à côté d'autres sans imposer une version précise.
   C'est pourquoi le collègue a eu besoin des deux : le wheel pour le code, et la version exacte de
   scikit-learn pour relire le modèle.

2. Quelle différence entre `pip install -e .` et `pip install dist\maintai-0.2.0-py3-none-any.whl` ?

   `pip install -e .` (éditable) pose un **lien** vers le dossier du projet : les modifications du code sont
   visibles immédiatement. C'est pour **développer**. Le wheel est une **copie** du code, figée au moment du
   `python -m build`, installée dans `site-packages` : modifier le projet ne la change plus, il faut une
   nouvelle version, un nouveau build et une réinstallation. C'est pour **livrer**, à quelqu'un qui n'a que
   le fichier `.whl`.

3. Qu'est-ce qu'un « point d'entrée » (`[project.scripts]`) ? Où pip crée-t-il le fichier `maintai-predict.exe` ?

   C'est une ligne qui associe un nom de commande à une fonction Python :
   `maintai-predict = "maintai.cli:main"` veut dire « la commande `maintai-predict` appelle la fonction
   `main` du module `maintai.cli` ». Au moment de l'installation, pip crée un petit exécutable
   `maintai-predict.exe` dans le dossier `Scripts` de l'environnement actif (chez moi
   `C:\Users\PC\Downloads\TP4\.venv\Scripts\`, et `...\Temp\essai\.venv\Scripts\` pour le wheel). Ce dossier
   est dans le `PATH` quand l'environnement est activé, d'où une commande utilisable partout.

## 5. Le rendu Git

- Lien de la pull request : …
- Le tag `tp4` existe sur GitHub : oui / non
- `git status` avant le commit : `dist/`, `build/` ou `maintai.egg-info/` apparaissaient-ils ? non (exclus par le `.gitignore` du starter, comme `.venv`)

## 6. Ce qui reste flou

- Difficultés rencontrées et comprises :
  - `maintai-predict` n'était pas reconnu : `[project.scripts]` avait été complété après la première
    installation. Le `.exe` n'est créé qu'à l'installation : relancer `pip install -e .` l'a créé.
  - `python -m build` a échoué une fois sur un `ReadTimeoutError` en téléchargeant setuptools (connexion
    lente) : réglé avec `$env:PIP_DEFAULT_TIMEOUT="300"` avant de relancer.
  - Au premier essai dans `%TEMP%\essai`, `pip` désignait le Python global et non le `.venv` (visible dans
    la ligne `Location` de `pip show`) : l'essai n'était pas dans un environnement neuf. Refait en utilisant
    `python -m pip`, qui installe toujours dans l'environnement du `python` actif.
- Ce qui reste flou : comment livrer le modèle en pratique (le mettre dans le package, le télécharger au
  premier lancement, ou le fournir à part avec `MAINTAI_MODELS_DIR` comme ici) et comment garantir
  automatiquement la bonne version de scikit-learn chez l'utilisateur.
