# main.py
# pyinstaller --onefile --add-data "config.ini;." --hidden-import "saisie_automatiser_psatime" --hidden-import "encryption_utils" --hidden-import "cryptography.hazmat.bindings._rust" --hidden-import "cryptography.hazmat.primitives.ciphers" --hidden-import "cryptography.hazmat.primitives.padding" main.py 

# Import des bibliothèques nécessaires
import configparser
import multiprocessing
import tkinter as tk
from tkinter import ttk, messagebox, StringVar
import re
import time
import subprocess
import sys
import os
from dropdown_options import work_location_options, cgi_options, cgi_options_dejeuner ,work_schedule_options
from encryption_utils import generer_cle_aes, chiffrer_donnees, stocker_en_memoire_partagee
from encryption_utils import supprimer_memoire_partagee_securisee
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from multiprocessing import shared_memory
from read_or_write_file_config_ini import get_runtime_config_path, read_config_ini, write_config_ini
# ----------------------------------------------------------------------------- #
# ------------------------------- CONSTANTE ----------------------------------- #
# ----------------------------------------------------------------------------- #
# # Fichier de configuration
# CONFIG_FILE = 'config.ini'

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

# Correspondances entre les noms affichés et les noms dans config.ini
ADDITIONAL_SECTION_LABELS = {
    'additional_information_rest_period_respected': 'période repos respectée',
    'additional_information_work_time_range': 'plage horaire travail',
    'additional_information_half_day_worked': 'demi-journée travaillée',
    'additional_information_lunch_break_duration': 'durée pause déjeuner'
}

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
# ------------------------------- FONCTIONS ------------------------------------ #
# ----------------------------------------------------------------------------- #
def run_psatime_with_credentials(cle_aes, login_var, mdp_var):
    try:
        login = login_var.get()
        password = mdp_var.get()
        
        # Chiffrer les informations
        nom_utilisateur_chiffre = chiffrer_donnees(login, cle_aes)
        mot_de_passe_chiffre = chiffrer_donnees(password, cle_aes)
        memoire_cle = stocker_en_memoire_partagee(MEMOIRE_PARTAGEE_CLE, cle_aes)
        # print(f"Taille des données chiffrées du nom d'utilisateur : {len(nom_utilisateur_chiffre)}")
        # print(f"Taille des données chiffrées du mot de passe : {len(mot_de_passe_chiffre)}")
        
        if not login or not password:
            messagebox.showerror("Erreur", "Veuillez entrer votre login et mot de passe.")
            return None

        memoire_nom = shared_memory.SharedMemory(name="memoire_nom", create=True, size=len(nom_utilisateur_chiffre))
        memoire_nom.buf[:len(nom_utilisateur_chiffre)] = nom_utilisateur_chiffre

        memoire_mdp = shared_memory.SharedMemory(name="memoire_mdp", create=True, size=len(mot_de_passe_chiffre))
        memoire_mdp.buf[:len(mot_de_passe_chiffre)] = mot_de_passe_chiffre

        # print(f"Clé et données chiffrées stockées dans la mémoire partagée.")
        print(f"Lancement de PSATime avec login: {login}@cgi.com et mot de passe.")

        run_psatime()
    except Exception as e:
        raise print(f"Erreur : {e}")
    else:
        # Suppression sécurisée
        time.sleep(DUREE_DE_VIE_CLE)
        if memoire_nom is not None:
            supprimer_memoire_partagee_securisee(memoire_nom)
        if memoire_mdp is not None:
            supprimer_memoire_partagee_securisee(memoire_mdp)
    finally:
        # Suppression sécurisée
        time.sleep(DUREE_DE_VIE_CLE)
        # Suppression sécurisée des mémoires partagées
        supprimer_memoire_partagee_securisee(memoire_cle)
        print("[FIN] Clé et données supprimées de manière sécurisée, des mémoires partagées du fichier main.")

