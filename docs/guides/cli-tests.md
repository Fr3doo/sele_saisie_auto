# Tests du CLI

Les tests CLI couvrent l'exécutable `NOM_DU_PROJET`. Ils s'assurent que la
commande renvoie la même solution que l'API Python, indique quand le cube est
déjà résolu et gère les entrées invalides. Tous les scénarios sont regroupés
dans `tests/test_cli.py`.

## Lancer les tests

```bash
poetry run pytest tests/test_cli.py
```

## Filtrer avec `pytest -k`

Pour exécuter un seul test ou un sous-ensemble, utilise l'option `-k` :

```bash
poetry run pytest -k invalid_cube tests/test_cli.py
```

## Exemple de sortie

```text
$ poetry run pytest -k cli -q
....                                                    [100%]
4 passed in 0.35s
```

## Dépannage

 - **Module introuvable** : exécute `poetry install` pour installer les dépendances nécessaires.
- **Couverture insuffisante** : vérifie que tous les tests passent afin
  d'atteindre le seuil défini dans la configuration.
