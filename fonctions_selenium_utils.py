# fonctions_selenium_utils.py

# Import des bibliothèques nécessaires
# import configparser
from selenium import webdriver
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
# from selenium.common.exceptions import TimeoutException, WebDriverException
# from datetime import datetime, timedelta
import time
# import sys
# import os
# from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
# from cryptography.hazmat.primitives.padding import PKCS7
# from multiprocessing import shared_memory
# from encryption_utils import recuperer_de_memoire_partagee, dechiffrer_donnees ,supprimer_memoire_partagee_securisee
# from read_file_config_ini_utils import read_config_ini
from logger_utils import write_log
from shared_utils import get_log_file

# ------------------------------------------------------------------------------------------- #
# ----------------------------------- CONSTANTE --------------------------------------------- #
# ------------------------------------------------------------------------------------------- #
# from main import get_log_file

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

def is_document_complete(driver):
    """Vérifie si le DOM est complètement chargé."""
    return driver.execute_script("return document.readyState") == "complete"


def wait_for_dom_ready(driver, timeout=20):
    """Attend que le DOM soit complètement chargé."""
    WebDriverWait(driver, timeout).until(is_document_complete)
    write_log("DOM chargé avec succès.", LOG_FILE, "DEBUG")


def wait_until_dom_is_stable(driver, timeout=10):
    """Attend jusqu'à ce que le DOM soit stable (sans changements) pendant un laps de temps donné."""
    previous_dom_snapshot = ""
    unchanged_count = 0
    required_stability_count = 3  # Le nombre de fois où le DOM doit rester stable pour être considéré comme chargé
    
    for _ in range(timeout):
        current_dom_snapshot = driver.page_source  # Récupère l'état actuel du DOM
        
        if current_dom_snapshot == previous_dom_snapshot:
            unchanged_count += 1
        else:
            unchanged_count = 0
        
        if unchanged_count >= required_stability_count:
            write_log("Le DOM est stable.", LOG_FILE, "DEBUG")
            return True
        
        previous_dom_snapshot = current_dom_snapshot
        time.sleep(1)  # Attendre une seconde avant de vérifier à nouveau le DOM
    
    write_log("Le DOM n'est pas complètement stable après le délai.", LOG_FILE, "WARNING")
    return False


def modifier_date_input(date_field, new_date, update_message):
    """Modifie la date dans le champ date_input et affiche un message."""
    date_field.clear()
    date_field.send_keys(new_date)
    write_log(f"{update_message} : {new_date}", LOG_FILE, "DEBUG")


def switch_to_iframe_by_id_or_name(driver, iframe_identifier):
    """Bascule dans l'iframe spécifié par l'ID ou le nom sans attendre sa présence."""
    driver.switch_to.frame(driver.find_element(By.ID, iframe_identifier))
    write_log(f"Bascule dans l'iframe '{iframe_identifier}' réussie.", LOG_FILE, "DEBUG")
    return True


def switch_to_default_content(driver):
    """Revenir au contexte principal du document après avoir travaillé dans un iframe."""
    driver.switch_to.default_content()
    write_log(f"Retour au contexte principal.", LOG_FILE, "DEBUG")


def wait_for_element(driver, by=By.ID, locator_value=None, condition=EC.presence_of_element_located, timeout=10):
    """Attend qu'un élément réponde à une condition, sinon retourne None après le délai."""

    if locator_value is None:
        write_log(f"Erreur : Le paramètre 'locator_value' doit être spécifié pour localiser l'élément.", LOG_FILE, "ERROR")
        return None
    
    found_elements = driver.find_elements(by, locator_value)
    if found_elements:
        matched_element = WebDriverWait(driver, timeout).until(condition((by, locator_value)))
        write_log(f"Élément avec {by}='{locator_value}' trouvé et condition '{condition.__name__}' validée.", LOG_FILE, "DEBUG")
        return matched_element
    else:
        write_log(f"Élément avec {by}='{locator_value}' non trouvé dans le délai imparti ({timeout}s).", LOG_FILE, "WARNING")
        return None


def click_element_without_wait(driver, by, locator_value):
    """Cliquer directement sur un élément spécifié (sans attente)."""
    target_element = driver.find_element(by, locator_value)
    target_element.click()
    write_log(f"Élément {by}='{locator_value}' cliqué avec succès.", LOG_FILE, "DEBUG")


