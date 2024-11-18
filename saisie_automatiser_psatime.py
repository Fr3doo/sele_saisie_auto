# saisie_automatiser_psatime.py

# Import des bibliothèques nécessaires
import configparser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException, StaleElementReferenceException
from datetime import datetime, timedelta
import time
import sys
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from multiprocessing import shared_memory
from encryption_utils import recuperer_de_memoire_partagee, dechiffrer_donnees ,supprimer_memoire_partagee_securisee
from read_or_write_file_config_ini import read_config_ini

# ----------------------------------------------------------------------------- #
# ------------------------------- CONSTANTE ----------------------------------- #
# ----------------------------------------------------------------------------- #
# # Fichier de configuration
# CONFIG_FILE = 'config.ini'
# # Charger le fichier de configuration
# config = read_config_ini(CONFIG_FILE)

# Charger le fichier de configuration
config = read_config_ini()

# Extraction des informations de connexion
ENCRYPTED_LOGIN = config.get('credentials', 'login')
ENCRYPTED_MDP = config.get('credentials', 'mdp')

# Extraction des paramètres de base
URL = config.get('settings', 'url')
DATE_CIBLE = config.get('settings', 'date_cible')
if DATE_CIBLE.lower() == 'none' or DATE_CIBLE.strip() == '':
    DATE_CIBLE = None

DEBUG_MODE = config.get('settings', 'debug_mode').lower() == 'true'

# Récupérer la liste, split, nettoie les espaces et les double quote
LISTE_ITEMS_DESCRIPTIONS = [item.strip().strip('"') for item in config.get('settings', 'liste_items_planning').split(",")]

# Configuration des jours de travail et congés
JOURS_DE_TRAVAIL = {day: (value.partition(',')[0].strip(), value.partition(',')[2].strip()) for day, value in config.items('work_schedule')}
# Configuration pour les informations additionnelles CGI - France
INFORMATIONS_SUPPLEMENTAIRES_PERIODE_REPOS_RESPECTEE = {day: value for day, value in config.items('additional_information_rest_period_respected')}
INFORMATIONS_SUPPLEMENTAIRES_HORAIRE_TRAVAIL_EFFECTIF = {day: value for day, value in config.items('additional_information_work_time_range')}
INFORMATIONS_SUPPLEMENTAIRES_PLUS_DEMI_JOURNEE_TRAVAILLEE = {day: value for day, value in config.items('additional_information_half_day_worked')}
INFORMATIONS_SUPPLEMENTAIRES_DUREE_PAUSE_DEJEUNER = {day: value for day, value in config.items('additional_information_lunch_break_duration')}
# Configuration des lieux de travail pour chaque jour Matin et Après-midi
LIEU_DU_TRAVAIL_MATIN = {day: value for day, value in config.items('work_location_am')}
LIEU_DU_TRAVAIL_APRES_MIDI = {day: value for day, value in config.items('work_location_pm')}

if DEBUG_MODE:
    # Afficher les configurations chargées (facultatif, pour le debug)
    print("Connexion:")
    print(f"--> Login : {ENCRYPTED_LOGIN}")
    print(f"--> Password : {ENCRYPTED_MDP}")
    print("\nParamètres:")
    print(f"--> URL : {URL}")
    print(f"--> Date cible: {DATE_CIBLE}")
    print("\nPlanning de travail de la semaine:")
    for day, (activity, hours) in JOURS_DE_TRAVAIL.items():
        print(f"--> '{day}': ('{activity}', '{hours}')")
    print("\nInfos_supp_cgi_periode_repos_respectee:")
    for day, status in INFORMATIONS_SUPPLEMENTAIRES_PERIODE_REPOS_RESPECTEE.items():
        print(f"--> '{day}': '{status}'")
    print("\nInfos_supp_cgi_horaire_travail_effectif:")    
    for day, status in INFORMATIONS_SUPPLEMENTAIRES_HORAIRE_TRAVAIL_EFFECTIF.items():
        print(f"--> '{day}': '{status}'")
    print("\nInfos_supp_cgi_demi_journee_travaillee:")
    for day, status in INFORMATIONS_SUPPLEMENTAIRES_PLUS_DEMI_JOURNEE_TRAVAILLEE.items():
        print(f"--> '{day}': '{status}'")
    print("\nInfos_supp_cgi_duree_pause_dejeuner:")    
    for day, status in INFORMATIONS_SUPPLEMENTAIRES_DUREE_PAUSE_DEJEUNER.items():
        print(f"--> '{day}': '{status}'")
    print("\nLieu de travail Matin:")
    for day, location in LIEU_DU_TRAVAIL_MATIN.items():
        print(f"--> '{day}': '{location}'")
    print("\nLieu de travail Apres-midi:")
    for day, location in LIEU_DU_TRAVAIL_APRES_MIDI.items():
        print(f"--> '{day}': '{location}'")

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
TITLE_PROGRAM = "Program PSATime Auto"

TITLE_QUESTION_MENU_ACCUEIL = "Que voulez faire ?"
CHOICE_MENU_ACCUEIL = (
        "Lancer votre PSATime",
        "Configurer le lancement",
        "Quitter le programme"
        )

