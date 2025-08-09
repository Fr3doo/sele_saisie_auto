from __future__ import annotations

import os
from configparser import ConfigParser
from datetime import datetime
from typing import Callable, Literal, Mapping, Optional

from sele_saisie_auto import messages
from sele_saisie_auto.enums import LogLevel
from sele_saisie_auto.exceptions import InvalidConfigError

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
LOG_ENTRY_FORMAT: str = "{timestamp} [{level}] {message}"
LOG_STYLE_ALLOWED_KEYS: set[str] = {"column_widths", "row_height", "font_size"}
LOG_LEVELS: dict[LogLevel, int] = {
    LogLevel.INFO: 10,
    LogLevel.DEBUG: 20,
    LogLevel.WARNING: 30,
    LogLevel.ERROR: 40,
    LogLevel.CRITICAL: 50,
    LogLevel.OFF: 0,
}
LOG_LEVEL_CHOICES: list[str] = [lvl.value for lvl in LogLevel]

# Par défaut, on commence avec un niveau de log minimal (par ex., "INFO")
DEFAULT_LOG_LEVEL: LogLevel = LogLevel.INFO
LOG_LEVEL_FILTER: LogLevel = DEFAULT_LOG_LEVEL

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

# ----------------------------------------------------------------------------- #
# ---------------------------------- HELPERS ---------------------------------- #
# ----------------------------------------------------------------------------- #


def _to_level(level: LogLevel | str) -> Optional[LogLevel]:
    try:
        return level if isinstance(level, LogLevel) else LogLevel(level)
    except ValueError:
        return None


def _level_allowed(lvl: LogLevel) -> bool:
    return LOG_LEVELS[lvl] <= LOG_LEVELS[LOG_LEVEL_FILTER]


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _append(path: str, text: str) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)


def _write_txt_line(path: str, ts: str, lvl: LogLevel, msg: str) -> None:
    formatted = LOG_ENTRY_FORMAT.format(timestamp=ts, level=lvl.value, message=msg)
    _append(path, formatted + "\n")


def _ensure_html_open(path: str) -> None:
    initialize_html_log_file(path)


def _write_html_row(path: str, ts: str, lvl: LogLevel, msg: str) -> None:
    _ensure_html_open(path)
    row = f"<tr><td>{ts}</td><td>{lvl.value}</td><td>{msg}</td></tr>\n"
    _append(path, row)


_WRITERS: Mapping[str, Callable[[str, str, LogLevel, str], None]] = {
    HTML_FORMAT: _write_html_row,
    TXT_FORMAT: _write_txt_line,
}

# ------------------------------------------------------------------------------------------- #
# ----------------------------------- FONCTIONS --------------------------------------------- #
# ------------------------------------------------------------------------------------------- #


def initialize_logger(
    config: ConfigParser,
    log_level_override: LogLevel | str | None = None,
    log_file: str | None = None,
) -> None:
    """Initialise le niveau de log avec priorité à l'override."""

    global LOG_LEVEL_FILTER
    level, warning = _resolve_level(config, log_level_override)
    LOG_LEVEL_FILTER = level

    if log_file is None:
        return
    if warning:
        write_log(warning, log_file, LogLevel.WARNING)
    write_log(
        f"Niveau de log initialisé sur {LOG_LEVEL_FILTER.name}",
        log_file,
        LogLevel.DEBUG,
    )


def _parse_level_or_none(value: LogLevel | str | None) -> Optional[LogLevel]:
    if value is None:
        return None
    return _to_level(value)


def _level_from_config(cfg: ConfigParser) -> Optional[LogLevel]:
    raw = cfg.get("settings", "debug_mode", fallback=LogLevel.INFO.value)
    return _to_level(raw)


def _resolve_level(
    config: ConfigParser, override: LogLevel | str | None
) -> tuple[LogLevel, str | None]:
    level = _parse_level_or_none(override)
    warning: str | None = None
    if level is None:
        if override is not None:
            warning = f"Invalid log level '{override}', fallback to INFO"
        level = _level_from_config(config)
        if level is None:
            raw = config.get("settings", "debug_mode", fallback=LogLevel.INFO.value)
            warning = f"Invalid log level '{raw}' in config, fallback to INFO"
            level = LogLevel.INFO
    return level, warning


def is_log_level_allowed(
    current_level: LogLevel | str, configured_level: LogLevel | str
) -> bool:
    """
    Vérifie si le niveau actuel est autorisé en fonction de la configuration.

    Args:
        current_level (str): Niveau du log actuel (ex: "INFO", "ERROR").
        configured_level (str): Niveau de log configuré (ex: "DEBUG").

    Returns:
        bool: True si le niveau est autorisé, False sinon.
    """
    try:
        cur = (
            current_level
            if isinstance(current_level, LogLevel)
            else LogLevel(current_level)
        )
        conf = (
            configured_level
            if isinstance(configured_level, LogLevel)
            else LogLevel(configured_level)
        )
    except ValueError:
        return False
    return LOG_LEVELS[cur] >= LOG_LEVELS[conf]


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