def send_keys_to_element(driver, by, locator_value, input_text):
    """Fonction pour envoyer des touches à un élément spécifié."""
    target_element = driver.find_element(by, locator_value)
    target_element.send_keys(input_text)
    write_log(f"Valeur '{input_text}' envoyée à l'élément {by}='{locator_value}' avec succès.", LOG_FILE, "CRITICAL")


def verifier_champ_jour_rempli(day_field, day_label):
    """Vérifie si une cellule contient une valeur pour un jour spécifique."""
    field_content = day_field.get_attribute("value")
    
    if field_content.strip():
        write_log(f"Jour '{day_label}' contient une valeur : {field_content}", LOG_FILE, "DEBUG")
        return day_label  # On retourne le jour si une valeur est présente
    else:
        write_log(f"Jour '{day_label}' est vide", LOG_FILE, "DEBUG")
        return None  # Rien à faire si l'input est vide


def remplir_champ_texte(day_input_field, day_label, input_value):
    """Remplit une valeur dans l'input d'un jour spécifique si celui-ci est vide."""
    current_content = day_input_field.get_attribute("value")

    if not current_content.strip():
        day_input_field.clear()  # Effacer l'ancienne valeur
        day_input_field.send_keys(input_value)  # Entrer la nouvelle valeur
        write_log(f"Valeur '{input_value}' insérée dans le jour '{day_label}'", LOG_FILE, "DEBUG")
    else:
        write_log(f"Le jour '{day_label}' contient déjà une valeur : {current_content}, rien à changer.", LOG_FILE, "DEBUG")


def detecter_et_verifier_contenu(driver, element_id, input_value):
    """Détecte l'élément et vérifie si le contenu actuel correspond à la valeur cible."""
    try:
        # Rechercher l'élément par son ID
        day_input_field = driver.find_element(By.ID, element_id)
        current_content = day_input_field.get_attribute("value").strip()
        is_correct_value = current_content == input_value
        write_log(f"id trouvé : {element_id} / is_correct_value : {is_correct_value}", LOG_FILE, "DEBUG")
        return day_input_field, is_correct_value
    except NoSuchElementException as e:
        write_log(f"Élément avec id='{element_id}' introuvable. {str(e)}", LOG_FILE, "ERROR")
        raise
    except StaleElementReferenceException as e:
        write_log(f"Référence obsolète pour l'élément id='{element_id}'. {str(e)}", LOG_FILE, "ERROR")
        raise
    except Exception as e:
        write_log(f"Erreur inattendue lors de la détection et de la vérification du contenu : {str(e)}", LOG_FILE, "ERROR")
        raise


def effacer_et_entrer_valeur(day_input_field, input_value):
    """Efface le contenu actuel du champ et entre la nouvelle valeur."""
    day_input_field.clear()
    day_input_field.send_keys(input_value)
    write_log(f"Valeur '{input_value}' insérée dans le champ avec succès.", LOG_FILE, "DEBUG")


def controle_insertion(day_input_field, input_value):
    """Vérifie si la valeur a bien été insérée dans le champ."""
    return day_input_field.get_attribute("value").strip() == input_value


def selectionner_option_menu_deroulant_type_select(dropdown_field, visible_text):
    try:
        select = Select(dropdown_field)
        select.select_by_visible_text(visible_text)
        write_log(f"Valeur '{visible_text}' sélectionnée.", LOG_FILE, "DEBUG")
    except Exception as e:
        write_log(f"Erreur lors de la sélection de la valeur '{visible_text}' : {str(e)}", LOG_FILE, "ERROR")


def trouver_ligne_par_description(driver, target_description, row_prefix, partial_match=False):
    """
    Trouve l'index de la ligne qui correspond à une description spécifique ou partielle dans la table.
    Renvoie l'index de la ligne si trouvé, sinon renvoie None.
    Si partial_match est True, la recherche se fait par correspondance partielle en nettoyant les espaces supplémentaires dans le texte trouvé.
    """
    matched_row_index = None
    row_counter = 0

    while True:
        try:
            # Cherche le span qui correspond à la description de la ligne
            current_description_element = driver.find_element(By.ID, f"{row_prefix}{row_counter}")
            raw_text = current_description_element.text.strip()

            # Nettoyage du texte trouvé : suppression des espaces en trop, tabulations et nouvelles lignes
            cleaned_text = " ".join(raw_text.split())

            # Vérifie si la description correspond à celle recherchée (partielle ou complète)
            if partial_match:
                if target_description in cleaned_text:  # Correspondance partielle avec nettoyage du texte trouvé
                    write_log(f"Ligne trouvée (correspondance partielle) pour '{target_description}' à l'index {row_counter}", LOG_FILE, "DEBUG")
                    matched_row_index = row_counter
                    break
            else:
                if cleaned_text == target_description:  # Correspondance exacte après nettoyage
                    write_log(f"Ligne trouvée pour '{target_description}' à l'index {row_counter}", LOG_FILE, "DEBUG")
                    matched_row_index = row_counter
                    break
            row_counter += 1
        except NoSuchElementException:
            write_log(f"Aucune ligne trouvée pour '{target_description}'.", LOG_FILE, "WARNING")
            break
    return matched_row_index


