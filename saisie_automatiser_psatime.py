# saisie_automatiser_psatime.py

# ----------------------------------------------------------------------------- #
# ---------------- Import des bibliothèques nécessaires ----------------------- #
# ----------------------------------------------------------------------------- #
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException, StaleElementReferenceException
from datetime import datetime, timedelta
import time
import sys
import os
from multiprocessing import shared_memory
from encryption_utils import recuperer_de_memoire_partagee, dechiffrer_donnees ,supprimer_memoire_partagee_securisee
from fonctions_selenium_utils import click_element_without_wait, controle_insertion, definir_taille_navigateur, detecter_doublons_jours
from fonctions_selenium_utils import detecter_et_verifier_contenu, effacer_et_entrer_valeur, modifier_date_input, ouvrir_navigateur_sur_ecran_principal
from fonctions_selenium_utils import remplir_champ_texte, selectionner_option_menu_deroulant_type_select, send_keys_to_element, switch_to_default_content
from fonctions_selenium_utils import switch_to_iframe_by_id_or_name, trouver_ligne_par_description, verifier_champ_jour_rempli, wait_for_dom_ready, wait_for_element, wait_until_dom_is_stable
from logger_utils import write_log
from read_or_write_file_config_ini_utils import read_config_ini
from remplir_informations_supp_utils import traiter_description
from dropdown_options import cgi_options_billing_action
import remplir_jours_feuille_de_temps
from shared_utils import get_log_file

# ----------------------------------------------------------------------------- #
# ------------------------------- CONSTANTE ----------------------------------- #
# ----------------------------------------------------------------------------- #

LOG_FILE = get_log_file()
config = read_config_ini(LOG_FILE)

# Extraction des informations de connexion
ENCRYPTED_LOGIN = config.get('credentials', 'login')
ENCRYPTED_MDP = config.get('credentials', 'mdp')

# Extraction des paramètres de base
URL = config.get('settings', 'url')
DATE_CIBLE = config.get('settings', 'date_cible')
if DATE_CIBLE.lower() == 'none' or DATE_CIBLE.strip() == '':
    DATE_CIBLE = None

# DEBUG_MODE = config.get('settings', 'debug_mode').lower() == 'true'
DEBUG_MODE = True

# Récupérer la liste, split, nettoie les espaces et les double quote
LISTE_ITEMS_DESCRIPTIONS = [item.strip().strip('"') for item in config.get('settings', 'liste_items_planning').split(",")]

# Configuration des jours de travail et congés
JOURS_DE_TRAVAIL = {day: (value.partition(',')[0].strip(), value.partition(',')[2].strip()) for day, value in config.items('work_schedule')}
INFORMATIONS_PROJET_MISSION = {
    item_projet: cgi_options_billing_action.get(value, value)  # Remplace si une correspondance existe
    for item_projet, value in config.items('project_information')
}
# Liste des IDs associés aux informations du projet
LISTES_ID_INFORMATIONS_MISSION = ["PROJECT_CODE$0", "ACTIVITY_CODE$0", "CATEGORY_CODE$0", "SUB_CATEGORY_CODE$0", "BILLING_ACTION$0"]

ID_TO_KEY_MAPPING = {
    "PROJECT_CODE$0": 'project_code',
    "ACTIVITY_CODE$0": 'activity_code',
    "CATEGORY_CODE$0": 'category_code',
    "SUB_CATEGORY_CODE$0": 'sub_category_code',
    "BILLING_ACTION$0": 'billing_action'
}

# Configuration pour les informations additionnelles CGI - France
INFORMATIONS_SUPPLEMENTAIRES_PERIODE_REPOS_RESPECTEE = {day: value for day, value in config.items('additional_information_rest_period_respected')}
INFORMATIONS_SUPPLEMENTAIRES_HORAIRE_TRAVAIL_EFFECTIF = {day: value for day, value in config.items('additional_information_work_time_range')}
INFORMATIONS_SUPPLEMENTAIRES_PLUS_DEMI_JOURNEE_TRAVAILLEE = {day: value for day, value in config.items('additional_information_half_day_worked')}
INFORMATIONS_SUPPLEMENTAIRES_DUREE_PAUSE_DEJEUNER = {day: value for day, value in config.items('additional_information_lunch_break_duration')}
# Configuration des lieux de travail pour chaque jour Matin et Après-midi
LIEU_DU_TRAVAIL_MATIN = {day: value for day, value in config.items('work_location_am')}
LIEU_DU_TRAVAIL_APRES_MIDI = {day: value for day, value in config.items('work_location_pm')}