# Configuration memoire partagée et cryptage
MEMOIRE_PARTAGEE_CLE = "memoire_partagee_cle"
MEMOIRE_PARTAGEE_DONNEES = "memoire_partagee_donnees"
TAILLE_CLE = 32  # 256 bits pour AES-256
TAILLE_BLOC = 128  # Taille de bloc AES pour le padding

# ------------------------------------------------------------------------------------------- #
# ----------------------------------- FONCTIONS --------------------------------------------- #
# ------------------------------------------------------------------------------------------- #
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


def seprateur_menu_affichage():
    print("*************************************************************")


def demander_valeur_numerique_utilisateur(valeur_min, valeur_max):
    v_str = input(f"Donnez une valeur entre {valeur_min} et {valeur_max} : \n --> " )
    try:
        v_int = int(v_str)
    except:
        print("ERREUR : Vous devez rentrer une valeur numérique.")
        print()
        return demander_valeur_numerique_utilisateur(valeur_min, valeur_max)
    if not (valeur_min <= v_int <= valeur_max):
        print(f"ERREUR : Vous devez rentrer un nombre (entre {valeur_min} et {valeur_max} ).")
        print()
        return demander_valeur_numerique_utilisateur(valeur_min, valeur_max)

    return v_int


def afficher_menu_acceuil():
    print()
    print()
    seprateur_menu_affichage()
    print(f"*            {TITLE_PROGRAM}                     *")
    seprateur_menu_affichage()
    print(f"{TITLE_QUESTION_MENU_ACCUEIL}                          ")
    print()
    i = 0
    for items in CHOICE_MENU_ACCUEIL:
        choix_menu = items
        i += 1
        print(f"    {i} - {choix_menu}                              ")
    print("                                                           ")
    seprateur_menu_affichage() 
    valeur_choix_maximale = i
    
    return valeur_choix_maximale


def is_document_complete(driver):
    """Vérifie si le DOM est complètement chargé."""
    return driver.execute_script("return document.readyState") == "complete"


def wait_for_dom_ready(driver, timeout=20):
    """Attend que le DOM soit complètement chargé."""
    WebDriverWait(driver, timeout).until(is_document_complete)
    print("DOM chargé avec succès.")


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
            print("Le DOM est stable.")
            return True
        
        previous_dom_snapshot = current_dom_snapshot
        time.sleep(1)  # Attendre une seconde avant de vérifier à nouveau le DOM
    
    print("Le DOM n'est pas complètement stable après le délai.")
    return False


def get_next_saturday_if_not_saturday(date_str):
    """Retourne le prochain samedi si la date donnée n'est pas déjà un samedi."""
    initial_date = datetime.strptime(date_str, "%d/%m/%Y")
    initial_weekday = initial_date.weekday()
    if initial_weekday != 5:
        days_to_next_saturday = (5 - initial_weekday) % 7
        next_saturday_date = initial_date + timedelta(days=days_to_next_saturday)
        return next_saturday_date.strftime("%d/%m/%Y")
    return date_str


def modifier_date_input(date_field, new_date, update_message):
    """Modifie la date dans le champ date_input et affiche un message."""
    date_field.clear()
    date_field.send_keys(new_date)
    print(f"{update_message} : {new_date}")


def switch_to_iframe_by_id_or_name(driver, iframe_identifier):
    """Bascule dans l'iframe spécifié par l'ID ou le nom sans attendre sa présence."""
    driver.switch_to.frame(driver.find_element(By.ID, iframe_identifier))
    print(f"Bascule dans l'iframe '{iframe_identifier}' réussie.")
    return True


def switch_to_default_content(driver):
    """Revenir au contexte principal du document après avoir travaillé dans un iframe."""
    driver.switch_to.default_content()
    print("Retour au contexte principal.")


def wait_for_element(driver, by=By.ID, locator_value=None, condition=EC.presence_of_element_located, timeout=10):
    """Attend qu'un élément réponde à une condition, sinon retourne None après le délai."""

    if locator_value is None:
        print("Erreur : Le paramètre 'locator_value' doit être spécifié pour localiser l'élément.")
        return None
    
    found_elements = driver.find_elements(by, locator_value)
    if found_elements:
        matched_element = WebDriverWait(driver, timeout).until(condition((by, locator_value)))
        print(f"Élément avec {by}='{locator_value}' trouvé et condition '{condition.__name__}' validée.")
        return matched_element
    else:
        print(f"Élément avec {by}='{locator_value}' non trouvé dans le délai imparti ({timeout}s).")
        return None


def click_element_without_wait(driver, by, locator_value):
    """Cliquer directement sur un élément spécifié (sans attente)."""
    target_element = driver.find_element(by, locator_value)
    target_element.click()
    print(f"Élément {by}='{locator_value}' cliqué avec succès.")


def send_keys_to_element(driver, by, locator_value, input_text):
    """Fonction pour envoyer des touches à un élément spécifié."""
    target_element = driver.find_element(by, locator_value)
    target_element.send_keys(input_text)
    # print(f"Valeur '{input_text}' envoyée à l'élément {by}='{locator_value}' avec succès.")


def verifier_champ_jour_rempli(day_field, day_label):
    """Vérifie si une cellule contient une valeur pour un jour spécifique."""
    field_content = day_field.get_attribute("value")
    
    if field_content.strip():
        print(f"Jour '{day_label}' contient une valeur : {field_content}")
        return day_label  # On retourne le jour si une valeur est présente
    else:
        print(f"Jour '{day_label}' est vide")
        return None  # Rien à faire si l'input est vide


