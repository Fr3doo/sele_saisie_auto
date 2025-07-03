# Tests du CLI

La ligne de commande constitue la principale porte d'entrée du projet pour les
utilisateurs. Il est donc primordial de valider son fonctionnement à chaque
évolution. Une suite de tests dédiée permet de vérifier que les commandes
disponibles produisent les messages attendus et protègent contre les
régressions.

Les tests CLI couvrent l'exécutable `sele_saisie_auto`. Ils s'assurent que la
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
- [Guide complet des tests](../../TESTING.md)