def run_psatime():
    # Fermez la fenêtre graphique
    menu.destroy()
    # Lancez le script `saisie_automatiser_psatime.py`
    # print("Lancement de saisie_automatiser_psatime.py avec le chemin du fichier temporaire.")
    # subprocess.Popen(["python", "-Xfrozen_modules=off", "saisie_automatiser_psatime.py", temp_file_path])
    # subprocess.Popen(["python", "-Xfrozen_modules=off", "saisie_automatiser_psatime.py"])
    # memoire_cle, memoire_mdp, memoire_nom = subprocess.Popen([sys.executable, "-Xfrozen_modules=off", saisie_automatiser_psatime.main()])
    print("Lancement de la fonction main de saisie_automatiser_psatime.py")
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

# Vérification de l'existence des sections et ajout de valeurs par défaut si elles sont manquantes
def check_and_initialize_section(configuration, section, defaults):
    if not configuration.has_section(section):
        configuration.add_section(section)
    for key, value in defaults.items():
        if not configuration.has_option(section, key):
            configuration.set(section, key, value)

# Fonction pour valider le formet de la date avant la sauvegarde
def validate_data(date):
    date_cible = date.get()

    # Validation du format de date cible
    date_pattern = re.compile(r'^\d{2}/\d{2}/\d{4}$')
    if date_cible and not date_pattern.match(date_cible):
        messagebox.showerror("Erreur", "La date cible doit être au format jj/mm/aaaa")
        return False

    return True

# Fonction pour sauvegarder les modifications dans config.ini
def save_config(fichier_configuration_ini, date_cible, debug_mode, work_schedule, additional_info, work_location, main_configuration, cle_aes):
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

        # # Sauvegarder dans le fichier config.ini
        # write_config_ini(CONFIG_FILE, fichier_configuration_ini)
        # Sauvegarder dans le fichier config.ini
        write_config_ini(fichier_configuration_ini)
    
        # Fermer la fenêtre de configuration et revenir au menu principal
        main_configuration.destroy()
        main_menu(cle_aes)
    except IOError as e:
        messagebox.showerror("Erreur", f"Impossible de sauvegarder la configuration : {e}")

