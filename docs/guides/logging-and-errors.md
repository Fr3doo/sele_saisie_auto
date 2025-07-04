# Journalisation et gestion des erreurs

Le projet utilise le module standard `logging` pour enregistrer les différentes
étapes de la résolution. Les exceptions personnalisées sont définies dans
`exceptions.py`.

```mermaid
graph TD
    A[Utilisateur] --> B(Application)
    B --> C[Logger]
    C --> D[Fichier de log]
    B --> E[Message utilisateur]
```

Pour activer un niveau de log détaillé :

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

Pour enregistrer les messages dans un fichier dédié :

```python
logging.basicConfig(filename="app.log")
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
| `TimeoutError` | Temps d'attente dépassé lors d'une action Selenium |
| `WebDriverException` | Erreur générique du moteur Selenium |
| `FileNotFoundError` | Fichier de configuration ou de log introuvable |
| `PermissionError` | Droits insuffisants pour accéder au fichier |
| `UnicodeDecodeError` | Caractères invalides lors de la lecture d'un fichier |
| `RuntimeError` | État inattendu de l'application |
| `NameError` | Objet ou identifiant manquant dans le code |

## Exemple de sortie de log

```
2024-06-01 14:32:11 [INFO] Ouverture du navigateur
2024-06-01 14:32:15 [ERROR] Timeout lors du remplissage du champ
```

Pour plus d'informations sur la configuration ou l'utilisation avancée,
consultez également [configuration](configuration.md) et
[advanced-usage-example](advanced-usage-example.md).

