# main.py
# pyinstaller --onefile --add-data "config.ini:." --add-data "calendar_icon.png:." --hidden-import "saisie_automatiser_psatime" --hidden-import "encryption_utils" --hidden-import "cryptography.hazmat.bindings._rust" --hidden-import "cryptography.hazmat.primitives.ciphers" --hidden-import "cryptography.hazmat.primitives.padding" --hidden-import "tkcalendar" --hidden-import "babel.numbers" main.py 
# OU
# pyinstaller main.spec

# Import des bibliothèques nécessaires
# import configparser
import datetime
import multiprocessing
import tkinter as tk
from tkinter import ttk, messagebox, StringVar
from tkcalendar import Calendar
import re
import time
# import subprocess
# import sys
# import os
from dropdown_options import work_location_options, cgi_options, cgi_options_dejeuner, work_schedule_options, cgi_options_billing_action
from encryption_utils import generer_cle_aes, chiffrer_donnees, stocker_en_memoire_partagee
from encryption_utils import supprimer_memoire_partagee_securisee
# from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
# from cryptography.hazmat.primitives.padding import PKCS7
from multiprocessing import shared_memory
from read_or_write_file_config_ini_utils import get_runtime_resource_path, read_config_ini, write_config_ini
from logger_utils import initialize_logger, write_log, close_logs, LOG_LEVELS
from shared_utils import get_log_file
from PIL import Image, ImageTk  # Pour la gestion des images
# ----------------------------------------------------------------------------- #
# ------------------------------- CONSTANTE ----------------------------------- #
# ----------------------------------------------------------------------------- #

# Jours de la semaine
JOURS_SEMAINE__DICT = {'lundi': '', 'mardi': '', 'mercredi': '', 'jeudi': '', 'vendredi': '', 'samedi': '', 'dimanche': ''}
JOURS_SEMAINE__LIST = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"]

# Valeurs par défaut pour les sections de configuration
DEFAULT_CREDENTIALS = {'login': '', 'mdp': ''}
DEFAULT_SETTINGS = {'date_cible': '', 'debug_mode': 'False'}
DEFAULT_WORK_SCHEDULE = JOURS_SEMAINE__DICT
DEFAULT_WORK_LOCATION_AM = JOURS_SEMAINE__DICT
DEFAULT_WORK_LOCATION_PM = JOURS_SEMAINE__DICT

# Sections additionnelles pour "Informations CGI"
ADDITIONAL_SECTIONS = [
    'additional_information_rest_period_respected',
    'additional_information_work_time_range',
    'additional_information_half_day_worked',
    'additional_information_lunch_break_duration'
]

# Sections pour les Informations projet
DEFAULT_PROJECT_INFORMATION = {
    'project_code':'',
    'activity_code':'',
    'category_code':'',
    'sub_category_code':'',
    'billing_action':''
}

# Correspondances entre les noms affichés et les noms dans config.ini
ADDITIONAL_SECTION_LABELS = {
    'additional_information_rest_period_respected': 'période repos respectée',
    'additional_information_work_time_range': 'plage horaire travail',
    'additional_information_half_day_worked': 'demi-journée travaillée',
    'additional_information_lunch_break_duration': 'durée pause déjeuner'
}

# Recuperation des valeurs dans dropdown_options.py
BILLING_ACTIONS_CHOICES = list(cgi_options_billing_action.keys())


# LOG_LEVELS_CHOICES_ALL = list(LOG_LEVELS.keys()) # Pour recuperer le LEVEL 'CRITICAL'
LOG_LEVELS_CHOICES = list(LOG_LEVELS.keys())[:-1] # Pour retirer le LEVEL 'CRITICAL'

# Définition des couleurs et du style
COLORS = {
    'primary': '#2563eb',       # Bleu principal
    'secondary': '#f8fafc',     # Fond clair
    'text': '#1e293b',          # Texte principal
    'border': '#e2e8f0',        # Bordures
    'hover': '#3b82f6',         # Survol
    'success': '#22c55e',       # Vert pour succès
    'background': '#ffffff',    # Fond blanc
    'light_yellow': '#fefce8'   # Fond pour les notes
}

# Configuration
MEMOIRE_PARTAGEE_CLE = "memoire_partagee_cle"
MEMOIRE_PARTAGEE_DONNEES = "memoire_partagee_donnees"
DUREE_DE_VIE_CLE = 10  # En secondes
TAILLE_CLE = 32  # 256 bits pour AES-256
TAILLE_BLOC = 128  # Taille de bloc AES pour le padding

