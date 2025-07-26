import os
from __future__ import annotations

from configparser import ConfigParser
from datetime import datetime
from typing import Literal

# ----------------------------------------------------------------------------- #
# ------------------------------- CONSTANTE ----------------------------------- #
# ----------------------------------------------------------------------------- #
DEFAULT_LOG_DIR: str = "logs"
HTML_FORMAT: Literal["html"] = "html"
TXT_FORMAT: Literal["txt"] = "txt"
COLUMN_WIDTHS: dict[str, str] = {"timestamp": "10%", "level": "6%", "message": "84%"}
ROW_HEIGHT: str = "20px"
FONT_SIZE: str = "12px"
PADDING: str = "2px"
LOG_LEVELS: dict[str, int] = {
    "INFO": 10,
    "DEBUG": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
    "OFF": 0,
}

# Par défaut, on commence avec un niveau de log minimal (par ex., "INFO")
DEFAULT_LOG_LEVEL: str = "INFO"
LOG_LEVEL_FILTER: str = DEFAULT_LOG_LEVEL

# Mapping between short codes and user-facing log messages.
MESSAGE_TEMPLATES: dict[str, str] = {
    "BROWSER_OPEN": "Ouverture du navigateur",
    "BROWSER_CLOSE": "Fermeture du navigateur",
    "DECRYPT_CREDENTIALS": "Déchiffrement des identifiants",
    "SEND_CREDENTIALS": "Envoi des identifiants",
    "ADDITIONAL_INFO_DONE": "Validation des informations supplémentaires terminée.",
    "SAVE_ALERT_WARNING": "⚠️ Alerte rencontrée lors de la sauvegarde.",
    "DOM_STABLE": "Le DOM est stable.",
    "NO_DATE_CHANGE": "Aucune modification de la date nécessaire.",
    "TIME_SHEET_EXISTS_ERROR": "ERREUR : Vous avez déjà créé une feuille de temps pour cette période. (10502,125)",
    "MODIFY_DATE_MESSAGE": "--> Modifier la date du PSATime dans le fichier ini. Le programme va s'arrêter.",
    "DATE_VALIDATED": "Date validée avec succès.",
}

# ------------------------------------------------------------------------------------------- #
# ----------------------------------- FONCTIONS --------------------------------------------- #
# ------------------------------------------------------------------------------------------- #


def initialize_logger(
    config: ConfigParser, 
    log_level_override: str | None = None
) -> None:
    """Initialise le niveau de log.

    La priorité est donnée au niveau fourni en argument. Si aucun
    ``log_level_override`` n'est passé, la valeur provient de la configuration.

    Args:
        config: Objet ``ConfigParser`` contenant les paramètres.
        log_level_override: Niveau de log à appliquer en priorité.
    """

    global LOG_LEVEL_FILTER
    if log_level_override:
        LOG_LEVEL_FILTER = log_level_override
    else:
        LOG_LEVEL_FILTER = config.get("settings", "debug_mode", fallback="INFO")


def is_log_level_allowed(current_level: str, configured_level: str) -> bool:
    """
    Vérifie si le niveau actuel est autorisé en fonction de la configuration.

    Args:
        current_level (str): Niveau du log actuel (ex: "INFO", "ERROR").
        configured_level (str): Niveau de log configuré (ex: "DEBUG").

    Returns:
        bool: True si le niveau est autorisé, False sinon.
    """
    return LOG_LEVELS[current_level] >= LOG_LEVELS[configured_level]


def format_message(code: str, details: dict[str, str] | None = None) -> str:
    """Return the message associated with ``code`` formatted with ``details``."""

    template = MESSAGE_TEMPLATES.get(code)
    if template is None:
        raise KeyError(f"Unknown message code: {code}")
    if details is None:
        details = {}
    return template.format(**details)


def _parse_column_widths(value: str) -> dict[str, str]:
    """Convert ``value`` into a mapping of column widths."""
    widths: dict[str, str] = {}
    for item in value.split(","):
        if ":" in item:
            key, _, val = item.partition(":")
            key = key.strip()
            val = val.strip()
            if key and val:
                widths[key] = val
    return widths