def _validate_section_keys(section: Mapping[str, str]) -> None:
    unknown = [k for k in section.keys() if k not in LOG_STYLE_ALLOWED_KEYS]
    if unknown:
        raise InvalidConfigError(f"Clé inconnue dans [log_style]: {', '.join(unknown)}")


def _validate_column_widths(raw: str) -> None:
    for item in raw.split(","):
        item = item.strip()
        if item and ":" not in item:
            raise InvalidConfigError(
                "column_widths doit utiliser le format 'nom:valeur'"
            )


def validate_log_style(parser: ConfigParser) -> None:
    if not parser.has_section("log_style"):
        return
    section = parser["log_style"]
    _validate_section_keys(section)
    _validate_column_widths(section.get("column_widths", ""))


def _load_style_overrides() -> tuple[dict[str, str], str, str]:
    column_widths = COLUMN_WIDTHS.copy()
    row_height = ROW_HEIGHT
    font_size = FONT_SIZE

    config_file = os.path.join(os.getcwd(), "config.ini")
    if not os.path.exists(config_file):
        return column_widths, row_height, font_size

    parser = ConfigParser(interpolation=None)
    try:
        with open(config_file, encoding="utf-8") as cfg:
            parser.read_file(cfg)
    except Exception as e:  # noqa: BLE001
        print(f"Erreur lors de la lecture du style de log : {e}")
        return column_widths, row_height, font_size

    validate_log_style(parser)
    if parser.has_section("log_style"):
        raw_widths = parser.get("log_style", "column_widths", fallback="")
        if raw_widths:
            column_widths.update(_parse_column_widths(raw_widths))
        row_height = parser.get("log_style", "row_height", fallback=row_height)
        font_size = parser.get("log_style", "font_size", fallback=font_size)

    return column_widths, row_height, font_size


def get_html_style() -> str:
    column_widths, row_height, font_size = _load_style_overrides()
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
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            tr:hover {{ background-color: #f1f1f1; }}
            th:nth-child(1), td:nth-child(1) {{ width: {column_widths['timestamp']}; }}
            th:nth-child(2), td:nth-child(2) {{ width: {column_widths['level']}; }}
            th:nth-child(3), td:nth-child(3) {{ width: {column_widths['message']}; }}
        </style>
    </head>
    <body>
    <table>
    <tr><th>Timestamp</th><th>Level</th><th>Message</th></tr>
    """


def afficher_message_insertion(
    jour: str,
    valeur: str,
    tentative: int,
    message: str,
    log_file: str,
) -> None:
    """Log un message de confirmation d'insertion."""

    if message == messages.TENTATIVE_INSERTION:
        write_log(
            f"⚠️ Valeur '{valeur}' confirmée pour le jour '{jour}' ({message}{tentative + 1})",
            log_file,
            "DEBUG",
        )
    else:
        write_log(
            f"⚠️ Valeur '{valeur}' confirmée pour le jour '{jour}' {message})",
            log_file,
            "DEBUG",
        )


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
    level: LogLevel | str = LogLevel.INFO,
    log_format: Literal["html", "txt"] = HTML_FORMAT,
    auto_close: bool = False,
) -> None:
    """Écrit un message dans le fichier de log."""
    try:
        _write_log_entry(message, log_file, level, log_format, auto_close)
    except OSError as e:
        raise RuntimeError(f"Erreur liée au système de fichiers : {e}") from e
    except Exception as e:
        raise RuntimeError(
            f"Erreur inattendue lors de l'écriture des logs : {e}"
        ) from e


def _write_log_entry(
    message: str,
    log_file: str,
    level: LogLevel | str,
    log_format: Literal["html", "txt"],
    auto_close: bool,
) -> None:
    lvl = _to_level(level)
    if lvl is None or not _level_allowed(lvl):
        return

    ts = _timestamp()
    fmt = log_format.lower()
    writer = _WRITERS.get(fmt, _write_txt_line)

    writer(log_file, ts, lvl, message)

    if auto_close and fmt == HTML_FORMAT:
        _append(log_file, "</table></body></html>")


def close_logs(
    log_file: str,
    log_format: Literal["html", "txt"] = HTML_FORMAT,
) -> None:
    """Ajoute la fermeture du tableau HTML si nécessaire."""
    try:
        if log_format.lower() != HTML_FORMAT:
            return
        if not os.path.exists(log_file):
            return
        with open(log_file, "r+", encoding="utf-8") as f:
            content = f.read()
            if "</table>" not in content:
                f.write("</table></body></html>")
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Erreur lors de la fermeture des logs : {e}") from e


def show_log_separator(log_file: str, level: LogLevel | str = LogLevel.INFO) -> None:
    """Write a visual separator to ``log_file``."""

    write_log(
        "*************************************************************",
        log_file,
        level,
    )
