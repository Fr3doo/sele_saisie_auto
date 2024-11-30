# remplir_informations_supp_france.py

# Import des bibliothèques nécessaires
# import configparser
# from selenium import webdriver
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.edge.options import Options as EdgeOptions
# from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.action_chains import ActionChains
# from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException, StaleElementReferenceException
from fonctions_selenium_utils import remplir_champ_texte, selectionner_option_menu_deroulant_type_select, trouver_ligne_par_description, verifier_champ_jour_rempli, wait_for_element
from logger_utils import write_log
from shared_utils import get_log_file

# ------------------------------------------------------------------------------------------- #
# ----------------------------------- CONSTANTE --------------------------------------------- #
# ------------------------------------------------------------------------------------------- #
LOG_FILE = get_log_file()

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

# ------------------------------------------------------------------------------------------- #
# ----------------------------------- FONCTIONS --------------------------------------------- #
# ------------------------------------------------------------------------------------------- #

def traiter_description(driver, config):
    """
    Traite une description en fonction d'une configuration donnée.

    Args:
        driver (webdriver): Instance du navigateur Selenium.
        config (dict): Configuration contenant toutes les informations nécessaires.
            - "description_cible" : Description à rechercher.
            - "id_value_ligne" : Préfixe des IDs pour identifier les lignes.
            - "id_value_jours" : Préfixe des IDs pour manipuler les jours.
            - "type_element" : Type des éléments à manipuler ("select" ou "input").
            - "valeurs_a_remplir" : Dictionnaire contenant les valeurs à remplir par jour.
    """
    description_cible = config["description_cible"]
    id_value_ligne = config["id_value_ligne"] # Pour trouver la ligne
    id_value_jours = config["id_value_jours"] # Pour les jours de la semaine
    type_element = config["type_element"]
    valeurs_a_remplir = config["valeurs_a_remplir"]
    jours_semaine = JOURS_SEMAINE

    
    # 1. Recherche de la ligne correspondant à la description
    write_log(f"🔍 Début du traitement pour la description : '{description_cible}'", LOG_FILE, "DEBUG")
    row_index = trouver_ligne_par_description(driver, description_cible, id_value_ligne)
    if row_index is None:
        write_log(f"❌ Description '{description_cible}' non trouvée avec l'id_value '{id_value_ligne}'.", LOG_FILE, "DEBUG")
        return
    write_log(f"✅ Description '{description_cible}' trouvée à l'index {row_index}.", LOG_FILE, "DEBUG")

    jours_remplis = []  # Suivre les jours déjà remplis

    # 2. Boucle pour parcourir tous les jours (Dimanche = 1, Samedi = 7 ). Vérification des jours remplis.
    write_log(f"🔍 Vérification des jours déjà remplis pour '{description_cible}'.", LOG_FILE, "DEBUG")
    for i in range(1, 8):  # Dimanche = 1, Samedi = 7
        # Gestion des cas où l'ID doit inclure une différence (exemple : ajout d'un décalage pour "Durée de la pause déjeuner")
        if "UC_TIME_LIN_WRK_UC_DAILYREST" in id_value_jours:
            input_id = f"{id_value_jours}{10 + i}$0"  # Cas particulier
        else:
            input_id = f"{id_value_jours}{i}${row_index}"

        element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)
        if element:
            jour = jours_semaine[i]
            write_log(f"👉 Vérification du jour : {jour} (ID: {input_id})", LOG_FILE, "DEBUG")
            if verifier_champ_jour_rempli(element, jour):
                jours_remplis.append(jour)
                write_log(f"✅ Jour '{jour}' déjà rempli.", LOG_FILE, "DEBUG")
            else:
                write_log(f"❌ Jour '{jour}' vide.", LOG_FILE, "DEBUG")
        else:
            write_log(f"❌ Élément non trouvé pour l'ID : {input_id}", LOG_FILE, "DEBUG")

    # 3. Remplir les jours (Dimanche = 1, Samedi = 7), s'ils sont encore vides.
    write_log(f"✍️ Remplissage des jours vides pour '{description_cible}'.", LOG_FILE, "DEBUG")
    for i in range(1, 8):  # Dimanche = 1, Samedi = 7
        if "UC_TIME_LIN_WRK_UC_DAILYREST" in id_value_jours:
            input_id = f"{id_value_jours}{10 + i}$0"  # Cas particulier
        else:
            input_id = f"{id_value_jours}{i}${row_index}"

        element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)
        if element:
            jour = jours_semaine[i]
            if jour not in jours_remplis:
                valeur_a_remplir = valeurs_a_remplir.get(jour)
                if valeur_a_remplir:
                    write_log(f"✏️ Remplissage de '{jour}' avec la valeur '{valeur_a_remplir}'.", LOG_FILE, "DEBUG")
                    if type_element == "select":
                        selectionner_option_menu_deroulant_type_select(element, valeur_a_remplir)
                    elif type_element == "input":
                        remplir_champ_texte(element, jour, valeur_a_remplir)
                else:
                    write_log(f"⚠️ Aucune valeur définie pour le jour '{jour}' dans 'valeurs_a_remplir'.", LOG_FILE, "DEBUG")
            else:
                write_log(f"🔄 Jour '{jour}' déjà rempli, aucun changement.", LOG_FILE, "DEBUG")
        else:
            write_log(f"❌ Impossible de trouver l'élément pour l'ID : {input_id}", LOG_FILE, "DEBUG")