def detecter_doublons_jours(driver):
    """
    Parcourt toutes les lignes et tous les jours pour vérifier si un même jour a été rempli plus d'une fois.
    Renvoie une alerte si des doublons sont détectés.
    """
    filled_days_tracker = {}  # Dictionnaire pour suivre les jours remplis (clé : jour, valeur : liste des lignes avec des valeurs)

    row_index = 0
    while True:
        try:
            # Cherche le span qui correspond à la description de la ligne
            current_line_description = driver.find_element(By.ID, f"POL_DESCR${row_index}")
            line_description = current_line_description.text.strip()
            write_log(f"Analyse de la ligne '{line_description}' à l'index {row_index}", LOG_FILE, "DEBUG")

            # Parcours tous les jours pour cette ligne
            for day_counter in range(1, 8):  # Dimanche = 1, Samedi = 7
                day_input_id = f"POL_TIME{day_counter}${row_index}"
                
                # Vérifie la présence de l'élément (input pour le jour)
                try:
                    day_field = driver.find_element(By.ID, day_input_id)
                    day_content = day_field.get_attribute("value")

                    if day_content.strip():  # Si le jour contient une valeur
                        day_name = JOURS_SEMAINE[day_counter]  # Obtenir le nom du jour (lundi, mardi, etc.)

                        # Ajouter la ligne à la liste des jours remplis
                        if day_name in filled_days_tracker:
                            filled_days_tracker[day_name].append(line_description)  # Ajouter la ligne actuelle
                        else:
                            filled_days_tracker[day_name] = [line_description]

                except NoSuchElementException:
                    write_log(f"Impossible de trouver l'élément pour le jour '{JOURS_SEMAINE[day_counter]}' avec l'ID '{day_input_id}'", LOG_FILE, "WARNING")

            row_index += 1  # Passer à la ligne suivante

        except NoSuchElementException:
            # Si aucune ligne supplémentaire n'est trouvée, on sort de la boucle
            write_log(f"Fin de l'analyse des lignes à l'index {row_index}", LOG_FILE, "DEBUG")
            break

    # Vérification des doublons dans les jours remplis
    for day_name, lines in filled_days_tracker.items():
        if len(lines) > 1:  # Si plus d'une ligne est remplie pour le même jour
            write_log(f"Doublon détecté pour le jour '{day_name}' dans les lignes : {', '.join(lines)}", LOG_FILE, "WARNING")
        else:
            write_log(f"Aucun doublon détecté pour le jour '{day_name}'", LOG_FILE, "DEBUG")


def ouvrir_navigateur_sur_ecran_principal(plein_ecran=False, url="https://www.example.com", headless=False, no_sandbox=False):
    """Ouvre le navigateur sur un écran principal de l'ordinateur, si necessaire avec des options"""
    edge_browser_options = EdgeOptions()
    edge_browser_options.use_chromium = True

    # Appliquer les arguments selon les choix de l'utilisateur
    if headless:
        edge_browser_options.add_argument("--headless")  # Pour exécuter sans interface graphique
    if no_sandbox:
        edge_browser_options.add_argument("--no-sandbox")

    # Initialiser le navigateur
    browser_instance = webdriver.Edge(options=edge_browser_options)

    # Charger l'URL désirée
    browser_instance.get(url)
    
    # plein écran si choisi
    if plein_ecran:
        browser_instance.maximize_window()

    return browser_instance


def definir_taille_navigateur(navigateur, largeur, hauteur):
    """Définit la taille de la fenêtre du navigateur en pixels"""

    navigateur.set_window_size(largeur, hauteur)

    return navigateur