# ----------------------------------------------------------------------------- #
# --------------------- CODE PRINCIPALE --------------------------------------- #
# ----------------------------------------------------------------------------- #
def start_configuration(cle_aes):
    # # Initialisation de la configuration
    # config_ini = read_config_ini(CONFIG_FILE)
    # Initialisation de la configuration
    config_ini = read_config_ini()

    # Initialiser les sections avec les valeurs par défaut
    check_and_initialize_section(config_ini, 'credentials', DEFAULT_CREDENTIALS)
    check_and_initialize_section(config_ini, 'settings', DEFAULT_SETTINGS)
    check_and_initialize_section(config_ini, 'work_schedule', DEFAULT_WORK_SCHEDULE)

    # Initialiser les sections additionnelles pour "Informations CGI"
    for section in ADDITIONAL_SECTIONS:
        check_and_initialize_section(config_ini, section, DEFAULT_WORK_SCHEDULE)

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
    settings_frame = ttk.Frame(notebook, style='Modern.TFrame', padding=20)
    notebook.add(settings_frame, text="Paramètres")

    # Création d'un conteneur principal avec deux colonnes : Paramètres / Notes
    main_container = ttk.Frame(settings_frame, style='Modern.TFrame')
    main_container.pack(fill='both', expand=True, padx=10, pady=10)

    #---------------------------------------------#
    #-- Colonne gauche pour l'onglet paramètres --#
    left_frame = ttk.LabelFrame(main_container, text="Paramètres:", style='Parametres.TLabelframe')
    left_frame.pack(side='left', fill='both', expand=True, padx=(0, 20), pady=0)

    # Variables
    date_cible_var = tk.StringVar(value=config_ini['settings'].get('date_cible', ''))
    debug_mode_var = tk.BooleanVar(value=config_ini['settings'].getboolean('debug_mode', False))
    # Sousmettre_mode_var = tk.BooleanVar(value=config_ini['settings'].getboolean('debug_mode', False))

    # Container pour les champs de saisie ou cocher/decocher
    fields_container = ttk.Frame(left_frame, style='Modern.TFrame', padding=(15, 5, 15, 15))
    fields_container.pack(fill='both', expand=True)

    # Date cible
    date_label_frame = ttk.Frame(fields_container, style='Modern.TFrame')
    date_label_frame.pack(fill='x', pady=(0, 15))
    date_entry = ttk.Label(date_label_frame, text="Date cible (jj/mm/aaaa):", style='Modern.TLabel').pack(side='left', padx=5)
    date_entry = ttk.Entry(date_label_frame, textvariable=date_cible_var, width=20,style='Settings.TEntry').pack(side='left', padx=5)

    # Mode debug
    debug_frame = ttk.Frame(fields_container, style='Modern.TFrame')
    debug_frame.pack(fill='x', pady=(0, 10))
    ttk.Label(debug_frame, text="Mode Debug:", style='Modern.TLabel').pack(side='left', padx=5)
    ttk.Checkbutton(debug_frame, variable=debug_mode_var, style='Modern.TCheckbutton').pack(side='left', padx=5)
    
    # Mode Soumettre directement -- > todo
    # debug_frame = ttk.Frame(fields_container, style='Modern.TFrame')
    # debug_frame.pack(fill='x', pady=(0, 10))
    # ttk.Label(debug_frame, text="Mode Soumettre:", style='Modern.TLabel').pack(side='left', padx=5)
    # ttk.Checkbutton(debug_frame, variable=Sousmettre_mode_var, style='Modern.TCheckbutton').pack(side='left', padx=5)

    #---------------------------------------------#
    #-- Colonne droite pour l'onglet paramètres --#
    right_frame = ttk.LabelFrame(main_container, text="Notes:", style='Parametres.TLabelframe')
    right_frame.pack(side='right', fill='both', expand=True, padx=(0, 20), pady=0)

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
                        "- La date peut être vide ou 'None'.\n"
                        "- Si, c'est vide ou 'None',\n"
                        "L'outil sélectionnera automatiquement\n"
                        "le prochain samedi comme date. Si\n"
                        "nous sommes un samedi, il garde ce jour.\n\n"
                        "Vous pouvez aussi modifier\n"
                        "directement le fichier config.ini")
    notes_text.config(state='disabled')

    # ----------------------------------------------------------------------------- #
    # ---------------------- ONGLET PLANNING DE TRAVAIL ------------------------- #
    # ----------------------------------------------------------------------------- #
    work_schedule_frame = ttk.Frame(notebook, style='Modern.TFrame', padding=20)
    notebook.add(work_schedule_frame, text="Planning de travail")

    # En-têtes
    ttk.Label(work_schedule_frame, text="Jour", style='Title.TLabel').grid(row=0, column=0, padx=5, pady=10)
    ttk.Label(work_schedule_frame, text="Description", style='Title.TLabel').grid(row=0, column=1, padx=5, pady=10)
    ttk.Label(work_schedule_frame, text="Heures travaillées", style='Title.TLabel').grid(row=0, column=2, padx=5, pady=10)

    work_schedule_vars = {}

    for i, day in enumerate(JOURS_SEMAINE__LIST, start=1):
        ttk.Label(work_schedule_frame, text=day.capitalize(), style='Modern.TLabel').grid(row=i, column=0, padx=5, pady=8, sticky='w')
        
        desc_var = StringVar(value=config_ini['work_schedule'].get(day, '').split(',')[0])
        desc_combo = ttk.Combobox(work_schedule_frame, 
                                textvariable=desc_var, 
                                values=work_schedule_options, 
                                state="normal", 
                                width=30,
                                style='Modern.TCombobox')
        desc_combo.grid(row=i, column=1, padx=5, pady=8)
        
        # Attacher l'événement pour la recherche dynamique
        desc_combo.bind('<Return>', lambda event, combo=desc_combo, values=work_schedule_options: filter_combobox_on_enter(event, combo, values))

        hours_value = ','.join(config_ini['work_schedule'].get(day, '').split(',')[1:])
        hours_var = tk.StringVar(value=hours_value)
        hours_entry = ttk.Entry(work_schedule_frame, 
                            textvariable=hours_var, 
                            width=15,
                            style='Modern.TEntry')
        hours_entry.grid(row=i, column=2, padx=5, pady=8)

        work_schedule_vars[day] = (desc_var, hours_var)

    # ----------------------------------------------------------------------------- #
    # ---------------------- ONGLET INFORMATIONS CGI ---------------------------- #
    # ----------------------------------------------------------------------------- #
    additional_info_frame = ttk.Frame(notebook, style='Modern.TFrame', padding=20)
    notebook.add(additional_info_frame, text="Informations CGI")

    # En-têtes
    ttk.Label(additional_info_frame, text="Jour", style='Title.TLabel').grid(row=0, column=0, padx=5, pady=10)
    for col, section in enumerate(ADDITIONAL_SECTIONS, start=1):
        section_name = ADDITIONAL_SECTION_LABELS[section]
        ttk.Label(additional_info_frame, text=section_name, style='Title.TLabel').grid(row=0, column=col, padx=5, pady=10)

    additional_info_vars = {}
    for i, day in enumerate(JOURS_SEMAINE__LIST, start=1):
        ttk.Label(additional_info_frame, text=day.capitalize(), style='Modern.TLabel').grid(row=i, column=0, padx=5, pady=8, sticky='w')
        additional_info_vars[day] = {}

        for col, section in enumerate(ADDITIONAL_SECTIONS, start=1):
            var = StringVar(value=config_ini[section].get(day, ''))
            if section == "additional_information_lunch_break_duration":
                combo = ttk.Combobox(additional_info_frame, 
                    textvariable=var, 
                    values=cgi_options_dejeuner, 
                    state="readonly", 
                    width=20,
                    style='Modern.TCombobox')
            else:
                combo = ttk.Combobox(additional_info_frame, 
                                    textvariable=var, 
                                    values=cgi_options, 
                                    state="readonly", 
                                    width=20,
                                    style='Modern.TCombobox')
            combo.grid(row=i, column=col, padx=5, pady=8)
            additional_info_vars[day][section] = var

    # ----------------------------------------------------------------------------- #
    # ---------------------- ONGLET LIEU DE TRAVAIL ------------------------------- #
    # ----------------------------------------------------------------------------- #
    work_location_frame = ttk.Frame(notebook, style='Modern.TFrame', padding=20)
    notebook.add(work_location_frame, text="Lieu de travail")

    # En-têtes
    ttk.Label(work_location_frame, text="Jour", style='Title.TLabel').grid(row=0, column=0, padx=5, pady=10)
    ttk.Label(work_location_frame, text="Matin", style='Title.TLabel').grid(row=0, column=1, padx=5, pady=10)
    ttk.Label(work_location_frame, text="Après-midi", style='Title.TLabel').grid(row=0, column=2, padx=5, pady=10)

    work_location_vars = {}

    for i, day in enumerate(JOURS_SEMAINE__LIST, start=1):
        ttk.Label(work_location_frame, text=day.capitalize(), style='Modern.TLabel').grid(row=i, column=0, padx=5, pady=8, sticky='w')
        
        morning_var = StringVar(value=config_ini['work_location_am'].get(day, ''))
        afternoon_var = StringVar(value=config_ini['work_location_pm'].get(day, ''))

        morning_combo = ttk.Combobox(work_location_frame, 
                                    textvariable=morning_var, 
                                    values=work_location_options, 
                                    state="readonly", 
                                    width=20,
                                    style='Modern.TCombobox')
        morning_combo.grid(row=i, column=1, padx=5, pady=8)

        afternoon_combo = ttk.Combobox(work_location_frame, 
                                    textvariable=afternoon_var, 
                                    values=work_location_options, 
                                    state="readonly", 
                                    width=20,
                                    style='Modern.TCombobox')
        afternoon_combo.grid(row=i, column=2, padx=5, pady=8)

        work_location_vars[day] = (morning_var, afternoon_var)

    # ----------------------------------------------------------------------------- #
    # -------------------------- BOUTON SAUVEGARDER ------------------------------- #
    # ----------------------------------------------------------------------------- #
    button_frame = ttk.Frame(configuration, style='Modern.TFrame')
    button_frame.pack(side=tk.BOTTOM, pady=20)

    save_button = ttk.Button(button_frame, 
                            text="Sauvegarder", 
                            style='Modern.TButton',
                            command=lambda: save_config(config_ini, date_cible_var, debug_mode_var,
                                                     work_schedule_vars, additional_info_vars, work_location_vars, configuration, cle_aes))
    save_button.pack()

    # Focus initial sur le champ parametre
    date_entry = settings_frame.winfo_children()[-1]
    date_entry.focus()

    # Lancement de l'interface
    configuration.mainloop()

