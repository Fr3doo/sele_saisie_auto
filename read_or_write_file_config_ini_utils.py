import configparser
import os
import sys
from tkinter import messagebox
import shutil

def get_runtime_config_path():
    """ Détermine le chemin du fichier `config.ini` à utiliser.
    Si le fichier n'existe pas dans le répertoire courant, copie la version embarquée.
    """
    # Chemin du fichier `config.ini` dans le répertoire courant
    current_dir_config = os.path.join(os.getcwd(), "config.ini")
    print(f"DEBUG: {current_dir_config}")
    
    # Si PyInstaller est utilisé
    if hasattr(sys, '_MEIPASS'):
        # Chemin du fichier `config.ini` embarqué
        embedded_config = os.path.join(sys._MEIPASS, "config.ini")
        print("DEBUG: Exécution via PyInstaller. Fichier embarqué :", embedded_config)
        
        # Copier le fichier embarqué vers le répertoire courant si nécessaire (si absent)
        if not os.path.exists(current_dir_config):
            shutil.copy(embedded_config, current_dir_config)
            print(f"DEBUG: Copie de {embedded_config} vers {current_dir_config}")
    else:
        print("DEBUG: Exécution en mode script.")
    
    return current_dir_config


def read_config_ini():
    """ Lit et charge le fichier de configuration `config.ini` et Retourne un objet ConfigParser.
    """
    # Obtenir le chemin du fichier de configuration
    config_file_ini = get_runtime_config_path()

    # Vérifier si le fichier existe
    if not os.path.exists(config_file_ini):
        print(f"ERREUR: Le fichier '{config_file_ini}' est introuvable.")
        raise FileNotFoundError(f"Le fichier de configuration '{config_file_ini}' est introuvable.")
    else:
        print(f"DEBUG: Le fichier '{config_file_ini}' a été trouvé.")

    # Initialiser ConfigParser
    config = configparser.ConfigParser()

    try:
        # Lire le fichier avec l'encodage UTF-8
        with open(config_file_ini, 'r', encoding="utf-8") as configfile:
            config.read_file(configfile)
            print(f"DEBUG: Le fichier de configuration '{config_file_ini}' a été lu avec succès.")
    except UnicodeDecodeError as e:
        print(f"ERREUR: Erreur d'encodage lors de la lecture du fichier '{config_file_ini}'.")
        raise UnicodeDecodeError(
            f"Erreur d'encodage lors de la lecture du fichier '{config_file_ini}'. "
            f"Assurez-vous qu'il est encodé en UTF-8."
        ) from e
    except Exception as e:
        print(f"ERREUR: Une erreur inattendue est survenue lors de la lecture du fichier '{config_file_ini}': {e}")
        raise RuntimeError(f"Erreur lors de la lecture du fichier '{config_file_ini}': {e}") from e

    print("DEBUG: Configuration initialisée avec succès.")
    return config


def write_config_ini(configuration_personnel):
    """
    Écrit et sauvegarde les modifications dans le fichier `config.ini`.
    """
    # Obtenir le chemin du fichier de configuration
    config_file_ini = get_runtime_config_path()

    # Vérifier si le fichier existe
    if not os.path.exists(config_file_ini):
        print(f"ERREUR: Le fichier '{config_file_ini}' est introuvable.")
        raise FileNotFoundError(f"Le fichier de configuration '{config_file_ini}' est introuvable.")
    else:
        print(f"DEBUG: Le fichier '{config_file_ini}' a été trouvé.")

    try:
        # Écrire dans le fichier avec l'encodage UTF-8
        with open(config_file_ini, 'w', encoding="utf-8") as configfile:
            configuration_personnel.write(configfile)
            print(f"DEBUG: Le fichier de configuration '{config_file_ini}' a été sauvegardé avec succès.")
            messagebox.showinfo("Enregistré", "Configuration sauvegardée avec succès.")
    except UnicodeDecodeError as e:
        print(f"ERREUR: Erreur d'encodage lors de la lecture du fichier '{config_file_ini}'.")
        raise UnicodeDecodeError(
            f"Erreur d'encodage lors de la lecture du fichier '{config_file_ini}'. "
            f"Assurez-vous qu'il est encodé en UTF-8."
        ) from e
    except Exception as e:
        print(f"ERREUR: Une erreur inattendue est survenue lors de la lecture du fichier '{config_file_ini}': {e}")
        raise RuntimeError(f"Erreur lors de la lecture du fichier '{config_file_ini}': {e}") from e

    return config_file_ini
