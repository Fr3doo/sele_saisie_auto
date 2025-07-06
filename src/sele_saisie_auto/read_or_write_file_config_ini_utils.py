# pragma: no cover
# read_or_write_file_config_ini_utils.py
import configparser
import os
import shutil
import sys
from tkinter import messagebox

from sele_saisie_auto import messages
from sele_saisie_auto.logger_utils import DEFAULT_LOG_LEVEL, write_log

# Cache des configurations lues, indexé par chemin du fichier
_CACHE: dict[str, tuple[float, configparser.ConfigParser]] = {}


def clear_cache() -> None:
    """Vide le cache de configuration."""
    _CACHE.clear()


def get_runtime_config_path(log_file=None):
    """Détermine le chemin du fichier `config.ini` à utiliser.
    Si le fichier n'existe pas dans le répertoire courant, copie la version embarquée.
    """

    # Chemin du fichier `config.ini` dans le répertoire courant
    current_dir_config = os.path.join(os.getcwd(), "config.ini")
    write_log(
        f"🔹 Chemin du fichier courant : {current_dir_config}",
        log_file,
        DEFAULT_LOG_LEVEL,
    )

    # Si PyInstaller est utilisé
    if hasattr(sys, "_MEIPASS"):
        # Chemin du fichier `config.ini` embarqué
        embedded_config = os.path.join(sys._MEIPASS, "config.ini")
        write_log(
            f"🔹 Exécution via PyInstaller. Fichier embarqué : {embedded_config}",
            log_file,
            DEFAULT_LOG_LEVEL,
        )

        # Copier le fichier embarqué vers le répertoire courant si nécessaire (si absent)
        if not os.path.exists(current_dir_config):
            shutil.copy(embedded_config, current_dir_config)
            write_log(
                f"🔹 Copie de {embedded_config} vers {current_dir_config}",
                log_file,
                DEFAULT_LOG_LEVEL,
            )
    else:
        write_log("🔹 Exécution en mode script.", log_file, DEFAULT_LOG_LEVEL)

    return current_dir_config


def get_runtime_resource_path(relative_path, log_file=None):
    """Détermine le chemin absolu d'une ressource (comme une image) à utiliser.
    Si le fichier n'existe pas dans le répertoire courant, copie la version embarquée.
    """
    # Chemin de la ressource dans le répertoire courant
    current_dir_resource = os.path.join(os.getcwd(), relative_path)
    write_log(
        f"🔹 Chemin du fichier courant : {current_dir_resource}",
        log_file,
        DEFAULT_LOG_LEVEL,
    )

    # Si PyInstaller est utilisé
    if hasattr(sys, "_MEIPASS"):
        # Chemin de la ressource embarquée
        embedded_resource = os.path.join(sys._MEIPASS, relative_path)
        write_log(
            f"🔹 Exécution via PyInstaller. Fichier embarqué : {embedded_resource}",
            log_file,
            DEFAULT_LOG_LEVEL,
        )

        # Copier le fichier embarqué vers le répertoire courant si nécessaire (si absent)
        if not os.path.exists(current_dir_resource):
            try:
                shutil.copy(embedded_resource, current_dir_resource)
                write_log(
                    f"🔹 Copie de {embedded_resource} vers {current_dir_resource}",
                    log_file,
                    DEFAULT_LOG_LEVEL,
                )
            except FileNotFoundError as e:
                write_log(
                    f"🔴 Fichier embarqué {messages.INTROUVABLE} : {embedded_resource}",
                    log_file,
                    "ERROR",
                )
                raise FileNotFoundError(
                    f"{messages.IMPOSSIBLE_DE_TROUVER} le fichier embarqué : {embedded_resource}"
                ) from e
            except PermissionError as e:
                write_log(
                    f"🔴 Permission refusée pour copier {embedded_resource} vers {current_dir_resource}",
                    log_file,
                    "ERROR",
                )
                raise PermissionError(
                    f"Permission refusée pour copier : {embedded_resource}"
                ) from e
    else:
        write_log("🔹 Exécution en mode script.", log_file, DEFAULT_LOG_LEVEL)

    return current_dir_resource