DESCRIPTIONS = [
    {
        "description_cible": "Temps de repos de 11h entre 2 jours travaillés respecté",
        "id_value_ligne": "DESCR100$",  # Recherche de la ligne
        "id_value_jours": "UC_DAILYREST",  # Recherche des jours
        "type_element": "select",
        "valeurs_a_remplir": INFORMATIONS_SUPPLEMENTAIRES_PERIODE_REPOS_RESPECTEE
    },
    {
        "description_cible": "Mon temps de travail effectif a débuté entre 8h00 et 10h00 et Mon temps de travail effectif a pris fin entre 16h30 et 19h00",
        "id_value_ligne": "DESCR100$",
        "id_value_jours": "UC_DAILYREST",
        "type_element": "select",
        "valeurs_a_remplir": INFORMATIONS_SUPPLEMENTAIRES_HORAIRE_TRAVAIL_EFFECTIF
    },
    {
        "description_cible": "J’ai travaillé plus d’une demi-journée",
        "id_value_ligne": "DESCR100$",
        "id_value_jours": "UC_DAILYREST",
        "type_element": "select",
        "valeurs_a_remplir": INFORMATIONS_SUPPLEMENTAIRES_PLUS_DEMI_JOURNEE_TRAVAILLEE
    },
    {
        "description_cible": "Durée de la pause déjeuner",
        "id_value_ligne": "UC_TIME_LIN_WRK_DESCR200$",
        "id_value_jours": "UC_TIME_LIN_WRK_UC_DAILYREST",
        "type_element": "input",
        "valeurs_a_remplir": INFORMATIONS_SUPPLEMENTAIRES_DUREE_PAUSE_DEJEUNER
    },
    {
        "description_cible": "Matin",
        "id_value_ligne": "DESCR$",  
        "id_value_jours": "UC_LOCATION_A",
        "type_element": "select",
        "valeurs_a_remplir": LIEU_DU_TRAVAIL_MATIN
    },
    {
        "description_cible": "Après-midi",
        "id_value_ligne": "DESCR$",  
        "id_value_jours": "UC_LOCATION_A",
        "type_element": "select",
        "valeurs_a_remplir": LIEU_DU_TRAVAIL_APRES_MIDI
    }
]


if DEBUG_MODE:
    # Afficher les configurations chargées (facultatif, pour le debug)
    write_log(f"📌 Chargement des configurations...", LOG_FILE, "INFO")
    write_log(f"👉 Login : {ENCRYPTED_LOGIN} - pas visible, normal", LOG_FILE, "CRITICAL")
    write_log(f"👉 Password : {ENCRYPTED_MDP} - pas visible, normal", LOG_FILE, "CRITICAL")
    write_log(f"👉 URL : {URL}", LOG_FILE, "CRITICAL")
    write_log(f"👉 Date cible : {DATE_CIBLE}", LOG_FILE, "INFO")
    
    write_log(f"👉 Planning de travail de la semaine:", LOG_FILE, "INFO")
    for day, (activity, hours) in JOURS_DE_TRAVAIL.items():
        write_log(f"🔹 '{day}': ('{activity}', '{hours}')", LOG_FILE, "INFO")
        
    write_log(f"👉 Infos_supp_cgi_periode_repos_respectee:", LOG_FILE, "INFO")
    for day, status in INFORMATIONS_SUPPLEMENTAIRES_PERIODE_REPOS_RESPECTEE.items():
        write_log(f"🔹 '{day}': '{status}'", LOG_FILE, "INFO")
        
    write_log(f"👉 Infos_supp_cgi_horaire_travail_effectif:", LOG_FILE, "INFO")
    for day, status in INFORMATIONS_SUPPLEMENTAIRES_HORAIRE_TRAVAIL_EFFECTIF.items():
        write_log(f"🔹 '{day}': '{status}'", LOG_FILE, "INFO")
        
    write_log(f"👉 Planning de travail de la semaine:", LOG_FILE, "INFO")
    for day, status in INFORMATIONS_SUPPLEMENTAIRES_PLUS_DEMI_JOURNEE_TRAVAILLEE.items():
        write_log(f"🔹 '{day}': '{status}'", LOG_FILE, "INFO")
        
    write_log(f"👉 Infos_supp_cgi_duree_pause_dejeuner:", LOG_FILE, "INFO") 
    for day, status in INFORMATIONS_SUPPLEMENTAIRES_DUREE_PAUSE_DEJEUNER.items():
        write_log(f"🔹 '{day}': '{status}'", LOG_FILE, "INFO")
        
    write_log(f"👉 Lieu de travail Matin:", LOG_FILE, "INFO")
    for day, location in LIEU_DU_TRAVAIL_MATIN.items():
        write_log(f"🔹 '{day}': '{location}'", LOG_FILE, "INFO")
        
    write_log(f"👉 Lieu de travail Apres-midi:", LOG_FILE, "INFO")
    for day, location in LIEU_DU_TRAVAIL_APRES_MIDI.items():
        write_log(f"🔹 '{day}': '{location}'", LOG_FILE, "INFO")

