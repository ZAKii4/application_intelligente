
"""Recherche automatique de configurations pour MaintAI.

Maximum : 30 runs MLflow.
Exécution : python -m maintai.gridsearch
"""

import itertools
import json

from maintai.config import get_settings
from maintai.data import load_data, split
from maintai.train import build_model, evaluate, evaluate_baseline
from maintai.tracking import log_run


def main():
    # 1. Définir les valeurs à tester
    models = ["logreg", "forest"]
    c_values = [0.01, 0.1, 1.0]
    thresholds = [0.2, 0.3, 0.4, 0.5, 0.6]

    # 2. Préparer les données une seule fois
    settings = get_settings()
    df = load_data(settings.data_path)
    X_train, X_test, y_train, y_test = split(df)

    baseline = evaluate_baseline(X_train, y_train, X_test, y_test)

    # 3. Générer les combinaisons (2 x 3 x 5 = 30)
    combinations = list(
        itertools.product(models, c_values, thresholds)
    )

    print(f"Nombre de configurations : {len(combinations)}")

    results = []

    # 4. Entraîner et enregistrer chaque configuration
    for number, (kind, C, threshold) in enumerate(combinations, start=1):
        model = build_model(kind, C)
        model.fit(X_train, y_train)

        metrics = evaluate(model, X_test, y_test, threshold)

        params = {
            "model": kind,
            "C": C,
            "threshold": threshold,
            "n_train": len(X_train),
            "gridsearch": True,
        }

        run_id = log_run(
            params=params,
            metrics={
                "accuracy": metrics["accuracy"],
                "recall": metrics["recall"],
                "precision": metrics["precision"],
                "baseline_recall": baseline["recall"],
            },
            model=model,
            X_example=X_train.head(3),
            data_path=settings.data_path,
        )

        result = {
            "run_id": run_id,
            "model": kind,
            "C": C,
            "threshold": threshold,
            **metrics,
        }
        results.append(result)

        print(
            f"[{number}/30] {kind}, C={C}, "
            f"threshold={threshold} | "
            f"recall={metrics['recall']} | "
            f"precision={metrics['precision']} | "
            f"accuracy={metrics['accuracy']}"
        )

    # 5. Trier les résultats par recall décroissant
    results.sort(key=lambda item: item["recall"], reverse=True)

    print("\n===== TOP 5 CONFIGURATIONS =====")
    for result in results[:5]:
        print(json.dumps(result, indent=2))

    print("\nGridSearch terminé : 30 runs MLflow enregistrés.")


if __name__ == "__main__":
    main()