def read_config_ini(log_file=None):
    """Lit ``config.ini`` et retourne un :class:`ConfigParser`.

    Si le fichier n'a pas changé depuis la dernière lecture,
    la configuration est retournée depuis le cache.
    """
    config_file_ini = get_runtime_config_path(log_file=log_file)

    if not os.path.exists(config_file_ini):
        write_log(
            f"🔹 Le fichier '{config_file_ini}' est {messages.INTROUVABLE}.",
            log_file,
            DEFAULT_LOG_LEVEL,
        )
        raise FileNotFoundError(
            f"Le fichier de configuration '{config_file_ini}' est {messages.INTROUVABLE}."
        )
    else:
        write_log(
            f"🔹 Le fichier '{config_file_ini}' a été trouvé.",
            log_file,
            DEFAULT_LOG_LEVEL,
        )

    current_mtime = os.path.getmtime(config_file_ini)
    cached = _CACHE.get(config_file_ini)
    if cached and cached[0] == current_mtime:
        write_log(
            "🔹 Configuration chargée depuis le cache.",
            log_file,
            DEFAULT_LOG_LEVEL,
        )
        return cached[1]

    config = configparser.ConfigParser()

    try:
        # Lire le fichier avec l'encodage UTF-8
        with open(config_file_ini, encoding="utf-8") as configfile:
            config.read_file(configfile)
            write_log(
                f"🧐 Le fichier de configuration '{config_file_ini}' a été lu avec succès.",
                log_file,
                DEFAULT_LOG_LEVEL,
            )
    except UnicodeDecodeError as e:
        write_log(
            f"🔹 Erreur d'encodage lors de la lecture du fichier '{config_file_ini}'.",
            log_file,
            DEFAULT_LOG_LEVEL,
        )
        raise UnicodeDecodeError(
            f"Erreur d'encodage lors de la lecture du fichier '{config_file_ini}'. "
            f"Assurez-vous qu'il est encodé en UTF-8."
        ) from e
    except Exception as e:
        write_log(
            f"🔹 {messages.ERREUR_INATTENDUE} lors de la lecture du fichier '{config_file_ini}': {e}",
            log_file,
            DEFAULT_LOG_LEVEL,
        )
        raise RuntimeError(
            f"Erreur lors de la lecture du fichier '{config_file_ini}': {e}"
        ) from e

    _CACHE[config_file_ini] = (current_mtime, config)
    write_log("🔹 Configuration initialisée avec succès.", log_file, DEFAULT_LOG_LEVEL)
    return config


def write_config_ini(configuration_personnel, log_file=None):
    """Écrit et sauvegarde les modifications dans le fichier `config.ini`."""
    # Obtenir le chemin du fichier de configuration
    config_file_ini = get_runtime_config_path(log_file=log_file)

    # Vérifier si le fichier existe
    if not os.path.exists(config_file_ini):
        write_log(
            f"🔹 Le fichier '{config_file_ini}' est {messages.INTROUVABLE}.",
            log_file,
            DEFAULT_LOG_LEVEL,
        )
        raise FileNotFoundError(
            f"Le fichier de configuration '{config_file_ini}' est {messages.INTROUVABLE}."
        )
    else:
        write_log(
            f"🔹 Le fichier '{config_file_ini}' a été trouvé.",
            log_file,
            DEFAULT_LOG_LEVEL,
        )

    try:
        # Écrire dans le fichier avec l'encodage UTF-8
        with open(config_file_ini, "w", encoding="utf-8") as configfile:
            configuration_personnel.write(configfile)
            write_log(
                f"💾 Le fichier de configuration '{config_file_ini}' a été sauvegardé avec succès.",
                log_file,
                DEFAULT_LOG_LEVEL,
            )
            messagebox.showinfo("Enregistré", "Configuration sauvegardée avec succès.")
        _CACHE.pop(config_file_ini, None)
    except UnicodeDecodeError as e:
        write_log(
            f"🔹 Erreur d'encodage lors de la lecture du fichier '{config_file_ini}'.",
            log_file,
            DEFAULT_LOG_LEVEL,
        )
        raise UnicodeDecodeError(
            f"Erreur d'encodage lors de la lecture du fichier '{config_file_ini}'. "
            f"Assurez-vous qu'il est encodé en UTF-8."
        ) from e
    except Exception as e:
        write_log(
            f"🔹 {messages.ERREUR_INATTENDUE} lors de la lecture du fichier '{config_file_ini}': {e}",
            log_file,
            DEFAULT_LOG_LEVEL,
        )
        raise RuntimeError(
            f"Erreur lors de la lecture du fichier '{config_file_ini}': {e}"
        ) from e

    return config_file_ini