def get_html_style() -> str:
    """
    Retourne le style HTML/CSS utilisé pour les fichiers de log.

    Returns:
        str: Chaîne contenant les balises HTML nécessaires pour inclure le style CSS.
    """
    column_widths = COLUMN_WIDTHS.copy()
    row_height = ROW_HEIGHT
    font_size = FONT_SIZE

    config_file = os.path.join(os.getcwd(), "config.ini")
    if os.path.exists(config_file):
        parser = ConfigParser(interpolation=None)
        try:
            with open(config_file, encoding="utf-8") as cfg:
                parser.read_file(cfg)
            if parser.has_section("log_style"):
                raw_widths = parser.get("log_style", "column_widths", fallback="")
                if raw_widths:
                    column_widths.update(_parse_column_widths(raw_widths))
                row_height = parser.get("log_style", "row_height", fallback=row_height)
                font_size = parser.get("log_style", "font_size", fallback=font_size)
        except Exception as e:  # noqa: BLE001
            print(f"Erreur lors de la lecture du style de log : {e}")

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
                height: {row_height};
                font-size: {font_size};
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
                width: {column_widths['timestamp']};
            }}
            th:nth-child(2), td:nth-child(2) {{
                width: {column_widths['level']};
            }}
            th:nth-child(3), td:nth-child(3) {{
                width: {column_widths['message']};
            }}
        </style>
    </head>
    <body>
    <table>
    <tr><th>Timestamp</th><th>Level</th><th>Message</th></tr>
    """


def initialize_html_log_file(log_file: str) -> None:
    """
    Initialise un fichier de log HTML avec le style requis si le fichier n'existe pas.
    Si le fichier existe déjà, vérifie si une table est ouverte.
    """
    if not os.path.exists(log_file):
        # Crée un nouveau fichier HTML avec la structure complète
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(get_html_style())
    else:
        # Vérifie si la balise </table> est présente
        with open(log_file, encoding="utf-8") as f:
            content = f.read()
        if "</table>" in content:
            # Supprime les balises fermantes pour continuer l'écriture
            content = content.replace("</table></body></html>", "")
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(content)


def write_log(
    message: str,
    log_file: str,
    level: str = "INFO",
    log_format: Literal["html", "txt"] = HTML_FORMAT,
    auto_close: bool = False,
) -> None:
    """Écrit un message dans le fichier de log."""
    try:
        # Vérifier si le niveau de log est valide
        if level not in LOG_LEVELS:
            return

        # Appliquer le filtre de niveau (gère les niveaux supérieurs ou égaux à LOG_LEVEL_FILTER)
        if LOG_LEVELS[level] > LOG_LEVELS[LOG_LEVEL_FILTER]:
            return

        # Securité supplementaire pour les logs: Si le mode DEBUG est désactivé, n'afficher que les logs INFO
        # Écriture dans le fichier
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if log_format.lower() == HTML_FORMAT:
            log_message = (
                f"<tr><td>{timestamp}</td><td>{level}</td><td>{message}</td></tr>\n"
            )

            initialize_html_log_file(log_file)

            # Ajout du message
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_message)
            # Ajouter fermeture propre si auto_close est activé
            if auto_close:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write("</table></body></html>")
        else:  # Format texte brut
            log_message = f"[{timestamp}] {level}: {message}\n"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_message)

    except OSError as e:
        raise RuntimeError(f"Erreur liée au système de fichiers : {e}") from e
    except Exception as e:
        raise RuntimeError(
            f"Erreur inattendue lors de l'écriture des logs : {e}"
        ) from e


def close_logs(
    log_file: str,
    log_format: Literal["html", "txt"] = HTML_FORMAT,
) -> None:
    """
    Ajoute une fermeture propre du tableau HTML si nécessaire.

    Args:
        log_file (str): Chemin complet du fichier de log.
        log_format (str): Format du fichier de log ("html" ou "txt").
    """
    try:
        if log_format.lower() == HTML_FORMAT and os.path.exists(log_file):
            with open(log_file, "r+", encoding="utf-8") as f:
                content = f.read()
                if "</table>" not in content:
                    f.write("</table></body></html>")
    except OSError as e:
        raise RuntimeError(f"Erreur liée au système de fichiers : {e}") from e
    except Exception as e:
        raise RuntimeError(
            f"Erreur inattendue lors de la fermeture des logs : {e}"
        ) from e
