# remplir_jours_feuille_de_temps.py

# Import des bibliothèques nécessaires
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from fonctions_selenium_utils import controle_insertion, detecter_et_verifier_contenu, effacer_et_entrer_valeur, remplir_champ_texte, selectionner_option_menu_deroulant_type_select, trouver_ligne_par_description, verifier_champ_jour_rempli, wait_for_dom_ready, wait_for_element, wait_until_dom_is_stable
from logger_utils import write_log
from read_or_write_file_config_ini_utils import read_config_ini
from shared_utils import get_log_file, program_break_time
from dropdown_options import cgi_options_billing_action
from constants import JOURS_SEMAINE

# ------------------------------------------------------------------------------------------- #
# ----------------------------------- CONSTANTE --------------------------------------------- #
# ------------------------------------------------------------------------------------------- #
LOG_FILE = get_log_file()
config = read_config_ini(LOG_FILE)

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

MAX_ATTEMPTS = 5
DEFAULT_TIMEOUT = 10  # Délai d'attente par défaut
LONG_TIMEOUT = 20


# ----------------------------------------------------------------------------- #
# ------------------------------- UTILITIES ----------------------------------- #
# ----------------------------------------------------------------------------- #

# def log_error(message: str):
#     """Log errors to a file."""
#     with open(LOG_FILE, 'a', encoding="utf-8") as log:
#         log.write(f"ERROR: {message}\n")

# def log_info(message: str):
#     """Log info to a file."""
#     with open(LOG_FILE, 'a', encoding="utf-8") as log:
#         log.write(f"INFO: {message}\n")

def wait_for_dom(driver):
    wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT) # Attendre que le DOM soit stable
    wait_for_dom_ready(driver, LONG_TIMEOUT) # chargé le DOM de page

def clear_screen():
    """Clear console output."""
    import os
    os.system("cls" if os.name == "nt" else "clear")

def est_en_mission(description):
    """Renvoie True si la description indique un jour 'En mission'."""
    return description == "En mission"

def est_en_mission_presente(jours_de_travail):
    """Vérifie si un jour de travail est marqué comme 'En mission'."""
    return any(value[0] == "En mission" for value in jours_de_travail.values())


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

# ------------------------------------------------------------------------------------------- #
# ----------------------------------- FONCTIONS --------------------------------------------- #
# ------------------------------------------------------------------------------------------- #

def remplir_jours(driver, liste_items_descriptions, jours_semaine, jours_remplis):
    """Remplir les jours dans l'application web."""
    # Parcourir chaque description dans liste_items_descriptions
    for description_cible in liste_items_descriptions:
        # Recherche de la ligne avec la description spécifiée pour le jour
        id_value = "POL_DESCR$"
        row_index = trouver_ligne_par_description(driver, description_cible, id_value)
        
        # Si la ligne est trouvée, remplir les jours de la semaine
        if row_index is not None:
            for jour_index, jour_name in jours_semaine.items():
                input_id = f"POL_TIME{jour_index}${row_index}"
                
                # Vérifier la présence de l'élément
                element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)
                
                if element:
                    # Vérifier s'il y a une valeur dans l'élément pour ce jour
                    jour_rempli = verifier_champ_jour_rempli(element, jour_name)
                    if jour_rempli:
                        jours_remplis.append(jour_rempli) # Ajouter le jour s'il est déjà rempli
                        
    return jours_remplis


