# pragma: no cover
# remplir_jours_feuille_de_temps.py

# Import des bibliothèques nécessaires
from typing import Optional

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By

from constants import ID_TO_KEY_MAPPING, JOURS_SEMAINE, LISTES_ID_INFORMATIONS_MISSION
from dropdown_options import (
    cgi_options_billing_action as DEFAULT_CGI_OPTIONS_BILLING_ACTION,
)
from error_handler import log_error
from logger_utils import write_log
from read_or_write_file_config_ini_utils import read_config_ini
from selenium_utils import (
    controle_insertion,
    detecter_et_verifier_contenu,
    effacer_et_entrer_valeur,
)
from selenium_utils import set_log_file as set_log_file_selenium
from selenium_utils import (
    trouver_ligne_par_description,
    verifier_champ_jour_rempli,
    wait_for_dom_ready,
    wait_for_element,
    wait_until_dom_is_stable,
)
from shared_utils import program_break_time

# ------------------------------------------------------------------------------------------- #
# ----------------------------------- CONSTANTE --------------------------------------------- #
# ------------------------------------------------------------------------------------------- #
# Variables initialisées lors de l'``initialize``
LOG_FILE: Optional[str] = None
config = None
LISTE_ITEMS_DESCRIPTIONS = []
JOURS_DE_TRAVAIL = {}
INFORMATIONS_PROJET_MISSION = {}

MAX_ATTEMPTS = 5
DEFAULT_TIMEOUT = 10  # Délai d'attente par défaut
LONG_TIMEOUT = 20


def initialize(log_file: str) -> None:
    """Initialise la configuration du module."""
    global LOG_FILE, config, LISTE_ITEMS_DESCRIPTIONS, JOURS_DE_TRAVAIL, INFORMATIONS_PROJET_MISSION

    LOG_FILE = log_file
    set_log_file_selenium(log_file)
    config = read_config_ini(log_file)
    LISTE_ITEMS_DESCRIPTIONS = [
        item.strip().strip('"')
        for item in config.get("settings", "liste_items_planning").split(",")
    ]
    JOURS_DE_TRAVAIL = {
        day: (value.partition(",")[0].strip(), value.partition(",")[2].strip())
        for day, value in config.items("work_schedule")
    }
    billing_map = (
        dict(config.items("cgi_options_billing_action"))
        if config.has_section("cgi_options_billing_action")
        else DEFAULT_CGI_OPTIONS_BILLING_ACTION
    )
    INFORMATIONS_PROJET_MISSION = {
        item_projet: billing_map.get(value.lower(), value)
        for item_projet, value in config.items("project_information")
    }


# ----------------------------------------------------------------------------- #
# ------------------------------- UTILITIES ----------------------------------- #
# ----------------------------------------------------------------------------- #


def wait_for_dom(driver):
    wait_until_dom_is_stable(
        driver, timeout=DEFAULT_TIMEOUT
    )  # Attendre que le DOM soit stable
    wait_for_dom_ready(driver, LONG_TIMEOUT)  # chargé le DOM de page


def clear_screen():
    """Clear console output."""
    import os

    os.system("cls" if os.name == "nt" else "clear")  # nosec B605


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
        write_log(
            f"⚠️ Valeur '{valeur}' confirmée pour le jour '{jour}' ({message}{tentative + 1})",
            LOG_FILE,
            "DEBUG",
        )
    else:
        write_log(
            f"⚠️ Valeur '{valeur}' confirmée pour le jour '{jour}' {message})",
            LOG_FILE,
            "DEBUG",
        )


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
                element = wait_for_element(
                    driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT
                )

                if element:
                    # Vérifier s'il y a une valeur dans l'élément pour ce jour
                    jour_rempli = verifier_champ_jour_rempli(element, jour_name)
                    if jour_rempli:
                        jours_remplis.append(
                            jour_rempli
                        )  # Ajouter le jour s'il est déjà rempli

    return jours_remplis


