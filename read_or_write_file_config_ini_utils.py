# read_or_write_file_config_ini_utils.py
import configparser
import os
import sys
from tkinter import messagebox
import shutil
from logger_utils import write_log, DEFAULT_LOG_LEVEL


def get_runtime_config_path(log_file=None):
    """ Détermine le chemin du fichier `config.ini` à utiliser.
    Si le fichier n'existe pas dans le répertoire courant, copie la version embarquée.
    """
    
    # Chemin du fichier `config.ini` dans le répertoire courant
    current_dir_config = os.path.join(os.getcwd(), "config.ini")
    write_log(f"Chemin du fichier courant : {current_dir_config}", log_file, DEFAULT_LOG_LEVEL)
    
    # Si PyInstaller est utilisé
    if hasattr(sys, '_MEIPASS'):
        # Chemin du fichier `config.ini` embarqué
        embedded_config = os.path.join(sys._MEIPASS, "config.ini")
        write_log(f"Exécution via PyInstaller. Fichier embarqué : {embedded_config}", log_file, DEFAULT_LOG_LEVEL)
        
        # Copier le fichier embarqué vers le répertoire courant si nécessaire (si absent)
        if not os.path.exists(current_dir_config):
            shutil.copy(embedded_config, current_dir_config)
            write_log(f"Copie de {embedded_config} vers {current_dir_config}", log_file, DEFAULT_LOG_LEVEL)
    else:
        write_log("Exécution en mode script.", log_file, DEFAULT_LOG_LEVEL)
    
    return current_dir_config


def read_config_ini(log_file=None):
    """ Lit et charge le fichier de configuration `config.ini` et Retourne un objet ConfigParser."""
    # Obtenir le chemin du fichier de configuration
    config_file_ini = get_runtime_config_path(log_file=log_file)

    # Vérifier si le fichier existe
    if not os.path.exists(config_file_ini):
        write_log(f"Le fichier '{config_file_ini}' est introuvable.", log_file, DEFAULT_LOG_LEVEL)
        raise FileNotFoundError(f"Le fichier de configuration '{config_file_ini}' est introuvable.")
    else:
        write_log(f"Le fichier '{config_file_ini}' a été trouvé.", log_file, DEFAULT_LOG_LEVEL)

    # Initialiser ConfigParser
    config = configparser.ConfigParser()

    try:
        # Lire le fichier avec l'encodage UTF-8
        with open(config_file_ini, 'r', encoding="utf-8") as configfile:
            config.read_file(configfile)
            write_log(f"Le fichier de configuration '{config_file_ini}' a été lu avec succès.", log_file, DEFAULT_LOG_LEVEL)
    except UnicodeDecodeError as e:
        write_log(f"Erreur d'encodage lors de la lecture du fichier '{config_file_ini}'.", log_file, DEFAULT_LOG_LEVEL)
        raise UnicodeDecodeError(
            f"Erreur d'encodage lors de la lecture du fichier '{config_file_ini}'. "
            f"Assurez-vous qu'il est encodé en UTF-8."
        ) from e
    except Exception as e:
        write_log(f"Une erreur inattendue est survenue lors de la lecture du fichier '{config_file_ini}': {e}", log_file, DEFAULT_LOG_LEVEL)
        raise RuntimeError(f"Erreur lors de la lecture du fichier '{config_file_ini}': {e}") from e

    write_log("Configuration initialisée avec succès.", log_file, DEFAULT_LOG_LEVEL)
    return config


def write_config_ini(configuration_personnel, log_file=None):
    """Écrit et sauvegarde les modifications dans le fichier `config.ini`."""
    # Obtenir le chemin du fichier de configuration
    config_file_ini = get_runtime_config_path(log_file=log_file)

    # Vérifier si le fichier existe
    if not os.path.exists(config_file_ini):
        write_log(f"Le fichier '{config_file_ini}' est introuvable.", log_file, DEFAULT_LOG_LEVEL)
        raise FileNotFoundError(f"Le fichier de configuration '{config_file_ini}' est introuvable.")
    else:
        write_log(f"Le fichier '{config_file_ini}' a été trouvé.", log_file, DEFAULT_LOG_LEVEL)

    try:
        # Écrire dans le fichier avec l'encodage UTF-8
        with open(config_file_ini, 'w', encoding="utf-8") as configfile:
            configuration_personnel.write(configfile)
            write_log(f"Le fichier de configuration '{config_file_ini}' a été sauvegardé avec succès.", log_file, DEFAULT_LOG_LEVEL)
            messagebox.showinfo("Enregistré", "Configuration sauvegardée avec succès.")
    except UnicodeDecodeError as e:
        write_log(f"Erreur d'encodage lors de la lecture du fichier '{config_file_ini}'.", log_file, DEFAULT_LOG_LEVEL)
        raise UnicodeDecodeError(
            f"Erreur d'encodage lors de la lecture du fichier '{config_file_ini}'. "
            f"Assurez-vous qu'il est encodé en UTF-8."
        ) from e
    except Exception as e:
        write_log(f"Une erreur inattendue est survenue lors de la lecture du fichier '{config_file_ini}': {e}", log_file, DEFAULT_LOG_LEVEL)
        raise RuntimeError(f"Erreur lors de la lecture du fichier '{config_file_ini}': {e}") from e

    return config_file_ini
