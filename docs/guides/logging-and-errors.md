# Journalisation et gestion des erreurs

Le projet utilise le module standard `logging` pour enregistrer les différentes
étapes de la résolution. Les exceptions personnalisées sont définies dans
`src/sele_saisie_auto/exceptions.py`.

Pour activer un niveau de log détaillé :

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

Les erreurs courantes sont `DriverError`, `TimeoutError` et `InvalidConfigError`.

## Niveaux de log disponibles

Le module `logging` gère les niveaux standards :

| Niveau    | Valeur numérique |
| --------- | ---------------- |
| DEBUG     | 10               |
| INFO      | 20               |
| WARNING   | 30               |
| ERROR     | 40               |
| CRITICAL  | 50               |

Le niveau recommandé par défaut est `INFO` afin d'obtenir des messages utiles
sans encombrer la sortie.

## Exemple de bloc `try/except`

```python
try:
    run_task()
except CustomError as exc:
    logger.error("operation failed: %s", exc)
```

## Fichier de log
## Exceptions personnalisées
| Exception                     | Raison de l'utilisation                                   |
| ----------------------------- | --------------------------------------------------------- |