def remplir_champ_texte(day_input_field, day_label, input_value):
    """Remplit une valeur dans l'input d'un jour spécifique si celui-ci est vide."""
    current_content = day_input_field.get_attribute("value")

    if not current_content.strip():
        day_input_field.clear()  # Effacer l'ancienne valeur
        day_input_field.send_keys(input_value)  # Entrer la nouvelle valeur
        print(f"Valeur '{input_value}' insérée dans le jour '{day_label}'")
    else:
        print(f"Le jour '{day_label}' contient déjà une valeur : {current_content}, rien à changer.")


def detecter_et_verifier_contenu(driver, element_id, input_value):
    """Détecte l'élément et vérifie si le contenu actuel correspond à la valeur cible."""
    day_input_field = driver.find_element(By.ID, element_id)
    current_content = day_input_field.get_attribute("value").strip()
    return day_input_field, current_content == input_value


def effacer_et_entrer_valeur(day_input_field, input_value):
    """Efface le contenu actuel du champ et entre la nouvelle valeur."""
    day_input_field.clear()
    day_input_field.send_keys(input_value)
    print(f"Valeur '{input_value}' insérée dans le champ avec succès.")


def controle_insertion(day_input_field, input_value):
    """Vérifie si la valeur a bien été insérée dans le champ."""
    return day_input_field.get_attribute("value").strip() == input_value


def selectionner_option_menu_deroulant_type_select(dropdown_field, visible_text):
    try:
        select = Select(dropdown_field)
        select.select_by_visible_text(visible_text) 
        print(f"Valeur '{visible_text}' sélectionnée.")
    except Exception as e:
        print(f"Erreur lors de la sélection de la valeur '{visible_text}' : {str(e)}")


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
                    print(f"Ligne trouvée (correspondance partielle) pour '{target_description}' à l'index {row_counter}")
                    matched_row_index = row_counter
                    break
            else:
                if cleaned_text == target_description:  # Correspondance exacte après nettoyage
                    print(f"Ligne trouvée pour '{target_description}' à l'index {row_counter}")
                    matched_row_index = row_counter
                    break
            row_counter += 1
        except NoSuchElementException:
            print(f"Aucune ligne trouvée pour '{target_description}'.")
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

            print(f"Analyse de la ligne '{line_description}' à l'index {row_index}")

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
                    print(f"Impossible de trouver l'élément pour le jour '{JOURS_SEMAINE[day_counter]}' avec l'ID '{day_input_id}'")

            row_index += 1  # Passer à la ligne suivante

        except NoSuchElementException:
            # Si aucune ligne supplémentaire n'est trouvée, on sort de la boucle
            print(f"Fin de l'analyse des lignes à l'index {row_index}")
            break

    # Vérification des doublons dans les jours remplis
    for day_name, lines in filled_days_tracker.items():
        if len(lines) > 1:  # Si plus d'une ligne est remplie pour le même jour
            print(f"Doublon détecté pour le jour '{day_name}' dans les lignes : {', '.join(lines)}")
        else:
            print(f"Aucun doublon détecté pour le jour '{day_name}'")


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
        print(f"Valeur '{valeur}' confirmée pour le jour '{jour}' ({message}{tentative + 1})")
    else:
        print(f"Valeur '{valeur}' confirmée pour le jour '{jour}' {message})")
        
