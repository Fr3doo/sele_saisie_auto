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

## Récupérer le résultat des hooks

`sele_saisie_auto` expose un petit système de plugins. Toutes les fonctions
enregistrées pour un hook sont exécutées via `plugins.call` et leurs retours sont
désormais collectés dans une liste :

```python
from sele_saisie_auto import plugins

@plugins.hook("after_run")
def plus_un(val):
    return val + 1

@plugins.hook("after_run")
def fois_deux(val):
    return val * 2

resultats = plugins.call("after_run", 3)
print(resultats)  # [4, 6]
```

Cette fonctionnalité permet de récupérer facilement les valeurs produites par
chaque plugin.

## Extensions via hooks

Le projet fournit un petit système de hooks pour étendre l'automatisation.
Le module `plugins` expose les fonctions `register`, `unregister`, `hook` et
`call`.
Créez simplement un fichier Python contenant des fonctions décorées avec
`@hook` :

```python
# my_plugin.py
from sele_saisie_auto.plugins import hook

@hook("before_submit")
def notifier(driver):
    print("Avant validation")
```

Importez ce module avant d'appeler `plugins.call` afin de l'enregistrer :

```python
import my_plugin
```

Un exemple complet se trouve dans `examples/example_plugin.py`.

## Orchestration avec `ResourceManager`

L'architecture expose un orchestrateur de haut niveau. On peut l'appeler
manuellement à partir d'un `ResourceManager` déjà initialisé :

```python
from sele_saisie_auto.config_manager import ConfigManager
from sele_saisie_auto.configuration import ServiceConfigurator
from sele_saisie_auto.orchestration import AutomationOrchestrator
from sele_saisie_auto.saisie_automatiser_psatime import PSATimeAutomation

log_file = "log.html"
config = ConfigManager(log_file).load()

automation = PSATimeAutomation(log_file, config)

with automation.resource_manager as manager:
    orchestrator = AutomationOrchestrator.from_components(
        manager,
        automation.page_navigator,
        ServiceConfigurator(config),
        automation.context,
        automation.logger,
    )
    orchestrator.run(headless=True, no_sandbox=True)
```