CHOIX_USER = True # true pour créer une nouvelle feuille de temps
DEFAULT_TIMEOUT = 10  # Délai d'attente par défaut
LONG_TIMEOUT = 20
JOURS_SEMAINE = {
    1: "dimanche",
    2: "lundi",
    3: "mardi",
    4: "mercredi",
    5: "jeudi",
    6: "vendredi",
    7: "samedi"
}

# Configuration memoire partagée et cryptage
MEMOIRE_PARTAGEE_CLE = "memoire_partagee_cle"
MEMOIRE_PARTAGEE_DONNEES = "memoire_partagee_donnees"
TAILLE_CLE = 32  # 256 bits pour AES-256
TAILLE_BLOC = 128  # Taille de bloc AES pour le padding

# ------------------------------------------------------------------------------------------------- #
# ----------------------------------- FONCTIONS UTILS --------------------------------------------- #
# ------------------------------------------------------------------------------------------------- #
def clear_screen():
    if(os.name == 'posix'):
        os.system('clear')
    else:
        os.system('cls')


def program_break_time(memorization_time, affichage_text):
    duree_restante_avant_lancement = memorization_time
    print(f"{affichage_text} {memorization_time} secondes ", end="", flush=True)
    for i in range(memorization_time):
        time.sleep(1)
        print(".", end="", flush=True)
        duree_restante_avant_lancement -= 1


def seprateur_menu_affichage_log():
    write_log(f"*************************************************************", LOG_FILE, "INFO")


def seprateur_menu_affichage_console():
    print(f"*************************************************************")


def get_next_saturday_if_not_saturday(date_str):
    """Retourne le prochain samedi si la date donnée n'est pas déjà un samedi."""
    initial_date = datetime.strptime(date_str, "%d/%m/%Y")
    initial_weekday = initial_date.weekday()
    if initial_weekday != 5:
        days_to_next_saturday = (5 - initial_weekday) % 7
        next_saturday_date = initial_date + timedelta(days=days_to_next_saturday)
        return next_saturday_date.strftime("%d/%m/%Y")
    return date_str


def est_en_mission(description):
    """Renvoie True si la description indique un jour 'En mission'."""
    return description == "En mission"


def ajouter_jour_a_jours_remplis(jour, jours_remplis):
    """Ajoute un jour à la liste jours_remplis si ce n'est pas déjà fait."""
    if jour not in jours_remplis:
        jours_remplis.append(jour)
    return jours_remplis


def afficher_message_insertion(jour, valeur, tentative, message):
    """Affiche un message d'insertion de la valeur."""
    if message == "tentative d'insertion n°":
        write_log(f"⚠️ Valeur '{valeur}' confirmée pour le jour '{jour}' ({message}{tentative + 1})", LOG_FILE, "DEBUG")
    else:
        write_log(f"⚠️ Valeur '{valeur}' confirmée pour le jour '{jour}' {message})", LOG_FILE, "DEBUG")


# ------------------------------------------------------------------------------------------------- #
# ----------------------------------- FONCTIONS PRINCIPALES --------------------------------------- #
# ------------------------------------------------------------------------------------------------- #

def log_initialisation():
    """Initialise les logs et vérifie les configurations essentielles."""
    if not LOG_FILE:
        raise RuntimeError("Fichier de log introuvable.")
    write_log(f"📌 Démarrage de la fonction 'saisie_automatiser_psatime.main()'", LOG_FILE, "INFO")
    write_log(f"🔍 Chemin du fichier log : {LOG_FILE}", LOG_FILE, "DEBUG")
    

def initialize_shared_memory():
    """Récupère les données de la mémoire partagée pour le login."""
    memoire_cle = memoire_nom = memoire_mdp = None
    
    memoire_cle, cle_aes = recuperer_de_memoire_partagee(MEMOIRE_PARTAGEE_CLE, TAILLE_CLE, log_file=LOG_FILE)
    write_log(f"💀 Clé AES récupérée : {cle_aes.hex()}", LOG_FILE, "CRITICAL")

    memoire_nom = shared_memory.SharedMemory(name="memoire_nom")
    taille_nom = len(bytes(memoire_nom.buf).rstrip(b"\x00"))
    nom_utilisateur_chiffre = bytes(memoire_nom.buf[:taille_nom])
    write_log(f"💀 Taille du login chiffré : {len(nom_utilisateur_chiffre)}", LOG_FILE, "CRITICAL")

    memoire_mdp = shared_memory.SharedMemory(name="memoire_mdp")
    taille_mdp = len(bytes(memoire_mdp.buf).rstrip(b"\x00"))
    mot_de_passe_chiffre = bytes(memoire_mdp.buf[:taille_mdp])
    write_log(f"💀 Taille du mot de passe chiffré : {len(mot_de_passe_chiffre)}", LOG_FILE, "CRITICAL")

    # Vérification des données en mémoire partagée
    if not memoire_nom or not memoire_mdp or not memoire_cle:
        write_log(f"🚨 La mémoire partagée n'a pas été initialisée correctement. Assurez-vous que les identifiants ont été chiffrés", LOG_FILE, "ERROR")
        sys.exit(1)
    
    return [cle_aes, memoire_cle, nom_utilisateur_chiffre, memoire_nom, mot_de_passe_chiffre, memoire_mdp]

