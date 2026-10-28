"""Entraîne chaque modèle candidat, l'évalue sur le jeu de test et les compare.

Usage, depuis la racine du projet : python -m monprojet.train
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (accuracy_score, f1_score, mean_absolute_error, mean_squared_error,
                             precision_score, r2_score, recall_score)
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from monprojet import config
from monprojet.data import load_data, split
from monprojet.models import candidates

HIGHER_IS_BETTER = {"accuracy": True, "recall": True, "precision": True, "f1": True,
                    "mae": False, "rmse": False, "r2": True}


def build_preprocessing(X: pd.DataFrame) -> ColumnTransformer:
    """Prépare les colonnes : nombres mis à l'échelle, catégories encodées, texte vectorisé. (Fournie.)"""
    text = [config.TEXT_COLUMN] if config.TEXT_COLUMN else []
    numeric = [c for c in X.columns if c not in text and pd.api.types.is_numeric_dtype(X[c])]
    categorical = [c for c in X.columns if c not in text and c not in numeric]
    steps = []
    if numeric:
        steps.append(("nombres", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numeric))
    if categorical:
        steps.append(("categories", make_pipeline(SimpleImputer(strategy="most_frequent"),
                                                  OneHotEncoder(handle_unknown="ignore")), categorical))
    if text:
        steps.append(("texte", TfidfVectorizer(), config.TEXT_COLUMN))
    return ColumnTransformer(steps, sparse_threshold=0)


def _is_classification() -> bool:
    return str(config.TASK).lower().startswith("class")


def evaluate(model, X_test, y_test) -> dict:
    """Prédit sur le jeu de test et renvoie {nom de la métrique: valeur}."""
    y_pred = model.predict(X_test)

    if _is_classification():
        labels = np.unique(y_test)
        if len(labels) == 2:
            pos_label = 1 if 1 in labels else labels[-1]
            kwargs = {"average": "binary", "pos_label": pos_label, "zero_division": 0}
        else:
            kwargs = {"average": "macro", "zero_division": 0}

        scores = {
            "accuracy": accuracy_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred, **kwargs),
            "precision": precision_score(y_test, y_pred, **kwargs),
            "f1": f1_score(y_test, y_pred, **kwargs),
        }
    else:
        scores = {
            "mae": mean_absolute_error(y_test, y_pred),
            "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
            "r2": r2_score(y_test, y_pred),
        }

    return {name: round(float(value), 3) for name, value in scores.items()}


def main() -> None:
    """Entraîne chaque candidat, l'évalue, compare, et sauvegarde."""
    df = load_data()
    X_train, X_test, y_train, y_test = split(df)
    print(f"Train : {len(X_train)} lignes | Test : {len(X_test)} lignes")

    resultats = {}
    modeles = {}
    for nom, estimateur in candidates().items():
        model = Pipeline([
            ("preparation", build_preprocessing(X_train)),
            ("modele", estimateur),
        ])
        model.fit(X_train, y_train)
        resultats[nom] = evaluate(model, X_test, y_test)
        modeles[nom] = model
        print(f"  {nom:<22} {resultats[nom]}")

    metric = config.MAIN_METRIC
    higher = HIGHER_IS_BETTER[metric]
    tableau = pd.DataFrame(resultats).T.sort_values(metric, ascending=not higher)
    print(f"\nComparaison (triée par {metric}) :")
    print(tableau.to_string())

    best = tableau.index[0]
    print(f"\nMeilleur modèle : {best} ({metric} = {resultats[best][metric]})")

    models_dir = Path(config.MODELS_DIR)
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(modeles[best], models_dir / "model.joblib")
    with open(models_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump({"main_metric": metric, "best": best, "results": resultats},
                  f, indent=2, ensure_ascii=False)
    print(f"Modèle et métriques sauvegardés dans {models_dir}/")


if __name__ == "__main__":
    main()