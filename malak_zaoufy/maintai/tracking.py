
"""Suivi des entraînements avec MLflow : chaque entraînement devient un « run » qu'on peut comparer.

Les runs sont enregistrés dans mlflow.db (dossier courant) ;
on les consulte avec la commande : mlflow ui
"""

import hashlib
import os
from pathlib import Path

# Désactive un message d'information de MLflow.
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")

import mlflow
import mlflow.sklearn


# Nom de l'expérience commune à tous les entraînements MaintAI.
EXPERIMENT = "maintai"

# Type autorisé pour sauvegarder les modèles Random Forest.
# Nécessaire pour éviter l'erreur UntrustedTypesFoundException.
TRUSTED_TYPES = ["sklearn.tree._tree.Tree"]


def file_md5(path: Path) -> str:
    """
    Calcule l'empreinte MD5 d'un fichier.

    Cette empreinte permet d'identifier précisément
    la version des données utilisées pendant l'entraînement.
    Elle sera comparée à celle enregistrée par DVC.
    """
    h = hashlib.md5()

    with open(path, "rb") as f:
        # Lecture par blocs de 1 Mo pour éviter de charger
        # tout le fichier en mémoire.
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)

    return h.hexdigest()


def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    """
    Enregistre un entraînement dans MLflow.

    Informations enregistrées :
    - Les paramètres du modèle.
    - L'empreinte MD5 des données.
    - Les métriques d'évaluation.
    - Le modèle entraîné.

    Retourne l'identifiant unique du run MLflow.
    """

    # 1. Sélectionner l'expérience MaintAI.
    # Tous les entraînements seront regroupés dans cette expérience.
    mlflow.set_experiment(EXPERIMENT)

    # 2. Démarrer un nouveau run.
    # Chaque entraînement possède son propre identifiant.
    with mlflow.start_run() as run:

        # 3. Enregistrer les paramètres d'entraînement.
        # Exemple : model, C, threshold.
        mlflow.log_params(params)

        # 4. Enregistrer la version exacte des données.
        # Le nom du paramètre doit être exactement "data_md5".
        data_md5 = file_md5(data_path)
        mlflow.log_param("data_md5", data_md5)

        # 5. Enregistrer les métriques d'évaluation.
        # Exemple : recall, precision, accuracy.
        mlflow.log_metrics(metrics)

        # 6. Enregistrer le modèle Scikit-learn.
        # input_example permet à MLflow de connaître
        # le format des données attendues par le modèle.
        # TRUSTED_TYPES autorise le type interne utilisé
        # par les arbres de décision de Random Forest.
        mlflow.sklearn.log_model(
            model,
            name="model",
            input_example=X_example,
            skops_trusted_types=TRUSTED_TYPES
        )

        # 7. Récupérer l'identifiant unique du run.
        run_id = run.info.run_id

    # Retourner l'identifiant pour pouvoir le retrouver.
    return run_id
