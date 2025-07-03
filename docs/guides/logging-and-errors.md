# Journalisation et gestion des erreurs

Le projet utilise le module standard `logging` pour enregistrer les différentes
étapes de la résolution. Les exceptions personnalisées sont définies dans
`exceptions.py`.

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
| NOTSET    | 0                |
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
except (DriverError, InvalidConfigError) as exc:
    logger.error("operation failed: %s", exc)
```

## Fichier de log
Les messages sont enregistres dans le dossier `logs/` sous forme de fichier HTML. Chaque execution ajoute de nouvelles entrees au meme fichier afin de conserver l'historique complet.
## Exceptions personnalisées
| Exception | Raison de l'utilisation |
| ------------------ | ---------------------------------------------------- |
| `DriverError` | Échec lors de l'initialisation du WebDriver |
| `InvalidConfigError` | Paramètres manquants ou incohérents dans `config.ini` |