# ----------------------------------------------------------------------------- #
# ------------------------------- STYLES -------------------------------------- #
# ----------------------------------------------------------------------------- #
def setup_modern_style(configuration, colors):
    style = ttk.Style(configuration)

    # Configuration générale
    style.configure('Modern.TFrame', background=colors['background'])
    style.configure('Modern.TLabel', 
                   background=colors['background'],
                   foreground=colors['text'],
                   font=('Segoe UI', 10))
    
    # Titres
    style.configure('Title.TLabel',
                   font=('Segoe UI', 11, 'bold'),
                   foreground=colors['primary'])
    
    # Notebook et onglets
    style.configure('Modern.TNotebook', 
                   background=colors['background'])
    
    # Configuration de base des onglets
    style.configure('Modern.TNotebook.Tab',
                   padding=[15, 5],
                   font=('Segoe UI', 9),
                   background=colors['secondary'],
                   foreground=colors['text'])  # Couleur du texte par défaut
    
    # Configuration des états des onglets
    style.map('Modern.TNotebook.Tab',
             background=[('selected', colors['primary']),   # Fond bleu quand sélectionné
                        ('active', colors['hover'])],       # Fond bleu clair au survol
             foreground=[('selected', colors['primary']),   # Texte blanc quand sélectionné
                        ('active', colors['text'])])        # Texte normal au survol
    
    # Entry et Combobox
    style.configure('Modern.TEntry',
                   fieldbackground=colors['secondary'],
                   padding=[5, 5])
    
    style.configure('Modern.TCombobox',
                   background=colors['secondary'],
                   fieldbackground=colors['secondary'],
                   padding=[5, 5])
    
    # Button
    style.configure('Modern.TButton',
                   padding=[20, 10],
                   background=colors['primary'],
                   font=('Segoe UI', 10, 'bold'))
    style.map('Modern.TButton',
             background=[('active', colors['hover'])])
    
    # Parametres et notes
    style.configure('Parametres.TLabelframe',
                   background=COLORS['background'],
                   padding=10,
                   borderwidth=1,
                   relief='solid')

    style.configure('Parametres.TLabelframe.Label',
                   background=COLORS['background'],
                   font=('Segoe UI', 10, 'bold'))

# ----------------------------------------------------------------------------- #
# ------------------------------- FONCTIONS ----------------------------------- #
# ----------------------------------------------------------------------------- #

def run_psatime_with_credentials(cle_aes, login_var, mdp_var, log_file):
    try:
        login = login_var.get()
        password = mdp_var.get()
        
        if not login or not password:
            messagebox.showerror("Erreur", "Veuillez entrer votre login et mot de passe.")
            return None
        
        # Chiffrer les informations
        nom_utilisateur_chiffre = chiffrer_donnees(login, cle_aes, log_file=log_file)
        mot_de_passe_chiffre = chiffrer_donnees(password, cle_aes, log_file=log_file)
        memoire_cle = stocker_en_memoire_partagee(MEMOIRE_PARTAGEE_CLE, cle_aes, log_file=log_file)
        write_log(f"Données à chiffrer pour l'utilisateur: {login}.", log_file, "CRITICAL")
        write_log(f"Données à chiffrer pour le password: {password}.", log_file, "CRITICAL")
        write_log(f"Données chiffrées stockées pour l'utilisateur: {nom_utilisateur_chiffre}.", log_file, "CRITICAL")
        write_log(f"Données chiffrées stockées pour le password: {mot_de_passe_chiffre}.", log_file, "CRITICAL")
        write_log(f"Taille des données chiffrées du nom d'utilisateur: {len(nom_utilisateur_chiffre)}", log_file, "CRITICAL")
        write_log(f"Taille des données chiffrées du mot de passe: {len(mot_de_passe_chiffre)}", log_file, "CRITICAL")
        
        memoire_nom = shared_memory.SharedMemory(name="memoire_nom", create=True, size=len(nom_utilisateur_chiffre))
        memoire_nom.buf[:len(nom_utilisateur_chiffre)] = nom_utilisateur_chiffre

        memoire_mdp = shared_memory.SharedMemory(name="memoire_mdp", create=True, size=len(mot_de_passe_chiffre))
        memoire_mdp.buf[:len(mot_de_passe_chiffre)] = mot_de_passe_chiffre

        write_log(f"Clé et données chiffrées stockées dans la mémoire partagée.", log_file, "CRITICAL")
        write_log(f"Lancement de PSATime avec login: {login}@cgi.com et mot de passe.", log_file, "CRITICAL")

        run_psatime(log_file)
    except Exception as e:
        write_log(f"Erreur rencontrée : {str(e)}", log_file, "ERROR")
        raise RuntimeError("Une erreur critique est survenue.") from e
    else:
        # Suppression sécurisée
        time.sleep(DUREE_DE_VIE_CLE)
        if memoire_nom is not None:
            supprimer_memoire_partagee_securisee(memoire_nom, log_file=log_file)
        if memoire_mdp is not None:
            supprimer_memoire_partagee_securisee(memoire_mdp, log_file=log_file)
        if memoire_cle is not None:
            # Suppression sécurisée des mémoires partagées
            supprimer_memoire_partagee_securisee(memoire_cle, log_file=log_file)
        write_log(f"🏁 [FIN] Clé et données supprimées de manière sécurisée, des mémoires partagées du fichier main.", log_file, "INFO")


def run_psatime(log_file):
    # Fermez la fenêtre graphique
    menu.destroy()
    write_log(f"📌 Lancement de la fonction 'main' du fichier 'saisie_automatiser_psatime.py'", log_file, "INFO")
    import saisie_automatiser_psatime # Import de saisie_automatiser_psatime.py comme module
    saisie_automatiser_psatime.main()


# Fonction de filtrage pour la recherche dynamique
def filter_combobox_on_enter(event, combobox, all_values):
    """Appliquer le filtre uniquement sur appui de la touche Entrée."""
    search_text = combobox.get().lower()
    filtered_values = [value for value in all_values if search_text in value.lower()]
    combobox['values'] = filtered_values
    if filtered_values:
        combobox.event_generate('<Down>')  # Ouvre le menu déroulant


def check_and_initialize_section(configuration, section, defaults):
    """Vérification de l'existence des sections et ajout de valeurs par défaut si elles sont manquantes"""
    if not configuration.has_section(section):
        configuration.add_section(section)
    for key, value in defaults.items():
        if not configuration.has_option(section, key):
            configuration.set(section, key, value)