def traiter_jour(driver, jour, description_cible, valeur_a_remplir, jours_remplis):
    """Traiter un jour spécifique pour le remplissage."""
    attempt = 0

    if jour in jours_remplis or not description_cible:
        return jours_remplis

    id_value = "POL_DESCR$"
    row_index = trouver_ligne_par_description(driver, description_cible, id_value)

    if row_index is not None:
        jour_index = list(JOURS_SEMAINE.keys())[
            list(JOURS_SEMAINE.values()).index(jour)
        ]
        input_id = f"POL_TIME{jour_index}${row_index}"

        # Vérifier la présence de l'élément
        element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

        if element:
            while attempt < MAX_ATTEMPTS:
                try:
                    # Étape 1 : Détection et vérification du contenu actuel
                    day_input_field, is_correct_value = detecter_et_verifier_contenu(
                        driver, input_id, valeur_a_remplir
                    )

                    if is_correct_value:
                        jours_remplis = ajouter_jour_a_jours_remplis(
                            jour, jours_remplis
                        )
                        afficher_message_insertion(
                            jour, valeur_a_remplir, attempt, "tentative d'insertion n°"
                        )
                        break

                    # Étape 2 : Effacer et entrer la nouvelle valeur
                    effacer_et_entrer_valeur(day_input_field, valeur_a_remplir)
                    program_break_time(
                        1, "Veuillez patienter. Court délai pour stabilisation du DOM"
                    )
                    print()

                    # Étape 3 : Contrôler que la valeur est bien insérée
                    if controle_insertion(day_input_field, valeur_a_remplir):
                        jours_remplis = ajouter_jour_a_jours_remplis(
                            jour, jours_remplis
                        )
                        afficher_message_insertion(
                            jour, valeur_a_remplir, attempt, "après insertion"
                        )
                        break

                except StaleElementReferenceException:
                    write_log(
                        f"Référence obsolète pour '{jour}', tentative {attempt + 1}",
                        LOG_FILE,
                        "DEBUG",
                    )

                attempt += 1

            # Si toutes les tentatives échouent, indiquer un message d'échec
            if attempt == MAX_ATTEMPTS:
                write_log(
                    f"Échec de l'insertion de la valeur '{valeur_a_remplir}' dans le jour '{jour}' après {MAX_ATTEMPTS} tentatives.",
                    LOG_FILE,
                    "DEBUG",
                )

    return jours_remplis


def remplir_mission(driver, jours_de_travail, jours_remplis):
    """Remplir les jours de travail pour les missions."""
    for jour, (description_cible, valeur_a_remplir) in jours_de_travail.items():
        if (
            description_cible
            and not est_en_mission(description_cible)
            and jour not in jours_remplis
        ):
            jours_remplis = traiter_jour(
                driver, jour, description_cible, valeur_a_remplir, jours_remplis
            )
        elif (
            description_cible
            and est_en_mission(description_cible)
            and jour not in jours_remplis
        ):
            remplir_mission_specifique(driver, jour, valeur_a_remplir, jours_remplis)
    return jours_remplis


def remplir_mission_specifique(driver, jour, valeur_a_remplir, jours_remplis):
    """Cas spécifique pour les jours en mission.
    Cas où description_cible est "En mission", on écrit directement dans les IDs spécifiques sans utiliser `description_cible`
    """
    attempt = 0
    jour_index = list(JOURS_SEMAINE.keys())[list(JOURS_SEMAINE.values()).index(jour)]
    input_id = f"TIME{jour_index}$0"  # Définir l'ID de l'élément pour ce jour

    # Vérifier la présence de l'élément
    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

    if element:
        while attempt < MAX_ATTEMPTS:
            try:
                # Étape 1 : Détection et vérification du contenu actuel
                day_input_field, is_correct_value = detecter_et_verifier_contenu(
                    driver, input_id, valeur_a_remplir
                )

                if is_correct_value:
                    jours_remplis = ajouter_jour_a_jours_remplis(jour, jours_remplis)
                    afficher_message_insertion(
                        jour, valeur_a_remplir, attempt, "tentative d'insertion n°"
                    )
                    break

                # Étape 2 : Effacer et entrer la nouvelle valeur
                effacer_et_entrer_valeur(day_input_field, valeur_a_remplir)
                program_break_time(
                    1, "Veuillez patienter. Court délai pour stabilisation du DOM"
                )
                print()

                # Étape 3 : Contrôler que la valeur est bien insérée
                if controle_insertion(day_input_field, valeur_a_remplir):
                    jours_remplis = ajouter_jour_a_jours_remplis(jour, jours_remplis)
                    afficher_message_insertion(
                        jour, valeur_a_remplir, attempt, "après insertion"
                    )
                    break

            except StaleElementReferenceException:
                write_log(
                    f"Référence obsolète pour '{jour}', tentative {attempt + 1}",
                    LOG_FILE,
                    "DEBUG",
                )

            attempt += 1

        # Si toutes les tentatives échouent, indiquer un message d'échec
        if attempt == MAX_ATTEMPTS:
            write_log(
                f"Échec de l'insertion de la valeur '{valeur_a_remplir}' dans le jour '{jour}' après {MAX_ATTEMPTS} tentatives.",
                LOG_FILE,
                "DEBUG",
            )


