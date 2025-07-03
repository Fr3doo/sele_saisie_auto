# Guide de configuration

Ce guide explique comment ajuster les limites d’exécution et les options de traitement.

## 1. Limites de sécurité

Les paramètres de sécurité sont définis dans `src/`.



## 2. Constantes d’application

| Constante         | Description                                                | Valeur par défaut |
| ----------------- | ---------------------------------------------------------- | ----------------- |
| DEFAULT_TIMEOUT   | Délai d'attente par défaut pour les appels Selenium       | 10                |
| LONG_TIMEOUT      | Délai prolongé utilisé lors de certaines opérations       | 20                |
| DEFAULT_LOG_LEVEL | Niveau de journalisation appliqué par défaut              | INFO              |
| DEFAULT_LOG_DIR   | Dossier où sont générés les fichiers de logs              | logs              |

Modifiez ces valeurs dans `config.ini` ou via des variables d’environnement si besoin.

## 3. Exemple de fichier `.env`

```dotenv
PSATIME_URL=https://psa.example.com
PSATIME_LOGIN=encrypted_login
PSATIME_MDP=encrypted_password
PSATIME_DEBUG_MODE=INFO
PSATIME_LISTE_ITEMS_PLANNING="En mission,Formation"
```

```python
manager = ConfigManager()
cfg = manager.config
debug_mode = cfg.get("settings", "debug_mode", fallback="INFO")

Les valeurs définies dans le fichier `.env` sont chargées au démarrage. Si une
variable d'environnement du système porte le même nom, cette dernière prime sur
le contenu du fichier `.env`. Le fichier de configuration `config.ini` est
utilisé en dernier recours.
```

## 4. Conseils pour la production