def validate_data(date):
    """Valide le format de la date (jj/mm/aaaa) si une valeur est fournie."""
    date_cible = date.get()

    # Si la date est vide ou None, considérer comme valide
    if date_cible in (None, "", "None"):
        return True

    # si une valeur est fournie, Validation du format de date cible.
    date_pattern = re.compile(r'^\d{2}/\d{2}/\d{4}$')
    if not date_pattern.match(date_cible):
        messagebox.showerror("Erreur", "La date cible doit être au format jj/mm/aaaa")
        return False
    else:
        return True


def seperator_ttk(menu, orient='horizontal', fill='x', padx=10, pady=5):
    separator = ttk.Separator(menu, orient=orient)
    separator.pack(fill=fill, padx=padx, pady=pady)


def create_basic_StringVar(value="", default=""):
    return tk.StringVar(value=value if value else default)


def create_structured_StringVar(config, section, key, default="", index=None):
    value = config[section].get(key, default)
    if index is not None and ',' in value:
        value = value.split(',')[index]
    return tk.StringVar(value=value)


def create_structured_BooleanVar(config, section, key, default=False):
    """Crée un tk.BooleanVar basé sur une valeur dans la configuration."""
    value = default
    if config.has_section(section) and config.has_option(section, key):
        try:
            value = config.getboolean(section, key)
        except ValueError:
            pass  # Garde la valeur par défaut si la conversion échoue
    return tk.BooleanVar(value=value)


def create_tab(notebook, title, style="Modern.TFrame", padding=20):
    """Crée un onglet (ttk.Frame) et l'ajoute à un ttk.Notebook."""
    tab_frame = ttk.Frame(notebook, style=style, padding=padding)
    notebook.add(tab_frame, text=title)
    return tab_frame


def create_Title_label_with_grid(frame, text, row, col, style='Title.TLabel', padx=5, pady=5, sticky="w"):
    """Crée un Label et le place dans le cadre donné."""
    title_label = ttk.Label(frame, text=text, style=style)
    title_label.grid(row=row, column=col, padx=padx, pady=pady, sticky=sticky)
    return title_label


def create_a_frame(parent, style="Modern.TFrame", side=None, fill="both", expand=True, padx=0, pady=0, padding=None):
    """Crée un ttk.Frame avec des paramètres configurables et le positionne avec `pack`."""
    frame = ttk.Frame(parent, style=style, padding=padding)
    frame.pack(side=side, fill=fill, expand=expand, padx=padx, pady=pady)
    return frame


def create_labeled_frame(parent, text="", style="Parametres.TLabelframe", side=None, fill="both", expand=True, padx=0, pady=0, padding=None):
    """Crée un ttk.LabelFrame avec un texte et le positionne avec `pack`."""
    label_frame = ttk.LabelFrame(parent, text=text, style=style, padding=padding)
    label_frame.pack(side=side, fill=fill, expand=expand, padx=padx, pady=pady)
    return label_frame


def create_Modern_label_with_pack(frame, text, style="Modern.TLabel", side=None, padx=0, pady=0, sticky=None):
    """"""
    modern_label_pack = ttk.Label(frame, text=text, style=style)
    modern_label_pack.pack(side=side, padx=padx, pady=pady, sticky=sticky)
    return modern_label_pack


def create_Modern_entry_with_pack(frame, var, width=20, style="Settings.TEntry", side=None, padx=0, pady=0):
    """"""
    modern_entry_pack = ttk.Entry(frame, textvariable=var, width=width, style=style)
    modern_entry_pack.pack(side=side, padx=padx, pady=pady)
    return modern_entry_pack


def create_Modern_checkbox_with_pack(parent, var, style_checkbox="Modern.TCheckbutton", side=None, padx=0, pady=0):
    """Crée une case à cocher avec l'option .pack."""
    checkbox = ttk.Checkbutton(parent, variable=var, style=style_checkbox)
    checkbox.pack(side=side, padx=padx, pady=pady)
    return checkbox


def create_Modern_label_with_grid(frame, text, row, col, style="Modern.TLabel", padx=5, pady=5, sticky="w"):
    """Crée un Label et le place dans le cadre donné."""
    modern_label_grid = ttk.Label(frame, text=text, style=style)
    modern_label_grid.grid(row=row, column=col, padx=padx, pady=pady, sticky=sticky)
    return modern_label_grid


def create_Modern_entry_with_grid(frame, var, row, col, width=20, style="Modern.TEntry", padx=5, pady=5):
    """Crée un Entry lié à une variable et le place dans le cadre donné."""
    modern_entry_grid = ttk.Entry(frame, textvariable=var, width=width, style=style)
    modern_entry_grid.grid(row=row, column=col, padx=padx, pady=pady)
    return modern_entry_grid


def create_Modern_entry_with_grid_for_password(frame, var, row, col, width=20, style="Modern.TEntry", padx=5, pady=5):
    """Crée un Entry lié à une variable et le place dans le cadre donné."""
    modern_entry_grid_for_password = ttk.Entry(frame, textvariable=var,  show='*', width=width, style=style)
    modern_entry_grid_for_password.grid(row=row, column=col, padx=padx, pady=pady)
    return modern_entry_grid_for_password


def create_combobox_with_pack(frame, var, values, width=20, style="Modern.TCombobox", state="normal", side="top", padx=5, pady=5):
    """Crée une Combobox liée à une variable et la place dans le cadre donné avec pack."""
    modern_combobox_pack = ttk.Combobox(frame, textvariable=var, values=values, width=width, style=style, state=state)
    modern_combobox_pack.pack(side=side, padx=padx, pady=pady)
    return modern_combobox_pack