def traiter_champs_mission(
    driver,
    listes_id_informations_mission,
    id_to_key_mapping,
    informations_projet_mission,
    max_attempts=5,
):
    """Traite les champs associés aux missions ('En mission') en insérant les valeurs nécessaires."""
    for id in listes_id_informations_mission:
        key = id_to_key_mapping.get(id)
        if key == "sub_category_code":  # Exclure les champs non concernés
            continue

        valeur_a_remplir = informations_projet_mission.get(key)
        if not valeur_a_remplir:
            write_log(
                f"Aucune valeur trouvée pour le champ '{key}' (ID: {id}).",
                LOG_FILE,
                "DEBUG",
            )
            continue

        write_log(
            f"Traitement de l'élément : {key} avec ID : {id} et valeur : {valeur_a_remplir}.",
            LOG_FILE,
            "DEBUG",
        )
        attempt = 0

        wait_for_dom(driver)  # Attente que le DOM soit prêt

        # Vérifier la présence de l'élément et gérer les tentatives d'insertion
        element = wait_for_element(driver, By.ID, id, timeout=DEFAULT_TIMEOUT)
        if element:
            while attempt < max_attempts:
                try:
                    # Étape 1 : Vérification de la valeur actuelle
                    input_field, is_correct_value = detecter_et_verifier_contenu(
                        driver, id, valeur_a_remplir
                    )
                    if is_correct_value:
                        write_log(
                            f"Valeur correcte déjà présente pour '{id}'.",
                            LOG_FILE,
                            "DEBUG",
                        )
                        break

                    # Étape 2 : Effacer et insérer la nouvelle valeur
                    effacer_et_entrer_valeur(input_field, valeur_a_remplir)
                    program_break_time(1, "Stabilisation du DOM après insertion.")
                    print()

                    # Étape 3 : Vérification de l'insertion
                    if controle_insertion(input_field, valeur_a_remplir):
                        write_log(
                            f"Valeur '{valeur_a_remplir}' insérée avec succès pour '{id}'.",
                            LOG_FILE,
                            "DEBUG",
                        )
                        break

                except StaleElementReferenceException:
                    write_log(
                        f"Référence obsolète pour '{id}', tentative {attempt + 1}.",
                        LOG_FILE,
                        "ERROR",
                    )

                attempt += 1

            # Si toutes les tentatives échouent
            if attempt == max_attempts:
                write_log(
                    f"Échec de l'insertion pour '{id}' après {max_attempts} tentatives.",
                    LOG_FILE,
                    "ERROR",
                )


# ----------------------------------------------------------------------------- #
# ----------------------------------- MAIN ------------------------------------ #
# ----------------------------------------------------------------------------- #
class TimeSheetHelper:
    """Helper class orchestrating the time sheet filling steps."""

    def __init__(self, log_file: str) -> None:
        self.log_file = log_file

    def initialize(self) -> None:
        initialize(self.log_file)

    def fill_standard_days(self, driver, jours_remplis: list[str]) -> list[str]:
        write_log(
            "Début du remplissage des jours hors mission...",
            LOG_FILE,
            "DEBUG",
        )
        return remplir_jours(
            driver, LISTE_ITEMS_DESCRIPTIONS, JOURS_SEMAINE, jours_remplis
        )

    def fill_work_missions(self, driver, jours_remplis: list[str]) -> list[str]:
        write_log(
            "Début du traitement des jours de travail et des missions...",
            LOG_FILE,
            "DEBUG",
        )
        return remplir_mission(driver, JOURS_DE_TRAVAIL, jours_remplis)

    def handle_additional_fields(self, driver) -> None:
        if est_en_mission_presente(JOURS_DE_TRAVAIL):
            write_log(
                "Jour 'En mission' détecté. Traitement des champs associés...",
                LOG_FILE,
                "DEBUG",
            )
            traiter_champs_mission(
                driver,
                LISTES_ID_INFORMATIONS_MISSION,
                ID_TO_KEY_MAPPING,
                INFORMATIONS_PROJET_MISSION,
            )
        else:
            write_log("Aucun Jour 'En mission' détecté.", LOG_FILE, "DEBUG")

    def run(self, driver) -> None:
        self.initialize()
        try:
            jours_remplis: list[str] = []

            write_log(
                "Initialisation du processus de remplissage...",
                LOG_FILE,
                "DEBUG",
            )

            jours_remplis = self.fill_standard_days(driver, jours_remplis)
            write_log(f"Jours déjà remplis : {jours_remplis}", LOG_FILE, "DEBUG")

            jours_remplis = self.fill_work_missions(driver, jours_remplis)
            write_log(
                f"Finalisation des jours remplis : {jours_remplis}",
                LOG_FILE,
                "DEBUG",
            )

            self.handle_additional_fields(driver)
            write_log(
                "Tous les jours et missions ont été traités avec succès.",
                LOG_FILE,
                "DEBUG",
            )

        except NoSuchElementException as e:
            log_error(f"Élément introuvable : {str(e)}.", LOG_FILE)
        except TimeoutException as e:
            log_error(f"Temps d'attente dépassé pour un élément : {str(e)}.", LOG_FILE)
        except StaleElementReferenceException as e:
            log_error(f"Référence obsolète détectée : {str(e)}.", LOG_FILE)
        except WebDriverException as e:
            log_error(f"Erreur WebDriver : {str(e)}.", LOG_FILE)
        except Exception as e:
            log_error(f"Erreur inattendue : {str(e)}.", LOG_FILE)


def main(driver, log_file: str) -> None:
    """Minimal orchestrator creating the helper and launching the process."""
    TimeSheetHelper(log_file).run(driver)


if __name__ == "__main__":
    from shared_utils import get_log_file

    main(None, get_log_file())