def wait_for_dom(driver):
    wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT) # Attendre que le DOM soit stable
    wait_for_dom_ready(driver, LONG_TIMEOUT) # chargé le DOM de page

def setup_browser():
    """Configure et démarre le navigateur."""
    driver = None
    
    driver = ouvrir_navigateur_sur_ecran_principal(
        plein_ecran=False,
        url=URL,
        headless=False,
        no_sandbox=False
    )
    if driver is not None:
        driver = definir_taille_navigateur(driver, 1260, 800)
        wait_for_dom_ready(driver, LONG_TIMEOUT)
    return driver


def connect_to_psatime(driver, cle_aes, nom_utilisateur_chiffre, mot_de_passe_chiffre):
    """Connecte l'utilisateur au portail PSATime."""
    nom_utilisateur = dechiffrer_donnees(nom_utilisateur_chiffre, cle_aes, log_file=LOG_FILE)
    mot_de_passe = dechiffrer_donnees(mot_de_passe_chiffre, cle_aes, log_file=LOG_FILE)
    cle_aes = None
    
    send_keys_to_element(driver, By.ID, "userid", nom_utilisateur)
    nom_utilisateur = None
    nom_utilisateur_chiffre = None
    send_keys_to_element(driver, By.ID, "pwd", mot_de_passe)
    mot_de_passe = None
    mot_de_passe_chiffre = None
    send_keys_to_element(driver, By.ID, "pwd", Keys.RETURN)

    wait_for_dom(driver)


def switch_to_iframe_main_target_win0(driver):
    # Attendre que l'iframe soit chargé avant de basculer
    element_present = wait_for_element(driver, By.ID, "main_target_win0", timeout=DEFAULT_TIMEOUT)
    if element_present:
        switched_to_iframe = switch_to_iframe_by_id_or_name(driver, "main_target_win0")  # Remplace par l'ID exact de l'iframe
    wait_for_dom(driver)
    
    return switched_to_iframe


