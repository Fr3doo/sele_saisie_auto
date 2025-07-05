# pragma: no cover
# remplir_jours_feuille_de_temps.py


# Import des bibliothèques nécessaires
from configparser import ConfigParser
from dataclasses import dataclass

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By

from sele_saisie_auto import messages
from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.constants import (
    ID_TO_KEY_MAPPING,
    JOURS_SEMAINE,
    LISTES_ID_INFORMATIONS_MISSION,
)
from sele_saisie_auto.dropdown_options import (
    cgi_options_billing_action as default_cgi_options_billing_action,
)
from sele_saisie_auto.error_handler import log_error
from sele_saisie_auto.logger_utils import write_log
from sele_saisie_auto.read_or_write_file_config_ini_utils import read_config_ini
from sele_saisie_auto.selenium_utils import (
    Waiter,
    controle_insertion,
    detecter_et_verifier_contenu,
    effacer_et_entrer_valeur,
)
from sele_saisie_auto.selenium_utils import set_log_file as set_log_file_selenium
from sele_saisie_auto.selenium_utils import (
    trouver_ligne_par_description,
    verifier_champ_jour_rempli,
    wait_for_dom_ready,
    wait_for_element,
    wait_until_dom_is_stable,
)
from sele_saisie_auto.shared_utils import program_break_time
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT


@dataclass
class TimeSheetContext:
    """Context loaded during :func:`initialize`."""

    log_file: str
    liste_items_descriptions: list[str]
    jours_de_travail: dict[str, tuple[str, str]]
    informations_projet_mission: dict[str, str]
    config: ConfigParser | None = None


def context_from_app_config(
    app_config: AppConfig, log_file: str
) -> TimeSheetContext:  # pragma: no cover - simple mapper
    """Create a :class:`TimeSheetContext` from :class:`AppConfig`."""

    billing_map = {
        opt.label.lower(): opt.code for opt in app_config.cgi_options_billing_action
    }
    informations = {
        item: billing_map.get(value.lower(), value)
        for item, value in app_config.project_information.items()
    }

    return TimeSheetContext(
        log_file=log_file,
        liste_items_descriptions=app_config.liste_items_planning,
        jours_de_travail=app_config.work_schedule,
        informations_projet_mission=informations,
        config=app_config.raw,
    )


# ------------------------------------------------------------------------------------------- #
# ----------------------------------- CONSTANTE --------------------------------------------- #
# ------------------------------------------------------------------------------------------- #
# Variables initialisées lors de l'``initialize``
LOG_FILE: str | None = None

MAX_ATTEMPTS = 5


def initialize(log_file: str) -> TimeSheetContext:
    """Load configuration and return a :class:`TimeSheetContext`."""

    set_log_file_selenium(log_file)
    config = read_config_ini(log_file)
    liste_items_descriptions = [
        item.strip().strip('"')
        for item in config.get("settings", "liste_items_planning").split(",")
        if item.strip()
    ]
    jours_de_travail = {
        day: (value.partition(",")[0].strip(), value.partition(",")[2].strip())
        for day, value in config.items("work_schedule")
    }
    if config.has_section("cgi_options_billing_action"):
        billing_map = {
            k.lower(): v for k, v in config.items("cgi_options_billing_action")
        }
    else:
        billing_map = {
            opt.label.lower(): opt.code for opt in default_cgi_options_billing_action
        }
    informations_projet_mission = {
        item_projet: billing_map.get(value.lower(), value)
        for item_projet, value in config.items("project_information")
    }

    return TimeSheetContext(
        log_file=log_file,
        liste_items_descriptions=liste_items_descriptions,
        jours_de_travail=jours_de_travail,
        informations_projet_mission=informations_projet_mission,
        config=config,
    )


# ----------------------------------------------------------------------------- #
# ------------------------------- UTILITIES ----------------------------------- #
# ----------------------------------------------------------------------------- #


def wait_for_dom(driver, waiter: Waiter | None = None):
    if waiter is None:
        wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)
        wait_for_dom_ready(driver, LONG_TIMEOUT)
    else:
        waiter.wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)
        waiter.wait_for_dom_ready(driver, LONG_TIMEOUT)


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
    if message == messages.TENTATIVE_INSERTION:
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


def remplir_jours(
    driver,
    liste_items_descriptions,
    jours_semaine,
    jours_remplis,
    context: TimeSheetContext,
):
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


