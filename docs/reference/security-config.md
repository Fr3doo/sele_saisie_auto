# Configuration de sécurité

Les paramètres de sécurité sont définis dans `src/sele_saisie_auto/`.

| Constante              | Valeur par défaut | Rôle |
| ---------------------- | ----------------- | --------------------------------------------- |
| DEFAULT_TIMEOUT        | 10                | Délai d'attente de base pour les opérations Selenium |
| LONG_TIMEOUT           | 20                | Délai étendu utilisé pour certaines attentes |
| DEFAULT_LOG_LEVEL      | INFO              | Niveau de journalisation par défaut |
| DEFAULT_LOG_DIR        | logs              | Répertoire où sont placés les fichiers de logs |
| HTML_FORMAT            | html              | Extension utilisée pour les journaux HTML |
| TXT_FORMAT             | txt               | Extension utilisée pour les journaux texte |
| DEBUG_MODE             | False             | Active l'affichage détaillé dans les logs |

Ces valeurs peuvent être remplacées via un fichier `.env` ou des variables d’environnement avant le démarrage de l’application. Pour plus de détails, consultez le guide [configuration.md](../guides/configuration.md).
Exemple de fichier `.env` pour surcharger une valeur:

```dotenv
DEFAULT_TIMEOUT=30
DEFAULT_LOG_LEVEL=DEBUG
```
