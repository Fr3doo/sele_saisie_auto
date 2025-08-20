# read_or_write_file_config_ini_utils.py
from __future__ import annotations

import configparser
import os
import shutil
import sys
import threading
from pathlib import Path
from tkinter import messagebox
from typing import Protocol, runtime_checkable

from sele_saisie_auto import messages
from sele_saisie_auto.logger_utils import write_log
from sele_saisie_auto.logging_service import log_info
from sele_saisie_auto.shared_utils import get_log_file

# Cache des configurations lues, indexé par chemin du fichier
_CACHE: dict[str, tuple[float, configparser.ConfigParser]] = {}
_CACHE_LOCK = threading.RLock()


def clear_cache() -> None:
    """Vide le cache de configuration."""
    with _CACHE_LOCK:
        _CACHE.clear()


# ---------------------------- Helpers internes -----------------------------


def _is_frozen() -> bool:
    """Retourne True si l'application tourne via PyInstaller."""
    return hasattr(sys, "_MEIPASS")


def _copy_if_missing(src: str, dst: str, lf: str) -> None:
    """Copie src -> dst uniquement si dst n'existe pas. Journalise et lève des erreurs explicites."""
    if os.path.exists(dst):
        return
    try:
        shutil.copy(src, dst)
        log_info(f"🔹 Copie de {src} vers {dst}", lf)
    except FileNotFoundError as e:
        write_log(
            f"🔴 Fichier embarqué {messages.INTROUVABLE} : {src}",
            lf,
            "ERROR",
        )
        raise FileNotFoundError(
            f"{messages.IMPOSSIBLE_DE_TROUVER} le fichier embarqué : {src}"
        ) from e
    except PermissionError as e:
        write_log(
            f"🔴 Permission refusée pour copier {src} vers {dst}",
            lf,
            "ERROR",
        )
        raise PermissionError(f"Permission refusée pour copier : {src}") from e


def _resource_base_dir() -> Path:
    """Répertoire de base pour les ressources. Surchargable via SAA_RES_DIR."""
    override = os.getenv("SAA_RES_DIR")
    return Path(override) if override else Path.cwd()


def _ensure_runtime_resource(relative_path: str, lf: str) -> str:
    """
    Retourne le chemin courant d'une ressource (copie la version PyInstaller si nécessaire).
    Utilisé à la fois pour config.ini et pour toute ressource embarquée.
    """
    dst = _resource_base_dir() / relative_path
    log_info(f"🔹 Chemin du fichier courant : {dst}", lf)

    if _is_frozen():
        src = Path(getattr(sys, "_MEIPASS")) / relative_path
        log_info(f"🔹 Exécution via PyInstaller. Fichier embarqué : {src}", lf)
        _copy_if_missing(str(src), str(dst), lf)
    else:
        log_info("🔹 Exécution en mode script.", lf)

    return str(dst)


def _ensure_exists(path: str, lf: str, label: str) -> None:
    """Vérifie l'existence d'un fichier, logge, et lève FileNotFoundError si absent."""
    if os.path.exists(path):
        log_info(f"🔹 Le fichier '{path}' a été trouvé.", lf)
        return
    log_info(f"🔹 Le fichier '{path}' est {messages.INTROUVABLE}.", lf)
    raise FileNotFoundError(f"Le fichier {label} '{path}' est {messages.INTROUVABLE}.")


def _read_ini_file(path: str, lf: str) -> configparser.ConfigParser:
    """Lit un INI en UTF-8 et retourne un ConfigParser avec gestion d'erreurs normalisée."""
    config = configparser.ConfigParser(interpolation=None)
    try:
        with open(path, encoding="utf-8") as configfile:
            config.read_file(configfile)
            log_info(
                f"🧐 Le fichier de configuration '{path}' a été lu avec succès.", lf
            )
            return config
    except UnicodeDecodeError as e:  # noqa: BLE001
        log_info(
            f"🔹 Erreur d'encodage lors de la lecture du fichier '{path}'.",
            lf,
        )
        raise TypeError(str(e)) from e
    except configparser.Error as e:  # noqa: BLE001
        section = getattr(e, "section", "inconnue")
        log_info(
            f"🔹 Erreur de configuration dans la section '{section}' du fichier '{path}': {e}",
            lf,
        )
        raise
    except Exception as e:
        log_info(
            f"🔹 {messages.ERREUR_INATTENDUE} lors de la lecture du fichier '{path}': {e}",
            lf,
        )
        raise RuntimeError(f"Erreur lors de la lecture du fichier '{path}': {e}") from e