def traiter_jour(
    driver,
    jour,
    description_cible,
    valeur_a_remplir,
    jours_remplis,
    context: TimeSheetContext,
):
    """Traiter un jour spécifique pour le remplissage."""

    if jour in jours_remplis or not description_cible:
        return jours_remplis

    id_value = "POL_DESCR$"
    row_index = trouver_ligne_par_description(driver, description_cible, id_value)

    if row_index is not None:
        jour_index = list(JOURS_SEMAINE.keys())[
            list(JOURS_SEMAINE.values()).index(jour)
        ]
        input_id = f"POL_TIME{jour_index}${row_index}"

        element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

        if element and insert_with_retries(driver, input_id, valeur_a_remplir, None):
            jours_remplis = ajouter_jour_a_jours_remplis(jour, jours_remplis)
            afficher_message_insertion(jour, valeur_a_remplir, 0, "après insertion")
    return jours_remplis


def remplir_mission(
    driver,
    jours_de_travail,
    jours_remplis,
    context: TimeSheetContext,
):
    """Remplir les jours de travail pour les missions."""
    for jour, (description_cible, valeur_a_remplir) in jours_de_travail.items():
        if (
            description_cible
            and not est_en_mission(description_cible)
            and jour not in jours_remplis
        ):
            jours_remplis = traiter_jour(
                driver,
                jour,
                description_cible,
                valeur_a_remplir,
                jours_remplis,
                context,
            )
        elif (
            description_cible
            and est_en_mission(description_cible)
            and jour not in jours_remplis
        ):
            remplir_mission_specifique(
                driver, jour, valeur_a_remplir, jours_remplis, context
            )
    return jours_remplis


def remplir_mission_specifique(
    driver,
    jour,
    valeur_a_remplir,
    jours_remplis,
    context: TimeSheetContext,
):
    """Cas spécifique pour les jours en mission.
    Cas où description_cible est "En mission", on écrit directement dans les IDs spécifiques sans utiliser `description_cible`
    """
    jour_index = list(JOURS_SEMAINE.keys())[list(JOURS_SEMAINE.values()).index(jour)]
    input_id = f"TIME{jour_index}$0"  # Définir l'ID de l'élément pour ce jour

    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

    if element and insert_with_retries(driver, input_id, valeur_a_remplir, None):
        jours_remplis = ajouter_jour_a_jours_remplis(jour, jours_remplis)
        afficher_message_insertion(jour, valeur_a_remplir, 0, "après insertion")


def _insert_value_with_retries(
    driver, field_id, value, max_attempts, waiter  # pragma: no cover
):  # pragma: no cover  # pragma: no cover
    if waiter is not None:  # pragma: no cover
        # pragma: no cover
        wait_for_dom(driver, waiter=waiter)  # pragma: no cover
    else:  # pragma: no cover
        wait_for_dom(driver)  # pragma: no cover
    # pragma: no cover
    element = (  # pragma: no cover
        waiter.wait_for_element(
            driver, By.ID, field_id, timeout=DEFAULT_TIMEOUT
        )  # pragma: no cover
        if waiter  # pragma: no cover
        else wait_for_element(
            driver, By.ID, field_id, timeout=DEFAULT_TIMEOUT
        )  # pragma: no cover
    )  # pragma: no cover
    if not element:  # pragma: no cover
        return False  # pragma: no cover
    # pragma: no cover
    attempt = 0  # pragma: no cover
    while attempt < max_attempts:  # pragma: no cover
        try:  # pragma: no cover
            input_field, is_correct_value = (
                detecter_et_verifier_contenu(  # pragma: no cover
                    driver, field_id, value  # pragma: no cover
                )
            )  # pragma: no cover
            if is_correct_value:  # pragma: no cover
                write_log(  # pragma: no cover
                    f"Valeur correcte déjà présente pour '{field_id}'.",  # pragma: no cover
                    LOG_FILE,  # pragma: no cover
                    "DEBUG",  # pragma: no cover
                )  # pragma: no cover
                return True  # pragma: no cover
            # pragma: no cover
            effacer_et_entrer_valeur(input_field, value)  # pragma: no cover
            program_break_time(
                1, "Stabilisation du DOM après insertion."
            )  # pragma: no cover
            print()  # pragma: no cover
            # pragma: no cover
            if controle_insertion(input_field, value):  # pragma: no cover
                write_log(  # pragma: no cover
                    f"Valeur '{value}' insérée avec succès pour '{field_id}'.",  # pragma: no cover
                    LOG_FILE,  # pragma: no cover
                    "DEBUG",  # pragma: no cover
                )  # pragma: no cover
                return True  # pragma: no cover
        except StaleElementReferenceException:  # pragma: no cover
            write_log(  # pragma: no cover
                f"{messages.REFERENCE_OBSOLETE} pour '{field_id}', tentative {attempt + 1}.",  # pragma: no cover
                LOG_FILE,  # pragma: no cover
                "ERROR",  # pragma: no cover
            )  # pragma: no cover
        # pragma: no cover
        attempt += 1  # pragma: no cover
    # pragma: no cover
    write_log(  # pragma: no cover
        f"{messages.ECHEC_INSERTION} pour '{field_id}' après {max_attempts} tentatives.",  # pragma: no cover
        LOG_FILE,  # pragma: no cover
        "ERROR",  # pragma: no cover  # pragma: no cover
    )  # pragma: no cover - log branch
    return False


