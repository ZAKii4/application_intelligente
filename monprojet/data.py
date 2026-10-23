"""Chargement et découpage des données."""
import pandas as pd
from sklearn.model_selection import train_test_split

from monprojet import config


def load_data(path=None) -> pd.DataFrame:
    """Lit le fichier CSV et renvoie un DataFrame."""
    path = path if path is not None else config.DATA_PATH
    df = pd.read_csv(path)

    if config.TARGET not in df.columns:
        raise ValueError(
            f"La colonne cible '{config.TARGET}' est absente du fichier {path}. "
            f"Colonnes disponibles : {list(df.columns)}"
        )

    return df.dropna(subset=[config.TARGET]).reset_index(drop=True)


def feature_columns(df: pd.DataFrame) -> list:
    """Les colonnes d'entrée : celles de config.FEATURES, ou toutes sauf la cible et la date. (Fournie.)"""
    if config.FEATURES is not None:
        return list(config.FEATURES)
    excluded = {config.TARGET, config.TIME_COLUMN}
    return [c for c in df.columns if c not in excluded]


def _is_classification() -> bool:
    return str(config.TASK).lower().startswith("class")


def split(df: pd.DataFrame):
    """Renvoie X_train, X_test, y_train, y_test."""
    X = df[feature_columns(df)]
    y = df[config.TARGET]

    if config.SPLIT == "random":
        return train_test_split(
            X, y,
            test_size=config.TEST_SIZE,
            random_state=config.SEED,
            stratify=y if _is_classification() else None,
        )

    if config.SPLIT == "chronologique":
        if config.TIME_COLUMN not in df.columns:
            raise ValueError(f"Colonne de temps '{config.TIME_COLUMN}' introuvable.")
        order = pd.to_datetime(df[config.TIME_COLUMN]).argsort().values
        X_sorted, y_sorted = X.iloc[order], y.iloc[order]

        n_test = max(1, int(round(len(df) * config.TEST_SIZE)))
        n_train = len(df) - n_test
        return (X_sorted.iloc[:n_train], X_sorted.iloc[n_train:],
                y_sorted.iloc[:n_train], y_sorted.iloc[n_train:])

    raise ValueError(f"config.SPLIT doit valoir 'random' ou 'chronologique', pas '{config.SPLIT}'.")