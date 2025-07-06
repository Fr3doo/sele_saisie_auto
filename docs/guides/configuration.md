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
| HTML_FORMAT       | Extension utilisée pour les journaux HTML                 | html              |
| TXT_FORMAT        | Extension utilisée pour les journaux texte                | txt               |

Modifiez ces valeurs dans `config.ini` ou via des variables d’environnement si besoin.

## Variables d'environnement prises en charge

Les paramètres du fichier peuvent être surchargés avec :

- `PSATIME_URL` — URL du portail PSA Time
- `PSATIME_DATE_CIBLE` — date cible au format `JJ/MM/AAAA`
- `PSATIME_LOGIN` — identifiant chiffré
- `PSATIME_MDP` — mot de passe chiffré
- `PSATIME_DEBUG_MODE` — niveau de log (`INFO`, `DEBUG`, …)
- `PSATIME_LISTE_ITEMS_PLANNING` — liste d'items séparés par des virgules
- `PSATIME_DEFAULT_TIMEOUT` — délai d'attente par défaut pour Selenium
- `PSATIME_LONG_TIMEOUT` — délai prolongé pour certaines opérations

## 3. Exemple de fichier `.env`

```dotenv
PSATIME_URL=https://psa.example.com
PSATIME_LOGIN=encrypted_login
PSATIME_MDP=encrypted_password
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

- Activez la rotation des journaux avec `logger_utils.write_log`. Limitez la
  taille du fichier grâce à l'option `max_size_mb` pour éviter un stockage
  excessif.
- Sauvegardez le fichier `config.ini` après chaque modification et conservez une
  copie sécurisée sur un serveur interne.
- Chaque paramètre peut être surchargé par une variable d'environnement. La
  valeur de cette dernière prime sur celles de `.env` et de `config.ini`.

