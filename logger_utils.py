import os
from datetime import datetime

# Constantes globales pour la configuration
DEFAULT_LOG_DIR = "logs"
HTML_FORMAT = "html"
TXT_FORMAT = "txt"
COLUMN_WIDTHS = {"timestamp": "10%", "level": "6%", "message": "84%"}
ROW_HEIGHT = "20px"
FONT_SIZE = "12px"
PADDING = "2px"
LOG_LEVELS = {"INFO": 10, "DEBUG": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
LOG_LEVEL_FILTER = "INFO"  # Niveau maxi des logs à écrire
DEBUG_MODE = False

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
        log_file = os.path.join(log_dir, f"log_{datetime.now().strftime('%Y-%m-%d')}.{extension}")
        return log_file
    except OSError as e:
        raise RuntimeError(f"Erreur liée au système de fichiers : {e}")
    except Exception as e:
        raise RuntimeError(f"Erreur inattendue lors de la création des logs : {e}")


def is_log_level_allowed(current_level, configured_level):
    """
    Vérifie si le niveau actuel est autorisé en fonction de la configuration.
    
    Args:
        current_level (str): Niveau du log actuel (ex: "INFO", "ERROR").
        configured_level (str): Niveau de log configuré (ex: "DEBUG").
    
    Returns:
        bool: True si le niveau est autorisé, False sinon.
    """
    return LOG_LEVELS[current_level] >= LOG_LEVELS[configured_level]


def should_rotate(log_file, max_size_mb=5):
    """
    Vérifie si un fichier de log doit être tourné (taille maximale atteinte).
    
    Args:
        log_file (str): Chemin du fichier de log.
        max_size_mb (int): Taille maximale en mégaoctets avant rotation.
    
    Returns:
        bool: True si le fichier doit être tourné, False sinon.
    """
    if os.path.exists(log_file):
        file_size = os.path.getsize(log_file) / (1024 * 1024)  # Taille en Mo
        return file_size >= max_size_mb
    return False


def rotate_log_file(log_file):
    """
    Tourne un fichier de log en renommant l'ancien fichier avec un suffixe unique.
    
    Args:
        log_file (str): Chemin du fichier de log à tourner.
    """
    if os.path.exists(log_file):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rotated_file = f"{log_file}.{timestamp}.bak"
        os.rename(log_file, rotated_file)


def get_html_style():
    """
    Retourne le style HTML/CSS utilisé pour les fichiers de log.
    
    Returns:
        str: Chaîne contenant les balises HTML nécessaires pour inclure le style CSS.
    """
    return f"""
    <html>
    <head>
        <style>
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            th, td {{
                border: 1px solid black;
                padding: {PADDING};
                text-align: left;
                height: {ROW_HEIGHT};
                font-size: {FONT_SIZE};
            }}
            th {{
                background-color: #f2f2f2;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            tr:hover {{
                background-color: #f1f1f1;
            }}
            /* Limiter la largeur des colonnes */
            th:nth-child(1), td:nth-child(1) {{
                width: {COLUMN_WIDTHS['timestamp']};
            }}
            th:nth-child(2), td:nth-child(2) {{
                width: {COLUMN_WIDTHS['level']};
            }}
            th:nth-child(3), td:nth-child(3) {{
                width: {COLUMN_WIDTHS['message']};
            }}
        </style>
    </head>
    <body>
    <table>
    <tr><th>Timestamp</th><th>Level</th><th>Message</th></tr>
    """


def initialize_html_log_file(log_file):
    """
    Initialise un fichier de log HTML avec le style requis.

    Args:
        log_file (str): Chemin du fichier de log.
    """
    with open(log_file, "w") as f:
        f.write(get_html_style())


def write_log(
    message,
    log_file,
    level="INFO",
    log_format=HTML_FORMAT,
    auto_close=False,
    max_size_mb=5
):
    try:
        # Vérifier si le niveau de log est valide
        if level not in LOG_LEVELS:
            if DEBUG_MODE:
                debug_print(f"Niveau non valide ignoré : {level}")  # Log pour niveau inconnu
            return

        # Appliquer le filtre de niveau (gère les niveaux supérieurs ou égaux à LOG_LEVEL_FILTER)
        if LOG_LEVELS[level] > LOG_LEVELS[LOG_LEVEL_FILTER]:
            if DEBUG_MODE:
                debug_print(f"Niveau ignoré par filtre : {level}")  # Log pour niveau filtré
            return

        # Securité supplementaire pour les logs: Si le mode DEBUG est désactivé, n'afficher que les logs INFO
        # if not DEBUG_MODE:
        #     if level != "INFO":
        #         # debug_print(f"Niveau ignoré - seul INFO est affiché : {level}")
        #         return

        # Si on passe ici, le niveau est autorisé
        if DEBUG_MODE:
            # Vérifiez l'encodage du message (débogage)
            log_message = f"<tr><td>{datetime.now()}</td><td>{level}</td><td>{message}</td></tr>\n"

        if DEBUG_MODE:
            debug_print(f"Écriture dans le fichier pour : {level}")

        # Rotation du fichier si nécessaire
        if should_rotate(log_file, max_size_mb):
            rotate_log_file(log_file)

        # Écriture dans le fichier
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if log_format.lower() == HTML_FORMAT:
            log_message = f"<tr><td>{timestamp}</td><td>{level}</td><td>{message}</td></tr>\n"
            
            # Initialisation du fichier HTML s'il n'existe pas
            if not os.path.exists(log_file):
                debug_print("Initialisation du fichier HTML")
                initialize_html_log_file(log_file)
            
            # Ajout du message
            with open(log_file, "a", encoding="utf-8") as f:
                if DEBUG_MODE:
                    debug_print(f"Ajout dans le fichier HTML : {message}")
                f.write(log_message)
                if auto_close:
                    f.write("</table>")

        else:  # Format texte brut
            log_message = f"[{timestamp}] {level}: {message}\n"
            with open(log_file, "a", encoding="utf-8") as f:
                if DEBUG_MODE:
                    debug_print(f"Ajout dans le fichier TXT : {message}")
                f.write(log_message)

    except OSError as e:
        raise RuntimeError(f"Erreur liée au système de fichiers : {e}")
    except Exception as e:
        raise RuntimeError(f"Erreur inattendue lors de l'écriture des logs : {e}")


def debug_print(message):
    """Affiche un message de débogage uniquement si DEBUG_MODE est activé."""
    if DEBUG_MODE:
        print(message)


def close_logs(log_file, log_format=HTML_FORMAT):
    """
    Ajoute une fermeture propre du tableau HTML si nécessaire.
    
    Args:
        log_file (str): Chemin complet du fichier de log.
        log_format (str): Format du fichier de log ("html" ou "txt").
    """
    try:
        if log_format.lower() == HTML_FORMAT and os.path.exists(log_file):
            with open(log_file, "a") as f:
                f.write("</table>")
    except OSError as e:
        raise RuntimeError(f"Erreur liée au système de fichiers : {e}")
    except Exception as e:
        raise RuntimeError(f"Erreur inattendue lors de la fermeture des logs : {e}")