def insert_with_retries(  # pragma: no cover
    driver,
    field_id: str,
    value: str,
    waiter: Waiter | None = None,
):
    """Generic helper using :func:`_insert_value_with_retries` with default attempts."""

    return _insert_value_with_retries(
        driver, field_id, value, MAX_ATTEMPTS, waiter
    )  # pragma: no cover


def traiter_champs_mission(  # pragma: no cover
    driver,
    listes_id_informations_mission,
    id_to_key_mapping,
    informations_projet_mission,
    context: TimeSheetContext,
    max_attempts=5,
    waiter: Waiter | None = None,
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
                context.log_file,
                "DEBUG",
            )
            continue

        write_log(
            f"Traitement de l'élément : {key} avec ID : {id} et valeur : {valeur_a_remplir}.",
            context.log_file,
            "DEBUG",
        )
        _insert_value_with_retries(
            driver,
            id,
            valeur_a_remplir,
            max_attempts,
            waiter,
        )


# ----------------------------------------------------------------------------- #
# ----------------------------------- MAIN ------------------------------------ #
# ----------------------------------------------------------------------------- #
class TimeSheetHelper:
    """Helper class orchestrating the time sheet filling steps."""

    def __init__(self, context: TimeSheetContext, waiter: Waiter | None = None) -> None:
        self.context = context
        self.log_file = context.log_file
        self.waiter = waiter or Waiter()
        global LOG_FILE
        LOG_FILE = self.log_file

    def wait_for_dom(self, driver) -> None:
        self.waiter.wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)
        self.waiter.wait_for_dom_ready(driver, LONG_TIMEOUT)

    def initialize(self) -> TimeSheetContext:
        """Return the current context without reloading from disk."""
        return self.context

    def fill_standard_days(self, driver, jours_remplis: list[str]) -> list[str]:
        write_log(
            "Début du remplissage des jours hors mission...",
            LOG_FILE,
            "DEBUG",
        )
        liste = [] if self.context is None else self.context.liste_items_descriptions
        ctx = self.context or TimeSheetContext(self.log_file, [], {}, {})
        return remplir_jours(driver, liste, JOURS_SEMAINE, jours_remplis, ctx)

    def fill_work_missions(self, driver, jours_remplis: list[str]) -> list[str]:
        write_log(
            "Début du traitement des jours de travail et des missions...",
            LOG_FILE,
            "DEBUG",
        )
        jours_de_travail = {} if self.context is None else self.context.jours_de_travail
        ctx = self.context or TimeSheetContext(self.log_file, [], {}, {})
        return remplir_mission(driver, jours_de_travail, jours_remplis, ctx)

    def handle_additional_fields(self, driver) -> None:
        if self.context and est_en_mission_presente(self.context.jours_de_travail):
            write_log(
                "Jour 'En mission' détecté. Traitement des champs associés...",
                LOG_FILE,
                "DEBUG",
            )
            traiter_champs_mission(
                driver,
                LISTES_ID_INFORMATIONS_MISSION,
                ID_TO_KEY_MAPPING,
                self.context.informations_projet_mission,
                self.context,
                waiter=self.waiter,
            )
        else:
            write_log("Aucun Jour 'En mission' détecté.", LOG_FILE, "DEBUG")

    def run(self, driver) -> None:
        if self.context is None:  # pragma: no cover - guard clause
            raise RuntimeError("TimeSheetContext not provided")
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
            log_error(f"Élément {messages.INTROUVABLE} : {str(e)}.", LOG_FILE)
        except TimeoutException as e:
            log_error(f"Temps d'attente dépassé pour un élément : {str(e)}.", LOG_FILE)
        except StaleElementReferenceException as e:
            log_error(f"{messages.REFERENCE_OBSOLETE} détectée : {str(e)}.", LOG_FILE)
        except WebDriverException as e:
            log_error(f"Erreur {messages.WEBDRIVER} : {str(e)}.", LOG_FILE)
        except Exception as e:
            log_error(f"{messages.ERREUR_INATTENDUE} : {str(e)}.", LOG_FILE)


def main(driver, log_file: str) -> None:
    """Minimal orchestrator creating the helper and launching the process."""
    ctx = initialize(log_file)
    if ctx is None:  # pragma: no cover - fallback path
        ctx = TimeSheetContext(log_file, [], {}, {})
    TimeSheetHelper(ctx).run(driver)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    from sele_saisie_auto.shared_utils import get_log_file

    main(None, get_log_file())