def create_combobox(frame, var, values, row, col, width=20, style="Modern.TCombobox", state="normal", padx=5, pady=8):
    """Crée une Combobox liée à une variable et la place dans le cadre donné avec grid."""
    modern_combobox_grid = ttk.Combobox(frame, textvariable=var, values=values, width=width, style=style, state=state)
    modern_combobox_grid.grid(row=row, column=col, padx=padx, pady=pady)
    return modern_combobox_grid


def create_button_with_style(frame, text, command, style="Modern.TButton", side=None, fill=None, padx=None, pady=None, ipady=None):
    """Crée un bouton ttk avec un style et l'ajoute au parent avec `.pack`."""
    button = ttk.Button(frame, text=text, command=command, style=style)
    button.pack(side=side, fill=fill, padx=padx, pady=pady, ipady=ipady)
    return button


def create_button_without_style(frame, text, command, side=None, fill="x", padx=20, pady=5, ipady=5):
    """Crée un bouton tk sans style et l'ajoute au parent avec `.pack`."""
    button = tk.Button(frame, text=text, command=command)
    button.pack(side=side, fill=fill, padx=padx, pady=pady, ipady=ipady)
    return button


def update_mission_frame_visibility(frame, active_mission_days):
    """Affiche ou masque le cadre des informations de mission en fonction de `active_mission_days`."""
    if active_mission_days:  # Si un ou plusieurs jours ont "En mission"
        frame.grid()  # Affiche le cadre
    else:
        frame.grid_remove()  # Masque le cadre si aucun jour n'a "En mission"


def handle_mission_selection(event, combo, frame, day, active_mission_days):
    """Ajoute ou retire un jour de la liste `active_mission_days`."""
    write_log(f"Événement déclenché par : {event.widget}", log_file, "DEBUG") # Affiche la Combobox déclenchant l'événement
    write_log(f"Type d'événement : {event.type}", log_file, "DEBUG") # Affiche le type d'événement
    if combo.get() == "En mission":
        if day not in active_mission_days:  # Ajouter uniquement si non présent
            active_mission_days.append(day)
    else:
        if day in active_mission_days:  # Retirer uniquement si présent
            active_mission_days.remove(day)
    # Mettre à jour l'affichage du cadre
    update_mission_frame_visibility(frame, active_mission_days)


def attach_event(combo, current_day, mission_frame, active_mission_days):
    """Attache l'événement pour gérer la sélection des items."""
    combo.bind("<<ComboboxSelected>>", 
               lambda event: handle_mission_selection(event, combo, mission_frame, current_day, active_mission_days))


def add_date_picker(parent, var, label_text="Date cible (jj/mm/aaaa):"):
    """Ajoute un champ avec un bouton pour ouvrir un calendrier réutilisable."""
    # Utilise un cadre standard pour contenir l'étiquette et l'entrée
    date_frame = create_a_frame(parent, fill="x", expand=False, pady=(0, 15))

    # Ajouter une étiquette
    create_Modern_label_with_pack(date_frame, label_text, side="left", padx=5, pady=5)

    # Ajouter une entrée pour la date
    create_Modern_entry_with_pack(date_frame, var, side="left", padx=0, pady=0)

    # Fenêtre de calendrier réutilisable
    calendar_window = None

    def open_calendar(button):
        """Ouvre une fenêtre avec un calendrier réutilisable."""
        nonlocal calendar_window
        if calendar_window is None or not calendar_window.winfo_exists():
            # Créer une nouvelle fenêtre si elle n'existe pas ou a été fermée
            calendar_window = tk.Toplevel(parent)
            calendar_window.title("Sélectionner une date")
            calendar_window.geometry("300x300")
            calendar_window.resizable(False, False)

            # Obtenir la position de l'icône ou du bouton
            button_x = button.winfo_rootx()
            button_y = button.winfo_rooty()
            button_height = button.winfo_height()

            # Ajuster la position de la fenêtre pour qu'elle s'affiche près du bouton
            calendar_window.geometry(f"+{button_x}+{button_y + button_height + 5}")  # Décalage de 5 pixels sous le bouton
            
            # Ajouter le calendrier (en français, sans numéro de semaine, avec la date actuelle)
            cal = Calendar(
                calendar_window,
                selectmode="day",
                date_pattern="dd/mm/yyyy",
                locale="fr_FR",
                showweeknumbers=False,
                mindate=datetime.date.today(),
                background="#f9f9f9",
                foreground="black",
                disabledbackground="#e0e0e0",
                bordercolor="#cfcfcf",
                headersbackground="#4CAF50",
                headersforeground="white",
                selectbackground="#2196F3",
                selectforeground="white",
                normalbackground="#ffffff",
                normalforeground="#333333",
                weekendbackground="#FFEBEE",
                weekendforeground="#E91E63",
                othermonthforeground="#9E9E9E",
                othermonthbackground="#F5F5F5"
            )
            cal.pack(padx=25, pady=25)

            # Bouton pour valider la date sélectionnée
            def validate_date():
                selected_date = cal.get_date()
                var.set(selected_date)  # Mettre à jour la variable associée à l'entrée
                calendar_window.withdraw()  # Masquer la fenêtre au lieu de la détruire
                messagebox.showinfo("Date sélectionnée", f"Vous avez sélectionné : {selected_date}")

            # Ajouter le bouton "Valider"
            create_button_with_style(calendar_window, "Valider", validate_date, side="top", pady=10)
        else:
            # Si la fenêtre existe, la montrer de nouveau
            calendar_window.deiconify()

    # Ajouter un bouton avec une icône pour ouvrir le calendrier
    try:
        # Charger l'image de l'icône avec le chemin correct
        icon_path = get_runtime_resource_path("calendar_icon.png", log_file)
        icon_image = Image.open(icon_path)
        # icon_image = Image.open(get_resource_path("calendar_icon.png", log_file))
        # icon_image = Image.open("calendar_icon.png")  # Charger l'image
        resized_icon = icon_image.resize((16, 16), Image.Resampling.LANCZOS)  # Redimensionner à 16x16 pixels
        icon_photo = ImageTk.PhotoImage(resized_icon)
        button = ttk.Button(date_frame, image=icon_photo, command=lambda: open_calendar(button))
        button.image = icon_photo  # Conserver une référence pour éviter la collecte de déchets
        button.pack(side=None, fill=None, padx=5, pady=5, ipady=0)
    except FileNotFoundError:
        # Si l'image n'est pas disponible, utiliser un texte par défaut
        write_log("🔹 Icône non trouvée, utilisation du texte par défaut.", log_file, "DEBUG")
        create_button_without_style(date_frame, "📅", open_calendar, side="left", padx=5, pady=5)

    return date_frame