def navigate_from_home_to_date_entry_page(driver):
    """Navigue de la page d'accueil jusqu'à la page de la saisie de la date cible"""
    
    # Verifier la présence et Interagir avec l'élément --> todo : indiquer quel nom
    element_present = wait_for_element(driver, By.ID, "PTNUI_LAND_REC14$0_row_0", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
    if element_present:
        click_element_without_wait(driver, By.ID, "PTNUI_LAND_REC14$0_row_0")
    wait_for_dom(driver)
    
    # Verifier la présence et Cliquer sur le bouton "panel" pour le fermer
    element_present = wait_for_element(driver, By.ID, "PT_SIDE$PIMG", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
    if element_present:
        click_element_without_wait(driver, By.ID, "PT_SIDE$PIMG")
    wait_for_dom(driver)
    
    switched_to_iframe = switch_to_iframe_main_target_win0(driver)
    
    return switched_to_iframe


def handle_date_input(driver, date_cible):
    """Gère la date cible pour la saisie."""
    date_input = wait_for_element(driver, By.ID, "EX_TIME_ADD_VW_PERIOD_END_DT", timeout=DEFAULT_TIMEOUT)
    if date_input:
        current_date_value = date_input.get_attribute("value")
        if date_cible and date_cible.strip():
            modifier_date_input(date_input, date_cible, "Date cible appliquée")
        else:
            new_date_value = get_next_saturday_if_not_saturday(current_date_value)
            if new_date_value != current_date_value:
                modifier_date_input(date_input, new_date_value, "Prochain samedi appliqué")
            else:
                write_log("Aucune modification de la date nécessaire.", LOG_FILE, "DEBUG")
    wait_for_dom(driver)


def submit_date_cible(driver):
    # Verifier la présence et Cliquer sur le bouton "Ajout"
    element_present = wait_for_element(driver, By.ID, "PTS_CFG_CL_WRK_PTS_ADD_BTN", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
    if element_present:
        send_keys_to_element(driver, By.ID, "PTS_CFG_CL_WRK_PTS_ADD_BTN", Keys.RETURN)
        # click_element_without_wait(driver, By.ID, "PTS_CFG_CL_WRK_PTS_ADD_BTN")
    wait_for_dom(driver)
    
    return element_present
    

def navigate_from_work_schedule_to_additional_information_page(driver):
    """Navigue de la page jours de travail jusqu'à la page information supplementaire"""
    wait_for_dom(driver)

    element_present = wait_for_element(driver, By.ID, "UC_EX_WRK_UC_TI_FRA_LINK", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
    if element_present:
        click_element_without_wait(driver, By.ID, "UC_EX_WRK_UC_TI_FRA_LINK")

    # Revenir au contexte principal du document
    switch_to_default_content(driver)
    
    wait_for_dom(driver)


def submit_and_validate_additional_information(driver):
    """Valide et remplit les informations supplémentaires nécessaires."""
    # Attendre que l'iframe soit chargé avant de basculer
    element_present = wait_for_element(driver, By.ID, "ptModFrame_0", timeout=DEFAULT_TIMEOUT)
    if element_present:
        switched_to_iframe = switch_to_iframe_by_id_or_name(driver, "ptModFrame_0")  # Remplace par l'ID exact de l'iframe
    
    if switched_to_iframe:
        for config_description in DESCRIPTIONS:
            traiter_description(driver, config_description)
        write_log(f"Validation des informations supplémentaires terminée.", LOG_FILE, "INFO")

    # Verifier la présence et Cliquer sur le bouton "OK"
    element_present = wait_for_element(driver, By.ID, "#ICSave", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
    if element_present:
        click_element_without_wait(driver, By.ID, "#ICSave")


def save_draft_and_validate(driver):
    """Verifier la présence et Cliquer sur le bouton "Enreg. brouill."""
    element_present = wait_for_element(driver, By.ID, "EX_ICLIENT_WRK_SAVE_PB", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
    if element_present:
        click_element_without_wait(driver, By.ID, "EX_ICLIENT_WRK_SAVE_PB")
        wait_for_dom(driver)
    
    return element_present


def finalize_submit_and_validate(driver):
    """Effectue les étapes finales de soumission."""
    # Attendre que l'iframe soit chargé avant de basculer
    element_present = wait_for_element(driver, By.ID, "ptModFrame_1", timeout=DEFAULT_TIMEOUT)
    if element_present:
        switched_to_iframe = switch_to_iframe_by_id_or_name(driver, "ptModFrame_1")

    # Verifier la présence et Cliquer sur le bouton "OK"
    element_present = wait_for_element(driver, By.ID, "#ICSave", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
    if element_present:
        click_element_without_wait(driver, By.ID, "#ICSave")

    # Verifier la présence et Cliquer sur le bouton "Soumettre pour approb."
    element_present = wait_for_element(driver, By.ID, "EX_TIME_HDR_WRK_PB_SUBMIT", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
    if element_present:
        click_element_without_wait(driver, By.ID, "EX_TIME_HDR_WRK_PB_SUBMIT")


def cleanup_resources(driver, memoire_cle, memoire_nom, memoire_mdp):
    """Nettoie les ressources à la fin de l'exécution."""
    if memoire_cle:
        supprimer_memoire_partagee_securisee(memoire_cle, LOG_FILE)
    if memoire_nom:
        supprimer_memoire_partagee_securisee(memoire_nom, LOG_FILE)
    if memoire_mdp:
        supprimer_memoire_partagee_securisee(memoire_mdp, LOG_FILE)
    if driver:
        driver.quit()
    write_log(f"🏁 [FIN] Clé et données supprimées de manière sécurisée, des mémoires partagées du fichier saisie_automatiser_psatime.", LOG_FILE, "INFO")


# ------------------------------------------------------------------------------------------------------------------ #
# -------------------------------------------- CODE PRINCIPAL ------------------------------------------------------ #
# ------------------------------------------------------------------------------------------------------------------ #
def main():
    """Point d'entrée principal du script."""
    try:
        # Initialisation des logs et configurations
        log_initialisation()
        variables = initialize_shared_memory()
        cle_aes = variables[0]
        memoire_cle = variables[1]
        nom_utilisateur_chiffre = variables[2]
        memoire_nom = variables[3]
        mot_de_passe_chiffre = variables[4]
        memoire_mdp = variables[5]
        variables = None
        
        # Initialisation du navigateur
        driver = setup_browser()
        
        # Connexion au portail PSATime
        connect_to_psatime(driver, cle_aes, nom_utilisateur_chiffre, mot_de_passe_chiffre)
        
        # Navigation vers la page de feuille de temps
        switched_to_iframe = navigate_from_home_to_date_entry_page(driver)

        if switched_to_iframe:
            # Gestion de la date cible
            handle_date_input(driver, DATE_CIBLE)

            program_break_time(1, "Veuillez patienter. Court délai pour stabilisation du DOM")
            print()
            
            element_present = submit_date_cible(driver)
            if element_present:
                # Revenir au contexte principal du document
                switch_to_default_content(driver)
        
                # Vérifier la présence d'un message d'alerte indiquant une date non conforme
                alertes = ["ptModContent_0"] 
                for alerte in alertes:
                    element_present = wait_for_element(driver, By.ID, alerte, timeout=DEFAULT_TIMEOUT)
                    if element_present:
                        # Cliquer sur le bouton "OK" pour fermer l'alerte et indiquer à l'utilisateur de modifier la date
                        click_element_without_wait(driver, By.ID, "#ICOK")
                        if alerte == alertes[0]:
                            write_log(f"\nERREUR : Vous avez déjà créé une feuille de temps pour cette période. (10502,125)\n"
                                "--> Modifier la date du PSATime dans le fichier ini. Le programme va s'arreter.", LOG_FILE, "INFO")


                        # Arrêter le script. Utilisez sys.exit() pour une sortie propre
                        sys.exit()
                else:
                    write_log("Date validée avec succès.", LOG_FILE, "DEBUG")
        
        wait_for_dom(driver)
        switched_to_iframe = switch_to_iframe_main_target_win0(driver)

        program_break_time(1, "Veuillez patienter. Court délai pour stabilisation du DOM")
        print()
        
        # Verifier la présence et Cliquer sur "Ouvrir déclaration vide" après avoir changé de page
        if CHOIX_USER:
            element_present = wait_for_element(driver, By.ID, "EX_ICLIENT_WRK_OK_PB", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
            if element_present:
                click_element_without_wait(driver, By.ID, "EX_ICLIENT_WRK_OK_PB")

        # Verifier la présence et Cliquer sur "Copie feuille temps" après avoir changé de page
        elif not CHOIX_USER:
            element_present = wait_for_element(driver, By.ID, "EX_TIME_HDR_WRK_COPY_TIME_RPT", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
            if element_present:
                click_element_without_wait(driver, By.ID, "EX_TIME_HDR_WRK_COPY_TIME_RPT")

        wait_for_dom(driver)

        remplir_jours_feuille_de_temps.main(driver)
        
        # jours_remplis = []  # Liste pour suivre les jours déjà remplis
        # max_attempts = 5
        # # Parcourir chaque description dans LISTE_ITEMS_DESCRIPTIONS
        # for description_cible in LISTE_ITEMS_DESCRIPTIONS:
        #     # Recherche de la ligne avec la description spécifiée pour le jour
        #     id_value = "POL_DESCR$"
        #     row_index = trouver_ligne_par_description(driver, description_cible, id_value)

        #     # Si la ligne est trouvée, remplir les jours de la semaine
        #     if row_index is not None:
        #         for jour_index, jour_name in JOURS_SEMAINE.items():  # Dimanche = 1, Lundi = 2, etc.
        #             input_id = f"POL_TIME{jour_index}${row_index}"

        #             # Vérifier la présence de l'élément
        #             element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

        #             if element:
        #                 # Vérifier s'il y a une valeur dans l'élément pour ce jour
        #                 jour_rempli = verifier_champ_jour_rempli(element, jour_name)
        #                 if jour_rempli:
        #                     jours_remplis.append(jour_rempli) # Ajouter le jour s'il est déjà rempli
        
        
        # # clear_screen()

        # # Remplir les jours du dimanche au samedi, s'ils sont encore vides.
        # for jour, (description_cible, valeur_a_remplir) in JOURS_DE_TRAVAIL.items():
        #     attempt = 0
        #     if description_cible and not est_en_mission(description_cible) and jour not in jours_remplis:  # Remplir seulement si le jour est vide
        #         id_value = "POL_DESCR$"
        #         row_index = trouver_ligne_par_description(driver, description_cible, id_value)
                
        #         if row_index is not None:
        #             jour_index = list(JOURS_SEMAINE.keys())[list(JOURS_SEMAINE.values()).index(jour)]
        #             input_id = f"POL_TIME{jour_index}${row_index}"
                    
        #             # Vérifier la présence de l'élément
        #             element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)
                    
        #             if element:
        #                 while attempt < max_attempts:
        #                     try:
        #                         # Étape 1 : Détection et vérification du contenu actuel
        #                         day_input_field, is_correct_value = detecter_et_verifier_contenu(driver, input_id, valeur_a_remplir)
                                
        #                         if is_correct_value:
        #                             jours_remplis = ajouter_jour_a_jours_remplis(jour, jours_remplis)
        #                             afficher_message_insertion(jour, valeur_a_remplir, attempt, "tentative d'insertion n°")
        #                             break

        #                         # Étape 2 : Effacer et entrer la nouvelle valeur
        #                         effacer_et_entrer_valeur(day_input_field, valeur_a_remplir)
        #                         program_break_time(1, "Veuillez patienter. Court délai pour stabilisation du DOM")
        #                         print()

        #                         # Étape 3 : Contrôler que la valeur est bien insérée
        #                         if controle_insertion(day_input_field, valeur_a_remplir):
        #                             jours_remplis = ajouter_jour_a_jours_remplis(jour, jours_remplis)
        #                             afficher_message_insertion(jour, valeur_a_remplir, attempt, "après insertion")
        #                             break

        #                     except StaleElementReferenceException:
        #                         write_log(f"Référence obsolète pour '{jour}', tentative {attempt + 1}", LOG_FILE, "DEBUG")
                            
        #                     attempt += 1

        #                 # Si toutes les tentatives échouent, indiquer un message d'échec
        #                 if attempt == max_attempts:
        #                     write_log(f"Échec de l'insertion de la valeur '{valeur_a_remplir}' dans le jour '{jour}' après {max_attempts} tentatives.", LOG_FILE, "DEBUG")

        #     elif description_cible and est_en_mission(description_cible) and jour not in jours_remplis:
        #         # Cas où description_cible est "En mission", on écrit directement dans les IDs spécifiques sans utiliser `description_cible`
        #         jour_index = list(JOURS_SEMAINE.keys())[list(JOURS_SEMAINE.values()).index(jour)]
        #         input_id = f"TIME{jour_index}$0"  # Définir l'ID de l'élément pour ce jour
                
        #         # Vérifier la présence de l'élément
        #         element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

        #         if element:
        #             while attempt < max_attempts:
        #                 try:
        #                     # Étape 1 : Détection et vérification du contenu actuel
        #                     day_input_field, is_correct_value = detecter_et_verifier_contenu(driver, input_id, valeur_a_remplir)
                            
        #                     if is_correct_value:
        #                         jours_remplis = ajouter_jour_a_jours_remplis(jour, jours_remplis)
        #                         afficher_message_insertion(jour, valeur_a_remplir, attempt, "tentative d'insertion n°")
        #                         break

        #                     # Étape 2 : Effacer et entrer la nouvelle valeur
        #                     effacer_et_entrer_valeur(day_input_field, valeur_a_remplir)
        #                     program_break_time(1, "Veuillez patienter. Court délai pour stabilisation du DOM")
        #                     print()

        #                     # Étape 3 : Contrôler que la valeur est bien insérée
        #                     if controle_insertion(day_input_field, valeur_a_remplir):
        #                         jours_remplis = ajouter_jour_a_jours_remplis(jour, jours_remplis)
        #                         afficher_message_insertion(jour, valeur_a_remplir, attempt, "après insertion")
        #                         break

        #                 except StaleElementReferenceException:
        #                     write_log(f"Référence obsolète pour '{jour}', tentative {attempt + 1}", LOG_FILE, "DEBUG")
                        
        #                 attempt += 1

        #             # Si toutes les tentatives échouent, indiquer un message d'échec
        #             if attempt == max_attempts:
        #                 write_log(f"Échec de l'insertion de la valeur '{valeur_a_remplir}' dans le jour '{jour}' après {max_attempts} tentatives.", LOG_FILE, "DEBUG")
        
        # # Vérifie si "En mission" est présent
        # contains_en_mission = any(value[0] == "En mission" for value in JOURS_DE_TRAVAIL.values())
        # if contains_en_mission:
        #     write_log(f"Contient 'En mission' : {contains_en_mission}", LOG_FILE, "INFO")
            
        #     # Boucle sur les IDs pour insérer les valeurs correspondantes
        #     for id in LISTES_ID_INFORMATIONS_MISSION:
        #         key = ID_TO_KEY_MAPPING[id]  # Récupérer la clé associée
        #         if key == "sub_category_code":
        #             continue
        #         valeur_a_remplir = INFORMATIONS_PROJET_MISSION[key]  # Récupérer la valeur associée
        #         write_log(f"Traitement de l'élément : {key} avec ID : {id} et valeur : {valeur_a_remplir}", LOG_FILE, "DEBUG")
        #         attempt = 0

        #         wait_for_dom(driver)
                
        #         # Vérifier la présence de l'élément
        #         element = wait_for_element(driver, By.ID, id, timeout=DEFAULT_TIMEOUT)
        #         if element:
        #             while attempt < max_attempts:
        #                 try:
        #                     # Étape 1 : Détection et vérification du contenu actuel
        #                     day_input_field, is_correct_value = detecter_et_verifier_contenu(driver, id, valeur_a_remplir)
        #                     # write_log(f"id trouvé : {day_input_field} / is_correct_value : {is_correct_value}", LOG_FILE, "DEBUG")
                            
        #                     if is_correct_value:
        #                         break
                            
        #                     # Étape 2 : Effacer et entrer la nouvelle valeur
        #                     effacer_et_entrer_valeur(day_input_field, valeur_a_remplir)
        #                     program_break_time(1, "Veuillez patienter. Court délai pour stabilisation du DOM")
        #                     print()

        #                     # Étape 3 : Contrôler que la valeur est bien insérée
        #                     if controle_insertion(day_input_field, valeur_a_remplir):
        #                         break

        #                 except StaleElementReferenceException:
        #                     write_log(f"Référence obsolète. tentative {attempt + 1}", LOG_FILE, "DEBUG")
                        
        #                 attempt += 1

        #             # Si toutes les tentatives échouent, indiquer un message d'échec
        #             if attempt == max_attempts:
        #                 write_log(f"Échec de l'insertion de la valeur '{valeur_a_remplir}' pour l'ID '{id}', après {max_attempts} tentatives.", LOG_FILE, "DEBUG")
                        
        # else:
        #     write_log("La personne N'EST PAS en mission", LOG_FILE, "INFO")
            
        # Navigue de la page jours de travail jusqu'à la page information supplementaire
        navigate_from_work_schedule_to_additional_information_page(driver)
        
        # Validation des informations supplémentaires
        submit_and_validate_additional_information(driver)

        # Revenir au contexte principal du document
        switch_to_default_content(driver)
        
        wait_for_dom(driver)

        switched_to_iframe = switch_to_iframe_main_target_win0(driver)
        
        if switched_to_iframe:
            # Contrôle après avoir rempli les jours
            detecter_doublons_jours(driver)
                
            # ----------------------------------------------------------------------------- #
            # ---------------------- ETAPE ENREG. BROUILL --------------------------------- #
            # ----------------------------------------------------------------------------- #
            if save_draft_and_validate(driver):

                # Revenir au contexte principal du document
                switch_to_default_content(driver)

                # Vérifier la présence d'un message d'alerte indiquant une date non conforme
                alertes = ["ptModContent_1", "ptModContent_2", "ptModContent_3"] 
                for alerte in alertes:
                    element_present = wait_for_element(driver, By.ID, alerte, timeout=DEFAULT_TIMEOUT)
                    if element_present:
                        if alerte == alertes[0]:
                            # Cliquer sur le bouton "OK" pour fermer l'alerte et indiquer à l'utilisateur le warning
                            click_element_without_wait(driver, By.ID, "#ICOK")
                            write_log(f"⚠️ \nAssurez-vous d’avoir choisi la bonne date pour votre relevé d’heures. (24500,19)", LOG_FILE, "INFO")
                            # input("--> Appuyez sur Entrée pour continuer.")  
                        elif alerte == alertes[1]:
                            # Cliquer sur le bouton "OK" pour fermer l'alerte et indiquer à l'utilisateur le warning
                            click_element_without_wait(driver, By.ID, "#ICOK")
                            write_log(f"⚠️ \nUn jour de la semaine est un jour férié. Ces heures n'ont pas été saisies comme telles. (24500,427).", LOG_FILE, "INFO")
                            # input("--> Appuyez sur Entrée pour fermer le navigateur.")  
                        elif alerte == alertes[2]:
                            # Cliquer sur le bouton "OK" pour fermer l'alerte et indiquer à l'utilisateur le warning
                            click_element_without_wait(driver, By.ID, "#ICOK")
                            write_log(f"⚠️\nIl existe un écart avec vos absences approuvées dans le Centre de service RH (24500,320)", LOG_FILE, "INFO")
                            # input("--> Appuyez sur Entrée pour fermer le navigateur.")    
                        break # Arrêter la boucle une fois la ou les alerte(s) traitée(s)
                    

        wait_for_dom(driver)
        
        switch_to_iframe_main_target_win0(driver)

        wait_for_dom(driver)
        # ----------------------------------------------------------------------------- #
        # ---------------------- ETAPE SOUMETTRE POUR APPROB. ------------------------- #
        # ----------------------------------------------------------------------------- #
        # finalize_submit_and_validate(driver)


    except NoSuchElementException as e:
        write_log(f"❌ L'élément n'a pas été trouvé : {str(e)}", LOG_FILE, "ERROR")
    except TimeoutException as e:
        write_log(f"❌ Temps d'attente dépassé pour un élément : {str(e)}", LOG_FILE, "ERROR")
    except WebDriverException as e:
        write_log(f"❌ Erreur liée au WebDriver : {str(e)}", LOG_FILE, "ERROR")
    except Exception as e:
        write_log(f"❌ Erreur inattendue : {str(e)}", LOG_FILE, "ERROR")

    finally:
        try:
            if driver is not None:
                input("INFO : Controler et soumettez votre PSATime, Puis appuyer sur ENTRER ")
            else:
                input("ERROR : Controler les Log, Puis appuyer sur ENTRER ET relancer l'outil ")
            seprateur_menu_affichage_console()
        except ValueError:
            pass  # Ignore toute erreur
        finally:
            cleanup_resources(driver, memoire_cle, memoire_nom, memoire_mdp)