# ------------------------------------------------------------------------------------------------------------------ #
# -------------------------------------------- CODE PRINCIPAL ------------------------------------------------------ #
# ------------------------------------------------------------------------------------------------------------------ #
def main():
    memoire_nom = None
    memoire_mdp = None
    memoire_cle = None
    taille_nom = None
    try:
        # Récupérer la clé depuis la mémoire partagée
        memoire_cle, cle_aes = recuperer_de_memoire_partagee(MEMOIRE_PARTAGEE_CLE, TAILLE_CLE)
        # print(f"Clé AES-256 récupérée : {cle_aes.hex()}")

        # Récupérer les données chiffrées depuis la mémoire partagée
        memoire_nom = shared_memory.SharedMemory(name="memoire_nom")
        taille_nom = len(bytes(memoire_nom.buf).rstrip(b"\x00"))
        nom_utilisateur_chiffre = bytes(memoire_nom.buf[:taille_nom])
        # print(f"Taille récupérée pour le nom d'utilisateur chiffré : {len(nom_utilisateur_chiffre)}")

        memoire_mdp = shared_memory.SharedMemory(name="memoire_mdp")
        taille_mdp = len(bytes(memoire_mdp.buf).rstrip(b"\x00"))
        mot_de_passe_chiffre = bytes(memoire_mdp.buf[:taille_mdp])
        # print(f"Taille récupérée pour le mot de passe chiffré : {len(mot_de_passe_chiffre)}")

        # Déchiffrer les données
        nom_utilisateur = dechiffrer_donnees(nom_utilisateur_chiffre, cle_aes)
        mot_de_passe = dechiffrer_donnees(mot_de_passe_chiffre, cle_aes)

        # print(f"Nom d'utilisateur déchiffré : {nom_utilisateur}")
        # print(f"Mot de passe déchiffré : {mot_de_passe}")
        
        # Démarrer le navigateur
        driver = ouvrir_navigateur_sur_ecran_principal(
            plein_ecran=False,
            url=URL,
            headless=False,  # Activez ou désactivez le mode headless
            no_sandbox=False  # Activez ou désactivez le mode no-sandbox
        )
        
        # Utilisation de la fonction avec des dimensions spécifiques
        driver = definir_taille_navigateur(driver, 1260, 800)
        
        # Vérifie si le DOM est complètement chargé.
        wait_for_dom_ready(driver, LONG_TIMEOUT)
        
        # Connexion
        send_keys_to_element(driver, By.ID, "userid", nom_utilisateur)
        send_keys_to_element(driver, By.ID, "pwd", mot_de_passe)
        send_keys_to_element(driver, By.ID, "pwd", Keys.RETURN)
        
        # Attendre que le DOM soit stable
        wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)
        
        # chargé le DOM de page
        wait_for_dom_ready(driver, LONG_TIMEOUT)
        
        # Verifier la présence et Interagir avec l'élément
        element_present = wait_for_element(driver, By.ID, "PTNUI_LAND_REC14$0_row_0", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
        if element_present:
            click_element_without_wait(driver, By.ID, "PTNUI_LAND_REC14$0_row_0")
        
        # Attendre que le DOM soit stable
        wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)
        
        # chargé le DOM de page
        wait_for_dom_ready(driver, LONG_TIMEOUT)

        # Verifier la présence et Cliquer sur le bouton "panel" pour le fermer
        element_present = wait_for_element(driver, By.ID, "PT_SIDE$PIMG", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
        if element_present:
            click_element_without_wait(driver, By.ID, "PT_SIDE$PIMG")


        # Attendre que l'iframe soit chargé avant de basculer
        element_present = wait_for_element(driver, By.ID, "main_target_win0", timeout=DEFAULT_TIMEOUT)
        if element_present:
            switched_to_iframe = switch_to_iframe_by_id_or_name(driver, "main_target_win0")  # Remplace par l'ID exact de l'iframe

        if switched_to_iframe:
            # Attendre que l'élément "EX_TIME_ADD_VW_PERIOD_END_DT" soit présent dans l'iframe
            date_input = wait_for_element(driver, By.ID ,"EX_TIME_ADD_VW_PERIOD_END_DT", timeout=DEFAULT_TIMEOUT)
            
            if date_input:
                if DATE_CIBLE and DATE_CIBLE.strip(): # si la date est none ou vide
                    # Utiliser la date cible
                    modifier_date_input(date_input, DATE_CIBLE, "Date modifiée par defaut vers la date cible")
                else:
                    # Sinon, appliquer la logique de prochain samedi
                    current_date_value = date_input.get_attribute("value")
                    new_date_value = get_next_saturday_if_not_saturday(current_date_value)

                    if new_date_value != current_date_value:
                        modifier_date_input(date_input, new_date_value, "Date modifiée au prochain samedi")
                    else:
                        print("Aucune modification nécessaire, date actuelle conservée.")

            # Verifier la présence et Cliquer sur le bouton "Ajout"
            element_present = wait_for_element(driver, By.ID, "PTS_CFG_CL_WRK_PTS_ADD_BTN", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
            if element_present:
                click_element_without_wait(driver, By.ID, "PTS_CFG_CL_WRK_PTS_ADD_BTN")

                # Attendre que le DOM soit stable
                wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)
                # chargé le DOM de page
                wait_for_dom_ready(driver, LONG_TIMEOUT)

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
                            print("\nERREUR : Vous avez déjà créé une feuille de temps pour cette période. (10502,125)\n"
                                "--> Modifier la date du PSATime dans le fichier ini. Le programme va s'arreter.")

                        # Arrêter le script. Utilisez sys.exit() pour une sortie propre
                        sys.exit()
                else:
                    print("Date validée avec succès.")
        
        # Attendre que le DOM soit stable
        wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)
        # chargé le DOM de page
        wait_for_dom_ready(driver, LONG_TIMEOUT)

        # Attendre que l'iframe soit chargé avant de basculer
        element_present = wait_for_element(driver, By.ID, "main_target_win0", timeout=DEFAULT_TIMEOUT)
        if element_present:
            switched_to_iframe = switch_to_iframe_by_id_or_name(driver, "main_target_win0")

        # Attendre que le DOM soit stable
        wait_until_dom_is_stable(driver, timeout=LONG_TIMEOUT)
        # chargé le DOM de page
        wait_for_dom_ready(driver, timeout=LONG_TIMEOUT)

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

        # Attendre que le DOM soit stable
        wait_until_dom_is_stable(driver, timeout=LONG_TIMEOUT)

        # chargé le DOM de page
        wait_for_dom_ready(driver, timeout=LONG_TIMEOUT)

        jours_remplis = []  # Liste pour suivre les jours déjà remplis
        max_attempts = 5
        # Parcourir chaque description dans LISTE_ITEMS_DESCRIPTIONS
        for description_cible in LISTE_ITEMS_DESCRIPTIONS:
            # Recherche de la ligne avec la description spécifiée pour le jour
            id_value = "POL_DESCR$"
            row_index = trouver_ligne_par_description(driver, description_cible, id_value)

            # Si la ligne est trouvée, remplir les jours de la semaine
            if row_index is not None:
                for jour_index, jour_name in JOURS_SEMAINE.items():  # Dimanche = 1, Lundi = 2, etc.
                    input_id = f"POL_TIME{jour_index}${row_index}"

                    # Vérifier la présence de l'élément
                    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

                    if element:
                        # Vérifier s'il y a une valeur dans l'élément pour ce jour
                        jour_rempli = verifier_champ_jour_rempli(element, jour_name)
                        if jour_rempli:
                            jours_remplis.append(jour_rempli) # Ajouter le jour s'il est déjà rempli
        
        clear_screen()

        # Remplir les jours du dimanche au samedi, s'ils sont encore vides.
        for jour, (description_cible, valeur_a_remplir) in JOURS_DE_TRAVAIL.items():
            attempt = 0
            if description_cible and not est_en_mission(description_cible) and jour not in jours_remplis:  # Remplir seulement si le jour est vide
                id_value = "POL_DESCR$"
                row_index = trouver_ligne_par_description(driver, description_cible, id_value)
                
                if row_index is not None:
                    jour_index = list(JOURS_SEMAINE.keys())[list(JOURS_SEMAINE.values()).index(jour)]
                    input_id = f"POL_TIME{jour_index}${row_index}"
                    
                    # Vérifier la présence de l'élément
                    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)
                    
                    if element:
                        while attempt < max_attempts:
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

                                # Étape 3 : Contrôler que la valeur est bien insérée
                                if controle_insertion(day_input_field, valeur_a_remplir):
                                    jours_remplis = ajouter_jour_a_jours_remplis(jour, jours_remplis)
                                    afficher_message_insertion(jour, valeur_a_remplir, attempt, "après insertion")
                                    break

                            except StaleElementReferenceException:
                                print(f"Référence obsolète pour '{jour}', tentative {attempt + 1}")
                            
                            attempt += 1

                        # Si toutes les tentatives échouent, indiquer un message d'échec
                        if attempt == max_attempts:
                            print(f"Échec de l'insertion de la valeur '{valeur_a_remplir}' dans le jour '{jour}' après {max_attempts} tentatives.")

            elif description_cible and est_en_mission(description_cible) and jour not in jours_remplis:
                # Cas où description_cible est "En mission", on écrit directement dans les IDs spécifiques sans utiliser `description_cible`
                jour_index = list(JOURS_SEMAINE.keys())[list(JOURS_SEMAINE.values()).index(jour)]
                input_id = f"TIME{jour_index}$0"  # Définir l'ID de l'élément pour ce jour
                
                # Vérifier la présence de l'élément
                element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

                if element:
                    while attempt < max_attempts:
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

                            # Étape 3 : Contrôler que la valeur est bien insérée
                            if controle_insertion(day_input_field, valeur_a_remplir):
                                jours_remplis = ajouter_jour_a_jours_remplis(jour, jours_remplis)
                                afficher_message_insertion(jour, valeur_a_remplir, attempt, "après insertion")
                                break

                        except StaleElementReferenceException:
                            print(f"Référence obsolète pour '{jour}', tentative {attempt + 1}")
                        
                        attempt += 1

                    # Si toutes les tentatives échouent, indiquer un message d'échec
                    if attempt == max_attempts:
                        print(f"Échec de l'insertion de la valeur '{valeur_a_remplir}' dans le jour '{jour}' après {max_attempts} tentatives.")

        # Attendre que le DOM soit stable
        wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)

        # chargé le DOM de page
        wait_for_dom_ready(driver, LONG_TIMEOUT)

        element_present = wait_for_element(driver, By.ID, "UC_EX_WRK_UC_TI_FRA_LINK", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
        if element_present:
            click_element_without_wait(driver, By.ID, "UC_EX_WRK_UC_TI_FRA_LINK")

        # Revenir au contexte principal du document
        switch_to_default_content(driver)
        
        # Attendre que le DOM soit stable
        wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)

        # chargé le DOM de page
        wait_for_dom_ready(driver, LONG_TIMEOUT)
        
        # ---------------------------- #
        # -- Sommaire feuille temps -- #
        # ---------------------------- #
        # Attendre que l'iframe soit chargé avant de basculer
        element_present = wait_for_element(driver, By.ID, "ptModFrame_0", timeout=DEFAULT_TIMEOUT)
        if element_present:
            switched_to_iframe = switch_to_iframe_by_id_or_name(driver, "ptModFrame_0")  # Remplace par l'ID exact de l'iframe

        if switched_to_iframe:
            # 1. Recherche de la ligne avec la description
            description_cible = "Temps de repos de 11h entre 2 jours travaillés respecté"
            id_value = "DESCR100$"
            row_index = trouver_ligne_par_description(driver, description_cible, id_value)
            jours_remplis = []  # Liste pour suivre les jours déjà remplis
            type_element = "select"  # Indiquer que les éléments sont des <select>
            
            # Si la ligne est trouvée, remplir les jours de la semaine
            if row_index is not None:
                # 2. Boucle pour parcourir tous les jours (dimanche à samedi)
                for i in range(1, 8):  # Dimanche = 1, Samedi = 7
                    input_id = f"UC_DAILYREST{i}${row_index}"

                    # Vérifier la présence de l'élément
                    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

                    if element:
                        jour = JOURS_SEMAINE[i]
                        # Vérifier s'il y a une valeur dans l'élément pour ce jour
                        jour_rempli = verifier_champ_jour_rempli(element, jour)
                        if jour_rempli:
                            jours_remplis.append(jour_rempli)

                # 3. Remplir les jours du lundi au vendredi s'ils sont encore vides.
                for i in range(1, 8):  # Dimanche = 1, Samedi = 7
                    input_id = f"UC_DAILYREST{i}${row_index}"

                    # Vérifier la présence de l'élément
                    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

                    if element:
                        jour = JOURS_SEMAINE[i]
                        # Récupérer la valeur spécifique pour le jour
                        valeur_a_remplir = INFORMATIONS_SUPPLEMENTAIRES_PERIODE_REPOS_RESPECTEE[jour]
                        # Remplir l'élément si nécessaire
                        if jour not in jours_remplis:
                            if type_element == "select":
                                selectionner_option_menu_deroulant_type_select(element, valeur_a_remplir)
                            elif type_element == "input":
                                remplir_champ_texte(element, jour, valeur_a_remplir)
            
            #--------------------------------------------------------------------------------#
            # 1. Recherche de la ligne avec la description
            description_cible = "Mon temps de travail effectif a débuté entre 8h00 et 10h00 et Mon temps de travail effectif a pris fin entre 16h30 et 19h00"
            id_value = "DESCR100$"
            row_index = trouver_ligne_par_description(driver, description_cible, id_value, partial_match=True)
            jours_remplis = []  # Liste pour suivre les jours déjà remplis
            type_element = "select"  # Indiquer que les éléments sont des <select>
            
            # Si la ligne est trouvée, remplir les jours de la semaine
            if row_index is not None:
                # 2. Boucle pour parcourir tous les jours (dimanche à samedi)
                for i in range(1, 8):  # Dimanche = 1, Samedi = 7
                    input_id = f"UC_DAILYREST{i}${row_index}"

                    # Vérifier la présence de l'élément
                    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

                    if element:
                        jour = JOURS_SEMAINE[i]
                        # Vérifier s'il y a une valeur dans l'élément pour ce jour
                        jour_rempli = verifier_champ_jour_rempli(element, jour)
                        if jour_rempli:
                            jours_remplis.append(jour_rempli)

                # 3. Remplir les jours du lundi au vendredi s'ils sont encore vides.
                for i in range(1, 8):  # Dimanche = 1, Samedi = 7
                    input_id = f"UC_DAILYREST{i}${row_index}"

                    # Vérifier la présence de l'élément
                    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

                    if element:
                        jour = JOURS_SEMAINE[i]
                        # Récupérer la valeur spécifique pour le jour
                        valeur_a_remplir = INFORMATIONS_SUPPLEMENTAIRES_HORAIRE_TRAVAIL_EFFECTIF[jour]
                        # Remplir l'élément si nécessaire
                        if jour not in jours_remplis:
                            if type_element == "select":
                                selectionner_option_menu_deroulant_type_select(element, valeur_a_remplir)
                            elif type_element == "input":
                                remplir_champ_texte(element, jour, valeur_a_remplir)
            
            #--------------------------------------------------------------------------------#
            # 1. Recherche de la ligne avec la description
            description_cible = "J’ai travaillé plus d’une demi-journée"
            id_value = "DESCR100$"
            row_index = trouver_ligne_par_description(driver, description_cible, id_value)
            jours_remplis = []  # Liste pour suivre les jours déjà remplis
            type_element = "select"  # Indiquer que les éléments sont des <select>
            
            # Si la ligne est trouvée, remplir les jours de la semaine
            if row_index is not None:
                # 2. Boucle pour parcourir tous les jours (dimanche à samedi)
                for i in range(1, 8):  # Dimanche = 1, Samedi = 7
                    input_id = f"UC_DAILYREST{i}${row_index}"

                    # Vérifier la présence de l'élément
                    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

                    if element:
                        jour = JOURS_SEMAINE[i]
                        # Vérifier s'il y a une valeur dans l'élément pour ce jour
                        jour_rempli = verifier_champ_jour_rempli(element, jour)
                        if jour_rempli:
                            jours_remplis.append(jour_rempli)

                # 3. Remplir les jours du lundi au vendredi s'ils sont encore vides.
                for i in range(1, 8):  # Dimanche = 1, Samedi = 7
                    input_id = f"UC_DAILYREST{i}${row_index}"

                    # Vérifier la présence de l'élément
                    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

                    if element:
                        jour = JOURS_SEMAINE[i]
                        # Récupérer la valeur spécifique pour le jour
                        valeur_a_remplir = INFORMATIONS_SUPPLEMENTAIRES_PLUS_DEMI_JOURNEE_TRAVAILLEE[jour]
                        # Remplir l'élément si nécessaire
                        if jour not in jours_remplis:
                            if type_element == "select":
                                selectionner_option_menu_deroulant_type_select(element, valeur_a_remplir)
                            elif type_element == "input":
                                remplir_champ_texte(element, jour, valeur_a_remplir)
            
            #--------------------------------------------------------------------------------#
            # 1. Recherche de la ligne avec la description
            description_cible = "Durée de la pause déjeuner"
            id_value = "UC_TIME_LIN_WRK_DESCR200$"
            row_index = trouver_ligne_par_description(driver, description_cible, id_value)
            jours_remplis = []  # Liste pour suivre les jours déjà remplis
            type_element = "input"  # Indiquer que les éléments sont des <select>

            # Si la ligne est trouvée, remplir les jours de la semaine
            if row_index is not None:
                # 2. Boucle pour parcourir tous les jours (dimanche à samedi)
                id = 10
                for i in range(1, 8):  # Dimanche = 1, Samedi = 7
                    input_id = f"UC_TIME_LIN_WRK_UC_DAILYREST{id+i}$0"  # Créer l'ID correspondant

                    # Vérifier la présence de l'élément
                    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

                    if element:
                        jour = JOURS_SEMAINE[i]
                        # Vérifier s'il y a une valeur dans l'élément pour ce jour
                        jour_rempli = verifier_champ_jour_rempli(element, jour)
                        if jour_rempli:
                            jours_remplis.append(jour_rempli)
                                
                                
                # 3. Remplir les jours du lundi au vendredi s'ils sont encore vides.
                for i in range(1, 8): # Dimanche = 1, Samedi = 7
                    input_id = f"UC_TIME_LIN_WRK_UC_DAILYREST{id+i}$0"  # Créer l'ID correspondant

                    # Vérifier la présence de l'élément
                    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

                    if element:
                        jour = JOURS_SEMAINE[i]
                        # Récupérer la valeur spécifique pour le jour
                        valeur_a_remplir = INFORMATIONS_SUPPLEMENTAIRES_DUREE_PAUSE_DEJEUNER[jour]
                        # Remplir l'élément si nécessaire
                        if jour not in jours_remplis:
                            if type_element == "select":
                                selectionner_option_menu_deroulant_type_select(element, valeur_a_remplir)
                            elif type_element == "input":
                                remplir_champ_texte(element, jour, valeur_a_remplir)

            #--------------------------------------------------------------------------------#
            # 1. Recherche de la ligne avec la description
            description_cible = "Matin"
            id_value = "DESCR$"
            row_index = trouver_ligne_par_description(driver, description_cible, id_value)
            jours_remplis = []  # Liste pour suivre les jours déjà remplis
            type_element = "select"  # Indiquer que les éléments sont des <select>
            
            # Si la ligne est trouvée, remplir les jours de la semaine
            if row_index is not None:
                # 2. Boucle pour parcourir tous les jours (dimanche à samedi)
                for i in range(1, 8):  # Dimanche = 1, Samedi = 7
                    input_id = f"UC_LOCATION_A{i}${row_index}"

                    # Vérifier la présence de l'élément
                    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

                    if element:
                        jour = JOURS_SEMAINE[i]
                        # Vérifier s'il y a une valeur dans l'élément pour ce jour
                        jour_rempli = verifier_champ_jour_rempli(element, jour)
                        if jour_rempli:
                            jours_remplis.append(jour_rempli)

                # 3. Remplir les jours du lundi au vendredi s'ils sont encore vides.
                for i in range(1, 8):  # Dimanche = 1, Samedi = 7
                    input_id = f"UC_LOCATION_A{i}${row_index}"

                    # Vérifier la présence de l'élément
                    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

                    if element:
                        jour = JOURS_SEMAINE[i]
                        # Récupérer la valeur spécifique pour le jour
                        valeur_a_remplir = LIEU_DU_TRAVAIL_MATIN[jour]
                        # Remplir l'élément si nécessaire
                        if jour not in jours_remplis:
                            if type_element == "select":
                                selectionner_option_menu_deroulant_type_select(element, valeur_a_remplir)
                            elif type_element == "input":
                                remplir_champ_texte(element, jour, valeur_a_remplir)

            #--------------------------------------------------------------------------------#
            # 1. Recherche de la ligne avec la description
            description_cible = "Après-midi"
            id_value = "DESCR$"
            row_index = trouver_ligne_par_description(driver, description_cible, id_value)
            jours_remplis = []  # Liste pour suivre les jours déjà remplis
            type_element = "select"  # Indiquer que les éléments sont des <select>
            
            # Si la ligne est trouvée, remplir les jours de la semaine
            if row_index is not None:
                # 2. Boucle pour parcourir tous les jours (dimanche à samedi)
                for i in range(1, 8):  # Dimanche = 1, Samedi = 7
                    input_id = f"UC_LOCATION_A{i}${row_index}"

                    # Vérifier la présence de l'élément
                    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

                    if element:
                        jour = JOURS_SEMAINE[i]
                        # Vérifier s'il y a une valeur dans l'élément pour ce jour
                        jour_rempli = verifier_champ_jour_rempli(element, jour)
                        if jour_rempli:
                            jours_remplis.append(jour_rempli)

                # 3. Remplir les jours du lundi au vendredi s'ils sont encore vides.
                for i in range(1, 8):  # Dimanche = 1, Samedi = 7
                    input_id = f"UC_LOCATION_A{i}${row_index}"

                    # Vérifier la présence de l'élément
                    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

                    if element:
                        jour = JOURS_SEMAINE[i]
                        # Récupérer la valeur spécifique pour le jour
                        valeur_a_remplir = LIEU_DU_TRAVAIL_APRES_MIDI[jour]
                        # Remplir l'élément si nécessaire
                        if jour not in jours_remplis:
                            if type_element == "select":
                                selectionner_option_menu_deroulant_type_select(element, valeur_a_remplir)
                            elif type_element == "input":
                                remplir_champ_texte(element, jour, valeur_a_remplir)

        # Verifier la présence et Cliquer sur le bouton "OK"
        element_present = wait_for_element(driver, By.ID, "#ICSave", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
        if element_present:
            click_element_without_wait(driver, By.ID, "#ICSave")

        # Revenir au contexte principal du document
        switch_to_default_content(driver)
        
        # Attendre que le DOM soit stable
        wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)

        # chargé le DOM de page
        wait_for_dom_ready(driver, LONG_TIMEOUT)

        # Attendre que l'iframe soit chargé avant de basculer
        element_present = wait_for_element(driver, By.ID, "main_target_win0", timeout=DEFAULT_TIMEOUT)
        if element_present:
            switched_to_iframe = switch_to_iframe_by_id_or_name(driver, "main_target_win0")  # Remplace par l'ID exact de l'iframe

        if switched_to_iframe:
            # Contrôle après avoir rempli les jours
            detecter_doublons_jours(driver)
            
            # Verifier la présence et Cliquer sur le bouton "Enreg. brouill."
            element_present = wait_for_element(driver, By.ID, "EX_ICLIENT_WRK_SAVE_PB", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
            if element_present:
                click_element_without_wait(driver, By.ID, "EX_ICLIENT_WRK_SAVE_PB")

                # Attendre que le DOM soit stable
                wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)
                # chargé le DOM de page
                wait_for_dom_ready(driver, LONG_TIMEOUT)

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
                            print("\nWARNING : Assurez-vous d’avoir choisi la bonne date pour votre relevé d’heures. (24500,19)")
                            input("--> Appuyez sur Entrée pour continuer.")  
                        elif alerte == alertes[1]:
                            # Cliquer sur le bouton "OK" pour fermer l'alerte et indiquer à l'utilisateur le warning
                            click_element_without_wait(driver, By.ID, "#ICOK")
                            print("\nWARNING : Un jour de la semaine est un jour férié. Ces heures n'ont pas été saisies comme telles. (24500,427).")
                            input("--> Appuyez sur Entrée pour fermer le navigateur.")  
                        elif alerte == alertes[2]:
                            # Cliquer sur le bouton "OK" pour fermer l'alerte et indiquer à l'utilisateur le warning
                            click_element_without_wait(driver, By.ID, "#ICOK")
                            print("\nWARNING : Il existe un écart avec vos absences approuvées dans le Centre de service RH (24500,320)")
                            input("--> Appuyez sur Entrée pour fermer le navigateur.")    
                        break # Arrêter la boucle une fois la ou les alerte(s) traitée(s)
                    

        # Attendre que le DOM soit stable
        wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)
        # chargé le DOM de page
        wait_for_dom_ready(driver, LONG_TIMEOUT)

        # Attendre que l'iframe soit chargé avant de basculer
        element_present = wait_for_element(driver, By.ID, "main_target_win0", timeout=DEFAULT_TIMEOUT)
        if element_present:
            switched_to_iframe = switch_to_iframe_by_id_or_name(driver, "main_target_win0")
        
        # Attendre que le DOM soit stable
        wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)

        # chargé le DOM de page
        wait_for_dom_ready(driver, LONG_TIMEOUT)

        # Attendre que l'iframe soit chargé avant de basculer
        # element_present = wait_for_element(driver, By.ID, "ptModFrame_1", timeout=DEFAULT_TIMEOUT)
        # if element_present:
        #     switched_to_iframe = switch_to_iframe_by_id_or_name(driver, "ptModFrame_1")

        # Verifier la présence et Cliquer sur le bouton "OK"
        # element_present = wait_for_element(driver, By.ID, "#ICSave", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
        # if element_present:
        #     click_element_without_wait(driver, By.ID, "#ICSave")

        # Verifier la présence et Cliquer sur le bouton "Soumettre pour approb."
        # element_present = wait_for_element(driver, By.ID, "EX_TIME_HDR_WRK_PB_SUBMIT", EC.element_to_be_clickable, timeout=DEFAULT_TIMEOUT)
        # if element_present:
        #     click_element_without_wait(driver, By.ID, "EX_TIME_HDR_WRK_PB_SUBMIT")

    except NoSuchElementException as e:
        print(f"L'élément n'a pas été trouvé : {str(e)}")
    except TimeoutException as e:
        print(f"Temps d'attente dépassé pour un élément : {str(e)}")
    except WebDriverException as e:
        print(f"Erreur liée au WebDriver : {str(e)}")
    except Exception as e:
        print(f"Erreur inattendue : {str(e)}")

    finally:
        try:
            seprateur_menu_affichage()
        except ValueError:
            pass  # Ignore toute erreur
        finally:
            # Suppression sécurisée des mémoires partagées
            if memoire_cle is not None:
                supprimer_memoire_partagee_securisee(memoire_cle)
            if memoire_nom is not None:
                supprimer_memoire_partagee_securisee(memoire_nom)
            if memoire_mdp is not None:
                supprimer_memoire_partagee_securisee(memoire_mdp)
            
            print("[FIN] Clé et données supprimées de manière sécurisée, des mémoires partagées du fichier saisie_automatiser_psatime.")
            driver.quit()


            
