# Choix du modèle — prédiction des pannes

Date : 21/10/26 · Groupe : non renseigné

## Contexte
Le projet prédit la classe `failure` (0 ou 1) à partir de mesures de température, vibration, charge et durée de fonctionnement. La métrique principale est le rappel de la classe positive : manquer une panne peut retarder une intervention de maintenance. La précision et le F1 sont également examinés pour tenir compte des fausses alertes.

## Données et découpage
- Fichier : `data/exemple_pannes.csv`.
- Volume : 5 000 lignes ; 4 variables explicatives et 1 cible ; aucune valeur manquante constatée.
- Répartition de la cible : 4 122 cas `failure = 0` et 878 cas `failure = 1`.
- Découpage : aléatoire stratifié, avec 80 % pour l'entraînement et 20 % pour le test ; graine 42. Le jeu de test compte 1 000 observations.
- Les données source sont présentes dans le dépôt, mais leur provenance, leur licence et leur caractère réel ou synthétique ne sont pas précisés.

## Résultats sur le jeu de test

| Modèle | Rappel (métrique principale) | Accuracy | Précision | F1 |
|---|---:|---:|---:|---:|
| Dummy (baseline) | 0,000 | 0,824 | 0,000 | 0,000 |
| LogisticRegression | 0,574 | 0,889 | 0,737 | 0,645 |
| DecisionTree | 0,597 | 0,839 | 0,538 | 0,566 |
| RandomForest | 0,545 | 0,873 | 0,671 | 0,602 |
| KNeighbors | 0,540 | 0,878 | 0,699 | 0,609 |

## Décision
Le DecisionTree est retenu par le critère configuré, le rappel : son score de 0,597 est le meilleur des candidats et dépasse la baseline de 0,597 point (la baseline a un rappel nul, donc un gain relatif n'est pas défini). Il détecte davantage de cas de panne que les autres modèles testés, mais sa précision (0,538) est plus faible et son accuracy n'est pas la meilleure.

Aucun seuil métier chiffré n'étant fourni, l'acceptation est limitée au critère de comparaison automatisé du projet : le meilleur modèle doit faire mieux que la baseline sur le rappel. Ce critère est satisfait. Cela ne constitue pas une validation pour un déploiement réel.

## Limites
- Le rappel de 0,597 implique qu'environ 40,3 % des pannes du jeu de test ne sont pas détectées ; le modèle ne doit pas remplacer les contrôles ni l'avis du personnel de maintenance.
- Les scores proviennent d'un seul découpage aléatoire de 1 000 lignes ; aucune validation croisée, chronologique ou externe n'est rapportée.
- La baseline prédit toujours la classe majoritaire : son accuracy de 0,824 ne signifie pas qu'elle détecte les pannes (son rappel est nul).
- La source, la licence et la nature des données ne sont pas précisées. Les résultats doivent être confirmés sur des données représentatives avant toute utilisation opérationnelle.

## Vérification d'exécution
- `python -m monprojet.train` : entraînement et comparaison exécutés ; modèle retenu : DecisionTree ; métriques enregistrées dans `models/metrics.json`.
- `python -m pytest -q` : 8 tests réussis.
