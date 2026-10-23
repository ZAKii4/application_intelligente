"""Les modèles à comparer."""
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from monprojet import config


def _is_classification() -> bool:
    return str(config.TASK).lower().startswith("class")


def candidates() -> dict:
    """Renvoie un dictionnaire {nom: modèle scikit-learn non entraîné}."""
    seed = config.SEED

    if _is_classification():
        return {
            "baseline": DummyClassifier(strategy="most_frequent"),
            "logistic_regression": LogisticRegression(max_iter=1000, random_state=seed),
            "decision_tree": DecisionTreeClassifier(max_depth=5, random_state=seed),
            "random_forest": RandomForestClassifier(n_estimators=200, random_state=seed),
            "gradient_boosting": GradientBoostingClassifier(random_state=seed),
            "knn": KNeighborsClassifier(n_neighbors=5),
        }

    return {
        "baseline": DummyRegressor(strategy="mean"),
        "ridge": Ridge(alpha=1.0),
        "decision_tree": DecisionTreeRegressor(max_depth=5, random_state=seed),
        "random_forest": RandomForestRegressor(n_estimators=200, random_state=seed),
        "gradient_boosting": GradientBoostingRegressor(random_state=seed),
        "knn": KNeighborsRegressor(n_neighbors=5),
    }