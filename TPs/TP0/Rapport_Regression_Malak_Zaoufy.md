# TP0 : MaintAI

**Nom :** Prénom Nom · **Groupe :** G3  
**Date :** 28/10/2026

## Le problème

Prédire une panne à partir de 4 capteurs ; une panne manquée arrête une ligne.

## Résultats sur le jeu de test — classification

| Modèle | Accuracy | Rappel | Précision |
|---|---:|---:|---:|
| baseline | 0.824 | 0.000 | 0.000 |
| régression logistique | 0.889 | 0.574 | 0.737 |

## Mon choix, et pourquoi

Parmi les deux modèles présentés, je choisis provisoirement la régression logistique : elle détecte des pannes, contrairement à la baseline dont le rappel est nul, et ses scores d'accuracy (0.889) et de précision (0.737) sont meilleurs. Ce choix reste à confirmer, car son rappel n'atteint pas le seuil demandé.

## Le critère (rappel >= 0,75) est-il atteint ?

Non. Le rappel de la régression logistique est de 0.574, inférieur au seuil de 0.75. Environ 42,6 % des pannes du jeu de test ne sont donc pas détectées par ce modèle.

## Ce qui reste flou

- Le modèle ne satisfait pas le niveau de détection exigé ; son utilisation pour piloter la maintenance n'est donc pas justifiée en l'état.
- Le coût acceptable des fausses alertes et des pannes manquées, ainsi que l'origine et la représentativité des données, ne sont pas précisés.
- Les résultats ci-dessus ne donnent que la baseline et la régression logistique ; une comparaison avec d'autres modèles et une validation complémentaire seraient nécessaires.

## Résultats du terminal après le passage en régression — 28/10/2026

Après le changement de `TASK` en `regression`, la commande `python -m monprojet.train` a été exécutée. Cette exécution utilise la configuration actuellement présente dans le projet : `data/cantine_repas.csv`, cible `repas_servis`, découpage chronologique et métrique principale `mae`. Elle porte donc sur une tâche et des données différentes de la prédiction de pannes décrite plus haut.

```text
Entraînement du modèle : Dummy
Entraînement du modèle : Ridge
Entraînement du modèle : DecisionTree
Entraînement du modèle : RandomForest
Entraînement du modèle : KNeighbors

Comparaison des modèles :
                 mae    rmse     r2
Ridge         22.623  28.545  0.880
RandomForest  31.845  41.540  0.746
KNeighbors    36.212  46.037  0.688
DecisionTree  46.000  59.710  0.475
Dummy         70.271  88.416 -0.151

Métrique principale : mae
Meilleur modèle : Ridge
Score : 22.623
```

Le meilleur modèle selon la MAE est **Ridge**, avec une MAE de **22.623**. La baseline `Dummy` obtient une MAE de 70.271. Cette métrique mesure l'erreur absolue moyenne : plus elle est faible, mieux c'est. Le rappel et le seuil de 0.75 ne s'appliquent pas à cette exécution de régression.