# ----------------------------------------------------------------------------- #
# -------------------------- MENU DE DEMARRAGE -------------------------------- #
# ----------------------------------------------------------------------------- #
def main_menu(cle_aes):
    global menu
    menu = tk.Tk()
    menu.title("Program PSATime Auto")
    # Désactiver le redimensionnement (largeur et hauteur)
    menu.resizable(False, False)
    menu.geometry("400x300")
    login_var = tk.StringVar(value="")  # Valeur par défaut
    mdp_var = tk.StringVar(value="")
    
    # Titre principal
    tk.Label(menu, text="Program PSATime Auto", font=("Segoe UI", 14)).pack(pady=10)
    
    # # Séparateur
    # separator = ttk.Separator(menu, orient='horizontal')
    # separator.pack(fill='x', pady=10)
    
    # Champs d'identifiants
    credentials_frame = ttk.LabelFrame(menu, text="Identifiants", style='Parametres.TLabelframe', padding=(10, 5))
    credentials_frame.pack(fill='both', expand=True, padx=20, pady=10)

    # pour le login
    ttk.Label(credentials_frame, text="Login:", style='Modern.TLabel').grid(row=0, column=0, sticky='w', padx=5, pady=5)
    login_entry = ttk.Entry(credentials_frame, textvariable=login_var, width=30, style='Modern.TEntry')
    login_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
    ttk.Label(credentials_frame, text="@cgi.com", style='Modern.TLabel').grid(row=0, column=2, sticky='w', padx=5, pady=5)

    # pour le mot de passe
    ttk.Label(credentials_frame, text="Mot de passe:", style='Modern.TLabel').grid(row=1, column=0, sticky='w', padx=5, pady=5)
    mdp_entry = ttk.Entry(credentials_frame, textvariable=mdp_var, show='*', width=30, style='Modern.TEntry')
    mdp_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
    
    # menu : Lancer votre PSATime
    launch_button = tk.Button(menu, text="Lancer votre PSATime", command=lambda: run_psatime())
    launch_button.pack(fill='x', padx=20, pady=5, ipady=5)
    # menu : Configurer le lancement
    config_button = tk.Button(menu, text="Configurer le lancement", command=lambda: [menu.destroy(), start_configuration(cle_aes)])
    config_button.pack(fill='x', padx=20, pady=5, ipady=5)
    
    # Signature en bas à droite
    color_grey = "grey"
    color_bleu_acier_doux ="#5f6a73"  # Bleu acier doux
    color_bleu_clair ="#4b9cd3"  # Bleu clair
    police_segoe_script = "Segoe Script"
    police_lucida_calligraphy = "Lucida Calligraphy"
    separator = ttk.Separator(menu, orient='horizontal')
    separator.pack(fill='x', padx=10, pady=5)

    signature_label = tk.Label(menu, text="Développé par Frédéric",
                            font=(police_lucida_calligraphy, 8, "italic"), fg=color_bleu_acier_doux)
    signature_label.pack(fill='x', padx=20, pady=5, ipady=5)

    # Mise à jour de la commande du bouton "Lancer votre PSATime" afin de prendre en compte les login et mdp
    launch_button.config(command=lambda: run_psatime_with_credentials(cle_aes, login_var, mdp_var))

    # Focus initial sur le champ login
    login_entry.focus()
    
    menu.mainloop()
    
    # Garder le script actif pour permettre au second script de s'exécuter si besoin
    time.sleep(10)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    try: 
        # Générer une clé AES-256
        cle_aes = generer_cle_aes(TAILLE_CLE)
        # print(f"Clé AES-256 générée : {cle_aes.hex()}")
        main_menu(cle_aes) # Lancer le menu principal
    except Exception as e:
        print(f"Erreur : {e}")