# Fonction pour sauvegarder les modifications dans config.ini
def save_config(elements):
    fichier_configuration_ini   = elements[0]
    date_cible                  = elements[1] 
    debug_mode                  = elements[2]
    work_schedule               = elements[3]
    additional_info             = elements[4]
    work_location               = elements[5]
    main_configuration          = elements[6]
    cle_aes                     = elements[7]
    project_code_var            = elements[8]
    activity_code_var           = elements[9]
    category_code_var           = elements[10]
    sub_category_code_var       = elements[11] 
    billing_action_var          = elements[12]
    log_file_var                = elements[13]
    
    messagebox.showinfo("Sauvegarde en cours", "Veuillez patienter pendant que la configuration est sauvegardée.")
    if not validate_data(date_cible):
        return

    try:
        # Enregistrer les paramètres généraux
        fichier_configuration_ini['settings']['date_cible'] = date_cible.get() if date_cible.get() else "None"
        fichier_configuration_ini['settings']['debug_mode'] = str(debug_mode.get())

        # Enregistrer la configuration du planning de travail
        for day, (desc_var, hours_var) in work_schedule.items():
            description = desc_var.get().strip()
            hours = hours_var.get().strip()
            # Format attendu : description,heures ou juste une virgule si vide
            fichier_configuration_ini['work_schedule'][day] = f"{description},{hours}" if description or hours else ","

        # Enregistrer les informations CGI
        for day, sections in additional_info.items():
            for section, var in sections.items():
                fichier_configuration_ini[section][day] = var.get()

        # Enregistrer le lieu de travail
        for day, var in work_location.items():
            fichier_configuration_ini['work_location_am'][day] = var[0].get()
            fichier_configuration_ini['work_location_pm'][day] = var[1].get()

        # Enregistrer les informations de mission
        fichier_configuration_ini['project_information']['project_code'] = project_code_var.get()
        fichier_configuration_ini['project_information']['activity_code'] = activity_code_var.get()
        fichier_configuration_ini['project_information']['category_code'] = category_code_var.get()
        fichier_configuration_ini['project_information']['sub_category_code'] = sub_category_code_var.get()
        fichier_configuration_ini['project_information']['billing_action'] = billing_action_var.get()

        # Sauvegarder dans le fichier config.ini
        write_config_ini(fichier_configuration_ini, log_file=log_file_var)
    
        # Fermer la fenêtre de configuration et revenir au menu principal
        main_configuration.destroy()
        main_menu(cle_aes, log_file=log_file_var)
    except IOError as e:
        messagebox.showerror("Erreur", f"Impossible de sauvegarder la configuration : {e}")