def _atomic_write_config(path: str, cfg: configparser.ConfigParser) -> None:
    """Écrit de façon atomique : fichier .tmp puis os.replace()."""
    p = Path(path)
    tmp = p.with_suffix(p.suffix + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            cfg.write(f)
        os.replace(tmp, p)
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:  # pragma: no cover  # nosec B110
            pass


def _get_cached_config(path: str, mtime: float) -> configparser.ConfigParser | None:
    with _CACHE_LOCK:
        cached = _CACHE.get(path)
        return cached[1] if cached and cached[0] == mtime else None


def _set_cache(path: str, mtime: float, cfg: configparser.ConfigParser) -> None:
    with _CACHE_LOCK:
        _CACHE[path] = (mtime, cfg)


@runtime_checkable
class Notifier(Protocol):
    def info(self, title: str, message: str) -> None:  # pragma: no cover
        """Affiche une notification d'information."""


class _MessageboxNotifier:
    def info(self, title: str, message: str) -> None:  # pragma: no cover
        messagebox.showinfo(title, message)


_notifier: Notifier = _MessageboxNotifier()


def set_notifier(n: Notifier | None) -> None:
    """Permet de remplacer le notifier (ex: stub en tests)."""
    global _notifier
    _notifier = n or _MessageboxNotifier()


def _notify_info(title: str, message: str) -> None:
    try:
        _notifier.info(title, message)
    except Exception:  # pragma: no cover  # nosec B110
        pass


# ---------------------------- API publique ---------------------------------


def get_runtime_config_path(log_file: str | None = None) -> str:
    """Retourne le chemin du `config.ini` prêt à l'emploi (copie la version embarquée si besoin)."""
    lf: str = log_file or get_log_file()
    return _ensure_runtime_resource("config.ini", lf)


def get_runtime_resource_path(relative_path: str, log_file: str | None = None) -> str:
    """Retourne le chemin absolu d'une ressource (copie la version embarquée si besoin)."""
    lf: str = log_file or get_log_file()
    return _ensure_runtime_resource(relative_path, lf)


def read_config_ini(log_file: str | None = None) -> configparser.ConfigParser:
    """
    Lit ``config.ini`` et retourne un ConfigParser.
    Utilise un cache invalide dès que le mtime change.
    """
    lf: str = log_file or get_log_file()
    config_path = get_runtime_config_path(log_file=lf)

    _ensure_exists(config_path, lf, "de configuration")

    mtime = os.path.getmtime(config_path)
    cached = _get_cached_config(config_path, mtime)
    if cached:
        log_info("🔹 Configuration chargée depuis le cache.", lf)
        return cached

    config = _read_ini_file(config_path, lf)
    _set_cache(config_path, mtime, config)
    log_info("🔹 Configuration initialisée avec succès.", lf)
    return config


def write_config_ini(
    configuration_personnel: configparser.ConfigParser, log_file: str | None = None
) -> str:
    """Écrit et sauvegarde les modifications dans le fichier `config.ini`."""
    lf: str = log_file or get_log_file()
    config_path = get_runtime_config_path(log_file=lf)

    _ensure_exists(config_path, lf, "de configuration")

    try:
        _atomic_write_config(config_path, configuration_personnel)
        log_info(
            f"💾 Le fichier de configuration '{config_path}' a été sauvegardé avec succès.",
            lf,
        )
        _notify_info("Enregistré", "Configuration sauvegardée avec succès.")
        with _CACHE_LOCK:
            _CACHE.pop(config_path, None)
    except UnicodeDecodeError as e:  # noqa: BLE001
        log_info(
            f"🔹 Erreur d'encodage lors de la lecture du fichier '{config_path}'.",
            lf,
        )
        raise TypeError(str(e)) from e
    except Exception as e:
        log_info(
            f"🔹 {messages.ERREUR_INATTENDUE} lors de la lecture du fichier '{config_path}': {e}",
            lf,
        )
        raise RuntimeError(
            f"Erreur lors de la lecture du fichier '{config_path}': {e}"
        ) from e

    return config_path
