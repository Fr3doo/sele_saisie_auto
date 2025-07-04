# Exemple d'utilisation avancée

Ce guide montre comment injecter des composants personnalisés dans `sele_saisie_auto` tout en activant la journalisation détaillée et en récupérant les métriques. Le code ci-dessous définit deux classes utilitaires pour étendre un element de l'application.



## Code source

```python
import logging
import time


def default_solver(cube):
    """Retourne une liste de mouvements factices."""
    return ["U"]


class VerboseAlgorithm:
    def solve(self, cube):
        logging.debug("debut")
        start = time.perf_counter()
        moves = default_solver(cube)
        duration = time.perf_counter() - start
        logging.debug("mouvements %s", moves)
        return moves, duration


class MetricValidator:
    def validate(self, moves):
        return len(moves)


algo = VerboseAlgorithm()
validator = MetricValidator()
moves, elapsed = algo.solve("cube")
print(f"duree {elapsed:.2f}s, taille {validator.validate(moves)}")
```

## Exécuter l'exemple

1. Enregistrez le code ci-dessus dans un fichier `advanced_usage_example.py`.
2. Lancez-le avec `python advanced_usage_example.py`.
3. Le programme affiche la solution renvoyée par `VerboseAlgorithm` et indique la durée d'exécution ainsi que le nombre de mouvements produits.

Avec le niveau de débogage activé, vous verrez aussi les messages de log signalant l'appel de l'algorithme et du validateur. La sortie finale ressemble à :

```text
DEBUG:root:debut
DEBUG:root:mouvements ['U']
duree 0.00s, taille 1
```