def traiter_jour(driver, jour, description_cible, valeur_a_remplir, jours_remplis):
    """Traiter un jour spécifique pour le remplissage."""
    attempt = 0
    
    if jour in jours_remplis or not description_cible:
        return jours_remplis

    id_value = "POL_DESCR$"
    row_index = trouver_ligne_par_description(driver, description_cible, id_value)
    
    if row_index is not None:
        jour_index = list(JOURS_SEMAINE.keys())[list(JOURS_SEMAINE.values()).index(jour)]
        input_id = f"POL_TIME{jour_index}${row_index}"
        
        # Vérifier la présence de l'élément
        element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

        if element:
            while attempt < MAX_ATTEMPTS:
                try:
                    # Étape 1 : Détection et vérification du contenu actuel
                    day_input_field, is_correct_value = detecter_et_verifier_contenu(driver, input_id, valeur_a_remplir)
                    
                    if is_correct_value:
                        jours_remplis = ajouter_jour_a_jours_remplis(jour, jours_remplis)
                        afficher_message_insertion(jour, valeur_a_remplir, attempt, "tentative d'insertion n°")
                        break
                    
                    # Étape 2 : Effacer et entrer la nouvelle valeur
                    effacer_et_entrer_valeur(day_input_field, valeur_a_remplir)
                    program_break_time(1, "Veuillez patienter. Court délai pour stabilisation du DOM")
                    print()
                    
                    # Étape 3 : Contrôler que la valeur est bien insérée
                    if controle_insertion(day_input_field, valeur_a_remplir):
                        jours_remplis = ajouter_jour_a_jours_remplis(jour, jours_remplis)
                        afficher_message_insertion(jour, valeur_a_remplir, attempt, "après insertion")
                        break
                    
                except StaleElementReferenceException:
                    write_log(f"Référence obsolète pour '{jour}', tentative {attempt + 1}", LOG_FILE, "DEBUG")
                
                attempt += 1

            # Si toutes les tentatives échouent, indiquer un message d'échec
            if attempt == MAX_ATTEMPTS:
                write_log(f"Échec de l'insertion de la valeur '{valeur_a_remplir}' dans le jour '{jour}' après {MAX_ATTEMPTS} tentatives.", LOG_FILE, "DEBUG")
            
    return jours_remplis


def remplir_mission(driver, jours_de_travail, jours_remplis):
    """Remplir les jours de travail pour les missions."""
    for jour, (description_cible, valeur_a_remplir) in jours_de_travail.items():
        if description_cible and not est_en_mission(description_cible) and jour not in jours_remplis:
            jours_remplis = traiter_jour(driver, jour, description_cible, valeur_a_remplir, jours_remplis)
        elif description_cible and est_en_mission(description_cible) and jour not in jours_remplis:
            remplir_mission_specifique(driver, jour, valeur_a_remplir, jours_remplis)
    return jours_remplis


def remplir_mission_specifique(driver, jour, valeur_a_remplir, jours_remplis):
    """Cas spécifique pour les jours en mission.
    Cas où description_cible est "En mission", on écrit directement dans les IDs spécifiques sans utiliser `description_cible`
    """
    attempt = 0
    jour_index = list(JOURS_SEMAINE.keys())[list(JOURS_SEMAINE.values()).index(jour)]
    input_id = f"TIME{jour_index}$0" # Définir l'ID de l'élément pour ce jour
    
    # Vérifier la présence de l'élément
    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

    if element:
        while attempt < MAX_ATTEMPTS:
            try:
                # Étape 1 : Détection et vérification du contenu actuel
                day_input_field, is_correct_value = detecter_et_verifier_contenu(driver, input_id, valeur_a_remplir)
                
                if is_correct_value:
                    jours_remplis = ajouter_jour_a_jours_remplis(jour, jours_remplis)
                    afficher_message_insertion(jour, valeur_a_remplir, attempt, "tentative d'insertion n°")
                    break
                
                # Étape 2 : Effacer et entrer la nouvelle valeur
                effacer_et_entrer_valeur(day_input_field, valeur_a_remplir)
                program_break_time(1, "Veuillez patienter. Court délai pour stabilisation du DOM")
                print()
                
                # Étape 3 : Contrôler que la valeur est bien insérée
                if controle_insertion(day_input_field, valeur_a_remplir):
                    jours_remplis = ajouter_jour_a_jours_remplis(jour, jours_remplis)
                    afficher_message_insertion(jour, valeur_a_remplir, attempt, "après insertion")
                    break
                
            except StaleElementReferenceException:
                write_log(f"Référence obsolète pour '{jour}', tentative {attempt + 1}", LOG_FILE, "DEBUG")
            
            attempt += 1
        
        # Si toutes les tentatives échouent, indiquer un message d'échec
        if attempt == MAX_ATTEMPTS:
            write_log(f"Échec de l'insertion de la valeur '{valeur_a_remplir}' dans le jour '{jour}' après {MAX_ATTEMPTS} tentatives.", LOG_FILE, "DEBUG")