# ----------------------------------------------------------------------------- #
# --------------------- CODE PRINCIPALE --------------------------------------- #
# ----------------------------------------------------------------------------- #
def start_configuration(cle_aes, log_file):
    # Initialisation de la configuration
    config_ini = read_config_ini(log_file)

    # Initialiser les sections avec les valeurs par défaut
    check_and_initialize_section(config_ini, 'credentials', DEFAULT_CREDENTIALS)
    check_and_initialize_section(config_ini, 'settings', DEFAULT_SETTINGS)
    check_and_initialize_section(config_ini, 'work_schedule', DEFAULT_WORK_SCHEDULE)

    # Initialiser les sections additionnelles pour "Informations CGI"
    for section in ADDITIONAL_SECTIONS:
        check_and_initialize_section(config_ini, section, DEFAULT_WORK_SCHEDULE)

    # Section pour les Informations projet
    check_and_initialize_section(config_ini, 'project_information', DEFAULT_PROJECT_INFORMATION)

    # Initialiser les sections pour le lieu de travail matin et après-midi
    check_and_initialize_section(config_ini, 'work_location_am', DEFAULT_WORK_LOCATION_AM)
    check_and_initialize_section(config_ini, 'work_location_pm', DEFAULT_WORK_LOCATION_PM)

    # Création de la fenêtre principale 
    configuration = tk.Tk() # chargement du contexte principale
    configuration.title("Configuration du lancement")
    configuration.geometry("850x650") #Largueur x Hauteur
    configuration.minsize(850, 650)
    configuration.configure(background=COLORS['background'])

    # Configuration du style APRÈS la création de configuration
    setup_modern_style(configuration, COLORS)

    # Création des onglets 
    notebook = ttk.Notebook(configuration, style='Modern.TNotebook')
    notebook.pack(expand=True, fill='both', padx=20, pady=20)

    # ----------------------------------------------------------------------------- #
    # -------------------------- ONGLET PARAMETRES ------------------------------ #
    # ----------------------------------------------------------------------------- #
    settings_frame = create_tab(notebook, title="Paramètres")

    # Création d'un conteneur principal avec deux colonnes : Paramètres / Notes
    main_container = create_a_frame(settings_frame, padx=10, pady=10)

    #---------------------------------------------#
    #-- Colonne gauche pour l'onglet paramètres --#
    left_frame = create_labeled_frame(main_container, side='left', text="Paramètres:", padx=(0, 20))

    # Variables
    date_cible_var = create_structured_StringVar(config_ini, 'settings', 'date_cible')
    debug_mode_var = create_structured_StringVar(config_ini, 'settings', 'debug_mode')
    # Sousmettre_mode_var = create_structured_BooleanVar(config_ini, 'settings', 'soumettre_mode')

    # Container pour les champs de saisie ou cocher/decocher
    fields_container = create_a_frame(left_frame, padding=(15, 5, 15, 15))

    # Date cible
    # date_label_frame = create_a_frame(fields_container, fill="x", expand=False, pady=(0, 15))
    # date_entry = create_Modern_label_with_pack(date_label_frame, text="Date cible (jj/mm/aaaa):", side='left', padx=5) # on cree une variable pour le focus
    # date_entry = create_Modern_entry_with_pack(date_label_frame, date_cible_var, side='left', padx=5)
    # Date cible avec un calendrier interactif
    add_date_picker(fields_container, date_cible_var)
    
    # Mode debug
    debug_frame = create_a_frame(fields_container, fill="x", expand=False, pady=(0, 10))
    create_Modern_label_with_pack(debug_frame, text="Log Level:", side='left', padx=5)
    create_combobox_with_pack(debug_frame, debug_mode_var, values=LOG_LEVELS_CHOICES, side='left')
    # create_Modern_checkbox_with_pack(debug_frame, debug_mode_var, side="left", padx=5)
    
    # Mode Soumettre directement -- > todo
    # debug_frame = ttk.Frame(fields_container, style='Modern.TFrame')
    # debug_frame.pack(fill='x', pady=(0, 10))
    # ttk.Label(debug_frame, text="Mode Soumettre:", style='Modern.TLabel').pack(side='left', padx=5)
    # ttk.Checkbutton(debug_frame, variable=Sousmettre_mode_var, style='Modern.TCheckbutton').pack(side='left', padx=5)

    #---------------------------------------------#
    #-- Colonne droite pour l'onglet paramètres --#
    right_frame = create_labeled_frame(main_container, text="Notes:", side='right', padx=(0, 20))

    # les notes
    notes_text = tk.Text(right_frame,
                        wrap='word',
                        font=('Segoe UI', 9),
                        background=COLORS['light_yellow'],
                        relief='flat',
                        height=10,
                        padx=10,
                        pady=10)
    notes_text.pack(fill='both', expand=True)

    notes_text.insert('1.0',
                        "Gestion de la Date : \n" 
                        "  - La date peut être 'vide' ou 'None'.\n"
                        "  - Si, c'est 'vide' ou 'None',\n"
                        "    l'outil sélectionnera le prochain samedi comme date.\n"
                        "  - Si nous sommes un samedi, il garde ce jour.\n\n"
                        "Gestion du fichier config.ini : \n"
                        "  - Vous pouvez directemennt le modifier\n"
                        "    sans passer par la configuration\n\n"
                        "Si vous êtes en mission :\n"
                        "  - dans l'onglet : 'Planning de travail'\n"
                        "  - selectionner : 'En mission'\n"
                        "    un nouveau cadre apparaît afin de remplir,\n"
                        "    les informations de la mission.\n")
    notes_text.config(state='disabled')

    # ----------------------------------------------------------------------------- #
    # ---------------------- ONGLET PLANNING DE TRAVAIL --------------------------- #
    # ----------------------------------------------------------------------------- #
    work_schedule_frame = create_tab(notebook, title="Planning de travail")

    # En-têtes
    create_Title_label_with_grid(work_schedule_frame, text=f"Jour", row=0, col=0, padx=5, pady=10, sticky=None)
    create_Title_label_with_grid(work_schedule_frame, text=f"Description", row=0, col=1, padx=5, pady=10, sticky=None)
    create_Title_label_with_grid(work_schedule_frame, text=f"Heures travaillées", row=0, col=2, padx=5, pady=10, sticky=None)

    work_schedule_vars = {} # Liste pour stocker les descriptions de tous les jours
    active_mission_days = []  # Contient les jours ayant "En mission"
    
    # Création d'un cadre pour les informations de mission
    mission_frame = ttk.LabelFrame(work_schedule_frame, text="Informations de mission", style='Parametres.TLabelframe')
    mission_frame.grid(row=1, column=3, rowspan=len(JOURS_SEMAINE__LIST), padx=10, pady=10, sticky='n')
    mission_frame.grid_remove()  # Masqué par défaut
    
    # Variables pour les champs d'information de la mission
    project_code_var        = create_structured_StringVar(config_ini, 'project_information', 'project_code')
    activity_code_var       = create_structured_StringVar(config_ini, 'project_information', 'activity_code')
    category_code_var       = create_structured_StringVar(config_ini, 'project_information', 'category_code')
    sub_category_code_var   = create_structured_StringVar(config_ini, 'project_information', 'sub_category_code')
    billing_action_var      = create_structured_StringVar(config_ini, 'project_information', 'billing_action')

    # Champs pour les informations de mission
    create_Modern_label_with_grid(mission_frame, text=f"Project Code:", row=0, col=0, padx=5, pady=5)
    create_Modern_entry_with_grid(mission_frame, project_code_var, row=0, col=1, padx=5, pady=5)
    create_Modern_label_with_grid(mission_frame, text=f"Activity Code:", row=1, col=0, padx=5, pady=5)
    create_Modern_entry_with_grid(mission_frame, activity_code_var, row=1, col=1, padx=5, pady=5)
    create_Modern_label_with_grid(mission_frame, text=f"Category Code:", row=2, col=0, padx=5, pady=5)
    create_Modern_entry_with_grid(mission_frame, category_code_var, row=2, col=1, padx=5, pady=5)
    create_Modern_label_with_grid(mission_frame, text=f"Sub Category Code:", row=3, col=0, padx=5, pady=5)
    create_Modern_entry_with_grid(mission_frame, sub_category_code_var, row=3, col=1, padx=5, pady=5)
    create_Modern_label_with_grid(mission_frame, text=f"Billing Action:", row=4, col=0, padx=5, pady=5)
    create_combobox(mission_frame, billing_action_var, values=BILLING_ACTIONS_CHOICES, row=4, col=1, width=17, padx=5, pady=5)


    for i, day in enumerate(JOURS_SEMAINE__LIST, start=1):
        create_Modern_label_with_grid(work_schedule_frame, text=day.capitalize(), row=i, col=0, padx=5, pady=8)

        desc_var = create_structured_StringVar(config_ini, 'work_schedule', day, index=0)
        desc_combo = create_combobox(work_schedule_frame, var=desc_var, values=work_schedule_options, row=i, col=1, width=30)

        hours_value = ','.join(config_ini['work_schedule'].get(day, '').split(',')[1:])
        hours_var = create_basic_StringVar(hours_value)
        create_Modern_entry_with_grid(work_schedule_frame, var=hours_var, row=i, col=2, padx=5, pady=8)

        work_schedule_vars[day] = (desc_var, hours_var)
        
        # Attacher l'événement pour la recherche dynamique
        desc_combo.bind('<Return>', 
                        lambda event, combo=desc_combo, values=work_schedule_options: 
                        filter_combobox_on_enter(event, combo, values))

        # Vérifier si la valeur initiale est "En mission" pour afficher le cadre
        if desc_var.get() == "En mission":
            if day not in active_mission_days:
                active_mission_days.append(day)

        # Appeler `attach_event` pour chaque combobox masqué / demasqué l'encadrer Mission
        attach_event(desc_combo, day, mission_frame, active_mission_days)  

    # Vérifier l'état initial du cadre des informations de mission
    update_mission_frame_visibility(mission_frame, active_mission_days)
    
    # ----------------------------------------------------------------------------- #
    # ---------------------- ONGLET INFORMATIONS CGI ------------------------------ #
    # ----------------------------------------------------------------------------- #
    additional_info_frame = create_tab(notebook, title="Informations CGI")

    # En-têtes
    create_Title_label_with_grid(additional_info_frame, text=f"Jour", row=0, col=0, padx=5, pady=10, sticky=None)
    
    for col, section in enumerate(ADDITIONAL_SECTIONS, start=1):
        section_name = ADDITIONAL_SECTION_LABELS[section]
        create_Title_label_with_grid(additional_info_frame, text=section_name, row=0, col=col, padx=5, pady=10, sticky=None)

    additional_info_vars = {}
    for i, day in enumerate(JOURS_SEMAINE__LIST, start=1):
        create_Modern_label_with_grid(additional_info_frame, text=day.capitalize(), row=i, col=0, padx=5, pady=8)
        
        additional_info_vars[day] = {}

        for col, section in enumerate(ADDITIONAL_SECTIONS, start=1):
            var = create_structured_StringVar(config_ini, section, day)
            if section == "additional_information_lunch_break_duration":
                create_combobox(additional_info_frame, var, values=cgi_options_dejeuner, row=i, col=col, state="readonly", padx=5, pady=5)
            else:
                create_combobox(additional_info_frame, var, values=cgi_options, row=i, col=col, state="readonly", padx=5, pady=5)
            
            additional_info_vars[day][section] = var

    # ----------------------------------------------------------------------------- #
    # ---------------------- ONGLET LIEU DE TRAVAIL ------------------------------- #
    # ----------------------------------------------------------------------------- #
    work_location_frame = create_tab(notebook, title="Lieu de travail")

    # En-têtes
    create_Title_label_with_grid(work_location_frame, text=f"Jour", row=0, col=0, padx=5, pady=10, sticky=None)
    create_Title_label_with_grid(work_location_frame, text=f"Matin", row=0, col=1, padx=5, pady=10, sticky=None)
    create_Title_label_with_grid(work_location_frame, text=f"Après-midi", row=0, col=2, padx=5, pady=10, sticky=None)

    work_location_vars = {}

    for i, day in enumerate(JOURS_SEMAINE__LIST, start=1):
        create_Modern_label_with_grid(work_location_frame, text=day.capitalize(), row=i, col=0, padx=5, pady=8)
        
        morning_var = create_structured_StringVar(config_ini, 'work_location_am', day)
        afternoon_var = create_structured_StringVar(config_ini, 'work_location_pm', day)
        create_combobox(work_location_frame, morning_var, work_location_options, row=i, col=1, state="readonly")
        create_combobox(work_location_frame, afternoon_var, work_location_options, row=i, col=2, state="readonly")

        work_location_vars[day] = (morning_var, afternoon_var)

    # ----------------------------------------------------------------------------- #
    # -------------------------- BOUTON SAUVEGARDER ------------------------------- #
    # ----------------------------------------------------------------------------- #
    button_frame = create_a_frame(configuration, side=tk.BOTTOM, pady=20)
    
    elements_to_save_it = [
                        config_ini, date_cible_var, debug_mode_var, work_schedule_vars,
                        additional_info_vars, work_location_vars, configuration, cle_aes,
                        project_code_var, activity_code_var, category_code_var, 
                        sub_category_code_var, billing_action_var, log_file
                        ]
    
    save_button = create_button_with_style(button_frame, text="Sauvegarder", command=lambda: save_config(elements_to_save_it))
    # Lier la touche Entrée au bouton
    save_button.bind("<Return>", lambda event: save_button.invoke())                    

    # Focus initial sur le champ parametre
    date_entry = settings_frame.winfo_children()[-1]
    date_entry.focus()

    # Lancement de l'interface
    configuration.mainloop()

