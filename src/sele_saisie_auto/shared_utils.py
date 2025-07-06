# shared_utils.py
import os
from datetime import datetime

# Constantes globales pour la configuration
"""Les modules externes n'accèdent pas directement à _log_file.
Ils passent par get_log_file(), qui garantit une gestion contrôlée du fichier de log.
Variable privée pour éviter des modifications externes"""
_log_file = None

DEFAULT_LOG_DIR = "logs"
HTML_FORMAT = "html"
TXT_FORMAT = "txt"


def setup_logs(log_dir=DEFAULT_LOG_DIR, log_format=HTML_FORMAT):
    """
    Prépare un fichier de log journalier.

    Args:
        log_dir (str): Nom du répertoire où seront stockés les logs.
        log_format (str): Format du fichier de log ("html" ou "txt").

    Returns:
        str: Chemin complet du fichier de log.
    """
    try:
        os.makedirs(log_dir, exist_ok=True)
        extension = HTML_FORMAT if log_format.lower() == HTML_FORMAT else TXT_FORMAT
        log_file = os.path.join(
            log_dir, f"log_{datetime.now().strftime('%Y-%m-%d')}.{extension}"
        )
        return log_file
    except OSError as e:
        raise RuntimeError(f"Erreur liée au système de fichiers : {e}")
    except Exception as e:
        raise RuntimeError(f"Erreur inattendue lors de la création des logs : {e}")


def get_log_file():
    """Retourne le fichier de log utilisé dans l'application, en l'initialisant si nécessaire.

    Cette fonction est utilisée pour centraliser la gestion du fichier de log dans le programme.
    Elle garantit qu'un unique fichier de log est créé et partagé entre les différents modules
    et processus de l'application.

    Si le fichier de log (_log_file) n'est pas encore initialisé, cette fonction appelle
    `setup_logs()` pour le créer et l'initialiser avant de le retourner. Dans le cas contraire,
    elle retourne simplement la référence existante du fichier de log.

    Utilisation :
    - Permet de s'assurer que tous les modules accèdent au même fichier de log sans le réinitialiser.
    - Évite les problèmes de redondance ou de création multiple de fichiers de log.

    Returns:
        str: Le chemin du fichier de log initialisé.
    """
    global _log_file
    if _log_file is None:
        _log_file = setup_logs()  # Initialise le fichier de log
    return _log_file