def traiter_champs_mission(driver, listes_id_informations_mission, id_to_key_mapping, informations_projet_mission, max_attempts=5):
    """Traite les champs associés aux missions ('En mission') en insérant les valeurs nécessaires."""
    for id in listes_id_informations_mission:
        key = id_to_key_mapping.get(id)
        if key == "sub_category_code":  # Exclure les champs non concernés
            continue

        valeur_a_remplir = informations_projet_mission.get(key)
        if not valeur_a_remplir:
            write_log(f"Aucune valeur trouvée pour le champ '{key}' (ID: {id}).", LOG_FILE, "DEBUG")
            continue

        write_log(f"Traitement de l'élément : {key} avec ID : {id} et valeur : {valeur_a_remplir}.", LOG_FILE, "DEBUG")
        attempt = 0

        wait_for_dom(driver)  # Attente que le DOM soit prêt

        # Vérifier la présence de l'élément et gérer les tentatives d'insertion
        element = wait_for_element(driver, By.ID, id, timeout=DEFAULT_TIMEOUT)
        if element:
            while attempt < max_attempts:
                try:
                    # Étape 1 : Vérification de la valeur actuelle
                    input_field, is_correct_value = detecter_et_verifier_contenu(driver, id, valeur_a_remplir)
                    if is_correct_value:
                        write_log(f"Valeur correcte déjà présente pour '{id}'.", LOG_FILE, "DEBUG")
                        break

                    # Étape 2 : Effacer et insérer la nouvelle valeur
                    effacer_et_entrer_valeur(input_field, valeur_a_remplir)
                    program_break_time(1, "Stabilisation du DOM après insertion.")
                    print()

                    # Étape 3 : Vérification de l'insertion
                    if controle_insertion(input_field, valeur_a_remplir):
                        write_log(f"Valeur '{valeur_a_remplir}' insérée avec succès pour '{id}'.", LOG_FILE, "DEBUG")
                        break

                except StaleElementReferenceException:
                    write_log(f"Référence obsolète pour '{id}', tentative {attempt + 1}.", LOG_FILE, "ERROR")
                
                attempt += 1

            # Si toutes les tentatives échouent
            if attempt == max_attempts:
                write_log(f"Échec de l'insertion pour '{id}' après {max_attempts} tentatives.", LOG_FILE, "ERROR")

        
# ----------------------------------------------------------------------------- #
# ----------------------------------- MAIN ------------------------------------ #
# ----------------------------------------------------------------------------- #
def main(driver):
    """Point d'entrée principal du script pour remplir automatiquement les jours et les missions."""
    try:
        jours_remplis = []  # Liste pour suivre les jours déjà remplis

        write_log(f"Initialisation du processus de remplissage...", LOG_FILE, "DEBUG")

        # Étape 1 : Remplir les jours standard
        write_log(f"Début du remplissage des jours hors mission...", LOG_FILE, "DEBUG")
        jours_remplis = remplir_jours(driver, LISTE_ITEMS_DESCRIPTIONS, JOURS_SEMAINE, jours_remplis)
        write_log(f"Jours déjà remplis : {jours_remplis}", LOG_FILE, "DEBUG")

        # Étape 2 : Gestion des jours de travail et des missions
        write_log(f"Début du traitement des jours de travail et des missions...", LOG_FILE, "DEBUG")
        jours_remplis = remplir_mission(driver, JOURS_DE_TRAVAIL, jours_remplis)
        write_log(f"Finalisation des jours remplis : {jours_remplis}", LOG_FILE, "DEBUG")

        # Étape 3 : Vérification des champs liés aux missions
        if est_en_mission_presente(JOURS_DE_TRAVAIL):
            write_log(f"Jour 'En mission' détecté. Traitement des champs associés...", LOG_FILE, "DEBUG")
            traiter_champs_mission(driver, LISTES_ID_INFORMATIONS_MISSION, ID_TO_KEY_MAPPING, INFORMATIONS_PROJET_MISSION)
        else:
            write_log(f"Aucun Jour 'En mission' détecté.", LOG_FILE, "DEBUG")

        # Étape finale : Succès
        write_log(f"Tous les jours et missions ont été traités avec succès.", LOG_FILE, "DEBUG")

    except NoSuchElementException as e:
        write_log(f"Élément introuvable : {str(e)}.", LOG_FILE, "ERROR")
    except TimeoutException as e:
        write_log(f"Temps d'attente dépassé pour un élément : {str(e)}.", LOG_FILE, "ERROR")
    except StaleElementReferenceException as e:
        write_log(f"Référence obsolète détectée : {str(e)}.", LOG_FILE, "ERROR")
    except WebDriverException as e:
        write_log(f"Erreur WebDriver : {str(e)}.", LOG_FILE, "ERROR")
    except Exception as e:
        write_log(f"Erreur inattendue : {str(e)}.", LOG_FILE, "ERROR")

if __name__ == "__main__":
    main()