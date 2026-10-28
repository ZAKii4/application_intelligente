# TP0 : MaintAI
**Nom :** Zakaria Khamlich · **Groupe :** G3
## Le problème
Prédire une panne à partir de quatre variables de capteurs et d'utilisation (température, vibration, charge et heures de fonctionnement). Une panne manquée peut entraîner l'arrêt d'une ligne : le rappel est donc la métrique principale.
## Résultats sur le jeu de test
Entraînement sur 4 000 lignes et évaluation sur 1 000 lignes, avec un découpage aléatoire stratifié (graine 42).

| Modèle | Accuracy | Rappel | Précision | F1 |
|---|---:|---:|---:|---:|
| Baseline | 0.824 | 0.000 | 0.000 | 0.000 |
| Régression logistique | 0.889 | 0.574 | 0.737 | 0.645 |
| Arbre de décision | 0.873 | 0.540 | 0.674 | 0.599 |
| Forêt aléatoire | 0.881 | 0.557 | 0.705 | 0.622 |
| Gradient boosting | 0.888 | 0.608 | 0.713 | 0.656 |
| K plus proches voisins (KNN) | 0.878 | 0.540 | 0.699 | 0.609 |

L'accuracy mesure la proportion totale de prédictions correctes ; le rappel mesure la proportion de pannes réellement détectées ; la précision mesure la proportion d'alertes qui correspondent effectivement à une panne. Le F1 résume le compromis entre rappel et précision. La baseline prédit toujours la classe majoritaire (absence de panne) : son accuracy de 0.824 paraît élevée, mais son rappel nul montre qu'elle ne détecte aucune panne.
## Mon choix, et pourquoi
Je retiens le gradient boosting, car il obtient le meilleur rappel (0.608), notre métrique principale : il détecte environ 61 pannes sur 100, contre aucune pour la baseline. Sa précision de 0.713 signifie qu'environ 71 alertes sur 100 correspondent à une panne. La régression logistique a la meilleure accuracy (0.889) et la meilleure précision (0.737), mais son rappel est inférieur (0.574) : elle détecte moins de pannes. Par rapport à la baseline, le gradient boosting améliore le rappel de 0.608 point et l'accuracy de 0.064 point.
## Le critère (rappel >= 0,75) est-il atteint ?
Non. Le meilleur rappel obtenu est 0.608, soit 0.142 point en dessous du seuil de 0.75. Le modèle manque donc encore environ 39,2 % des pannes présentes dans ce jeu de test ; il ne satisfait pas le critère d'acceptation.
## Ce qui reste flou
La provenance et la représentativité des données restent à confirmer. Un test sur d'autres machines ou périodes serait nécessaire pour vérifier la fiabilité des résultats, et le compromis acceptable entre pannes manquées et fausses alertes reste à définir.

# Deuxième jeu de données : CantineAI
**Nom :** Zakaria Khamlich · **Groupe :** G3
## Le problème
Prédire le nombre de repas servis à la cantine à partir des informations disponibles sur chaque journée, comme le nombre d'inscrits, le menu, la météo et le calendrier scolaire. Une estimation fiable peut aider à préparer le bon nombre de repas et à limiter le gaspillage ou les repas manquants.
## Résultats sur le jeu de test
Le modèle est entraîné sur 272 journées et évalué sur les 68 journées suivantes. Le découpage est chronologique afin de tester les modèles sur une période future plutôt que sur des journées mélangées aléatoirement.

| Modèle | MAE | RMSE | R² |
|---|---:|---:|---:|
| Baseline | 70.271 | 88.416 | -0.151 |
| Ridge (régression Ridge) | 22.623 | 28.545 | 0.880 |
| Gradient boosting | 29.852 | 37.727 | 0.790 |
| Forêt aléatoire | 31.825 | 41.647 | 0.745 |
| K plus proches voisins (KNN) | 36.212 | 46.037 | 0.688 |
| Arbre de décision | 42.010 | 54.766 | 0.558 |

La MAE représente l'écart absolu moyen entre les prédictions et le nombre réel de repas ; le RMSE pénalise davantage les grandes erreurs. Le R² indique dans quelle mesure le modèle explique les variations du nombre de repas : plus il est proche de 1, mieux c'est. Le score négatif de la baseline montre qu'elle fait moins bien qu'une prédiction fondée sur la moyenne des valeurs du jeu de test.
## Mon choix, et pourquoi
Je retiens Ridge, qui obtient la plus faible MAE (22.623 repas) et le meilleur R² (0.880). Son erreur absolue moyenne est inférieure de 47.648 repas à celle de la baseline (70.271), soit une réduction d'environ 67.8 %. Il fait également mieux que les autres modèles testés selon la MAE.
## Le critère (MAE la plus faible) est-il atteint ?
Oui, parmi les modèles comparés, Ridge a la MAE la plus faible : 22.623. Aucun seuil numérique d'acceptation n'est défini pour ce jeu de données ; on peut donc conclure qu'il est le meilleur des modèles testés, mais pas qu'il atteint une précision opérationnelle garantie.
## Ce qui reste flou
Il reste à vérifier si les données représentent bien les futures journées de cantine et si l'erreur moyenne d'environ 23 repas est acceptable pour l'organisation. Les résultats portent sur 68 journées de test ; ils peuvent varier selon la période, les menus ou les événements particuliers.