# ----------------------------------------------------------------------------- #
# -------------------------- MENU DE DEMARRAGE -------------------------------- #
# ----------------------------------------------------------------------------- #
def main_menu(cle_aes, log_file):
    global menu
    menu = tk.Tk()
    menu.title("Program PSATime Auto")
    # Désactiver le redimensionnement (largeur et hauteur)
    menu.resizable(False, False)
    menu.geometry("400x300")
    login_var = create_basic_StringVar("")
    mdp_var = create_basic_StringVar("")
    
    # Titre principal
    tk.Label(menu, text="Program PSATime Auto", font=("Segoe UI", 14)).pack(pady=10)
    
    # Champs d'identifiants
    credentials_frame = create_labeled_frame(menu, text="Identifiants", padx=20, pady=10, padding=(10, 5))
    
    # pour le login
    create_Modern_label_with_grid(credentials_frame, text=f"Login:", row=0, col=0)
    login_entry = create_Modern_entry_with_grid(credentials_frame, var=login_var, row=0, col=1)
    create_Modern_label_with_grid(credentials_frame, text=f"@cgi.com", row=0, col=2)

    # pour le mot de passe
    create_Modern_label_with_grid(credentials_frame, text=f"Mot de passe:", row=1, col=0)
    create_Modern_entry_with_grid_for_password(credentials_frame, var=mdp_var, row=1, col=1)
    
    # menu : Lancer votre PSATime
    launch_button = create_button_without_style(menu, text="Lancer votre PSATime", command=lambda: run_psatime(log_file))
    # Lier la touche Entrée au bouton
    launch_button.bind("<Return>", lambda event: launch_button.invoke())
    
    # menu : Configurer le lancement
    config_button = create_button_without_style(menu, text="Configurer le lancement", command=lambda: [menu.destroy(), start_configuration(cle_aes, log_file)])
    # Lier la touche Entrée au bouton
    config_button.bind("<Return>", lambda event: config_button.invoke())


    # Signature en bas à droite                     
    color_grey = "grey"
    color_bleu_acier_doux ="#5f6a73"  # Bleu acier doux
    color_bleu_clair ="#4b9cd3"  # Bleu clair
    police_segoe_script = "Segoe Script"
    police_lucida_calligraphy = "Lucida Calligraphy"
    
    seperator_ttk(menu, orient='horizontal', fill='x', padx=10, pady=5)

    signature_label = tk.Label(menu, text="Développé par Frédéric",
                            font=(police_lucida_calligraphy, 8, "italic"), fg=color_bleu_acier_doux)
    signature_label.pack(fill='x', padx=20, pady=5, ipady=5)

    # Mise à jour de la commande du bouton "Lancer votre PSATime" afin de prendre en compte les login et mdp
    launch_button.config(command=lambda: run_psatime_with_credentials(cle_aes, login_var, mdp_var, log_file))

    # Focus initial sur le champ login
    login_entry.focus()
    
    menu.mainloop()
    
    # Garder le script actif pour permettre au second script de s'exécuter si besoin
    time.sleep(10)

if __name__ == "__main__":
    log_file = get_log_file() # Initialiser le fichier de log
    write_log(f"🚦 Initialisation du programme.", log_file, "INFO")
    write_log(f"🔍 Chemin du fichier log : {log_file}", log_file, "INFO")
    
    # Charger la configuration et Initialiser le niveau de log à partir de la configuration
    config = read_config_ini(log_file) 
    initialize_logger(config) 
    write_log(f"🔹 Niveau de Log initialisée avec succès.", log_file, "INFO")
    
    # contouner un probléme avec Pyinstaller et les multi processus
    multiprocessing.freeze_support()
    
    try: 
        # Lancer le programme principal
        write_log(f"📌 Démarrage du programme", log_file, "INFO")
        cle_aes = generer_cle_aes(TAILLE_CLE, log_file=log_file)
        main_menu(cle_aes, log_file=log_file)
        write_log(f"✅ Toutes les tâches ont été effectuées.", log_file, "INFO")
    except Exception as e:
        write_log(f"Erreur rencontrée : {str(e)}", log_file, "ERROR")
    finally:
        close_logs(log_file=log_file)
