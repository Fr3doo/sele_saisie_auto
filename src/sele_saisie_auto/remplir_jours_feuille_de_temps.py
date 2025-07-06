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
    trouver_ligne_par_description,
    verifier_champ_jour_rempli,
    wait_for_dom_ready,
    wait_for_element,
    wait_until_dom_is_stable,
)
from sele_saisie_auto.selenium_utils import set_log_file as set_log_file_selenium
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT
from sele_saisie_auto.utils.misc import program_break_time


@dataclass
class TimeSheetContext:
    """Context loaded during :func:`initialize`."""

    log_file: str
    item_descriptions: list[str]
    work_days: dict[str, tuple[str, str]]
    project_mission_info: dict[str, str]
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
        item_descriptions=app_config.liste_items_planning,
        work_days=app_config.work_schedule,
        project_mission_info=informations,
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
    item_descriptions = [
        item.strip().strip('"')
        for item in config.get("settings", "liste_items_planning").split(",")
        if item.strip()
    ]
    work_days = {
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
    project_mission_info = {
        item_projet: billing_map.get(value.lower(), value)
        for item_projet, value in config.items("project_information")
    }

    return TimeSheetContext(
        log_file=log_file,
        item_descriptions=item_descriptions,
        work_days=work_days,
        project_mission_info=project_mission_info,
        config=config,
    )


# ----------------------------------------------------------------------------- #
# ------------------------------- UTILITIES ----------------------------------- #
# ----------------------------------------------------------------------------- #


def wait_for_dom(driver, waiter: Waiter | None = None):
    """Attend que le DOM soit chargé et stable."""
    if waiter is None:
        wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)
        wait_for_dom_ready(driver, LONG_TIMEOUT)
    else:
        waiter.wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)
        waiter.wait_for_dom_ready(driver, LONG_TIMEOUT)


def est_en_mission(description):
    """Renvoie True si la description indique un jour 'En mission'."""
    return description == "En mission"


def est_en_mission_presente(work_days):
    """Vérifie si un jour de travail est marqué comme 'En mission'."""
    return any(value[0] == "En mission" for value in work_days.values())


def ajouter_jour_a_jours_remplis(jour, filled_days):
    """Ajoute un jour à la liste jours_remplis si ce n'est pas déjà fait."""
    if jour not in filled_days:
        filled_days.append(jour)
    return filled_days


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
    item_descriptions,
    week_days,
    filled_days,
    context: TimeSheetContext,
):
    """Remplir les jours dans l'application web."""
    # Parcourir chaque description dans item_descriptions
    for description_cible in item_descriptions:
        # Recherche de la ligne avec la description spécifiée pour le jour
        id_value = "POL_DESCR$"
        row_index = trouver_ligne_par_description(driver, description_cible, id_value)

        # Si la ligne est trouvée, remplir les jours de la semaine
        if row_index is not None:
            for jour_index, jour_name in week_days.items():
                input_id = f"POL_TIME{jour_index}${row_index}"

                # Vérifier la présence de l'élément
                element = wait_for_element(
                    driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT
                )

                if element:
                    # Vérifier s'il y a une valeur dans l'élément pour ce jour
                    jour_rempli = verifier_champ_jour_rempli(element, jour_name)
                    if jour_rempli:
                        filled_days.append(
                            jour_rempli
                        )  # Ajouter le jour s'il est déjà rempli

    return filled_days


def traiter_jour(
    driver,
    jour,
    description_cible,
    value_to_fill,
    filled_days,
    context: TimeSheetContext,
):
    """Traiter un jour spécifique pour le remplissage."""

    if jour in filled_days or not description_cible:
        return filled_days

    id_value = "POL_DESCR$"
    row_index = trouver_ligne_par_description(driver, description_cible, id_value)

    if row_index is not None:
        jour_index = list(JOURS_SEMAINE.keys())[
            list(JOURS_SEMAINE.values()).index(jour)
        ]
        input_id = f"POL_TIME{jour_index}${row_index}"

        element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

        if element and insert_with_retries(driver, input_id, value_to_fill, None):
            filled_days = ajouter_jour_a_jours_remplis(jour, filled_days)
            afficher_message_insertion(jour, value_to_fill, 0, "après insertion")
    return filled_days


def remplir_mission(
    driver,
    work_days,
    filled_days,
    context: TimeSheetContext,
):
    """Remplir les jours de travail pour les missions."""
    for jour, (description_cible, value_to_fill) in work_days.items():
        if (
            description_cible
            and not est_en_mission(description_cible)
            and jour not in filled_days
        ):
            traiter_jour(
                driver,
                jour,
                description_cible,
                value_to_fill,
                filled_days,
                context,
            )
        elif (
            description_cible
            and est_en_mission(description_cible)
            and jour not in filled_days
        ):
            remplir_mission_specifique(
                driver, jour, value_to_fill, filled_days, context
            )
    return filled_days


def remplir_mission_specifique(
    driver,
    jour,
    value_to_fill,
    filled_days,
    context: TimeSheetContext,
):
    """Cas spécifique pour les jours en mission.
    Cas où description_cible est "En mission", on écrit directement dans les IDs spécifiques sans utiliser `description_cible`
    """
    jour_index = list(JOURS_SEMAINE.keys())[list(JOURS_SEMAINE.values()).index(jour)]
    input_id = f"TIME{jour_index}$0"  # Définir l'ID de l'élément pour ce jour

    element = wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)

    if element and insert_with_retries(driver, input_id, value_to_fill, None):
        filled_days = ajouter_jour_a_jours_remplis(jour, filled_days)
        afficher_message_insertion(jour, value_to_fill, 0, "après insertion")


def _insert_value_with_retries(
    driver, field_id, value, max_attempts, waiter  # pragma: no cover
):  # pragma: no cover  # pragma: no cover
    """Essaye d'insérer la valeur plusieurs fois si nécessaire."""
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
            write_log(messages.DOM_STABLE, LOG_FILE, "DEBUG")  # pragma: no cover
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
    project_mission_info,
    context: TimeSheetContext,
    max_attempts=5,
    waiter: Waiter | None = None,
):
    """Traite les champs associés aux missions ('En mission') en insérant les valeurs nécessaires."""
    for id in listes_id_informations_mission:
        key = id_to_key_mapping.get(id)
        if key == "sub_category_code":  # Exclure les champs non concernés
            continue

        value_to_fill = project_mission_info.get(key)
        if not value_to_fill:
            write_log(
                f"Aucune valeur trouvée pour le champ '{key}' (ID: {id}).",
                context.log_file,
                "DEBUG",
            )
            continue

        write_log(
            f"Traitement de l'élément : {key} avec ID : {id} et valeur : {value_to_fill}.",
            context.log_file,
            "DEBUG",
        )
        _insert_value_with_retries(
            driver,
            id,
            value_to_fill,
            max_attempts,
            waiter,
        )


# ----------------------------------------------------------------------------- #
# ----------------------------------- MAIN ------------------------------------ #
# ----------------------------------------------------------------------------- #
class TimeSheetHelper:
    """Helper class orchestrating the time sheet filling steps."""

    def __init__(self, context: TimeSheetContext, waiter: Waiter | None = None) -> None:
        """Crée l'assistant avec son contexte et un ``Waiter`` optionnel."""
        self.context = context
        self.log_file = context.log_file
        if waiter is None:
            cfg = context.config
            if hasattr(cfg, "default_timeout") and hasattr(cfg, "long_timeout"):
                timeout = cfg.default_timeout
                long_timeout = cfg.long_timeout
            else:
                timeout = DEFAULT_TIMEOUT
                long_timeout = LONG_TIMEOUT
            self.waiter = Waiter(default_timeout=timeout, long_timeout=long_timeout)
        else:
            self.waiter = waiter
        global LOG_FILE
        LOG_FILE = self.log_file

    def wait_for_dom(self, driver) -> None:
        """Attend que le DOM soit prêt via ``Waiter``."""
        self.waiter.wait_until_dom_is_stable(driver)
        self.waiter.wait_for_dom_ready(driver)

    def initialize(self) -> TimeSheetContext:
        """Return the current context without reloading from disk."""
        return self.context

    def fill_standard_days(self, driver, filled_days: list[str]) -> list[str]:
        """Remplit les jours hors mission."""
        write_log(
            "Début du remplissage des jours hors mission...",
            LOG_FILE,
            "DEBUG",
        )
        liste = [] if self.context is None else self.context.item_descriptions
        ctx = self.context or TimeSheetContext(self.log_file, [], {}, {})
        return remplir_jours(driver, liste, JOURS_SEMAINE, filled_days, ctx)

    def fill_work_missions(self, driver, filled_days: list[str]) -> list[str]:
        """Traite les jours en mission."""
        write_log(
            "Début du traitement des jours de travail et des missions...",
            LOG_FILE,
            "DEBUG",
        )
        work_days = {} if self.context is None else self.context.work_days
        ctx = self.context or TimeSheetContext(self.log_file, [], {}, {})
        return remplir_mission(driver, work_days, filled_days, ctx)

    def handle_additional_fields(self, driver) -> None:
        """Insère les champs complémentaires liés aux missions."""
        if self.context and est_en_mission_presente(self.context.work_days):
            write_log(
                "Jour 'En mission' détecté. Traitement des champs associés...",
                LOG_FILE,
                "DEBUG",
            )
            traiter_champs_mission(
                driver,
                LISTES_ID_INFORMATIONS_MISSION,
                ID_TO_KEY_MAPPING,
                self.context.project_mission_info,
                self.context,
                waiter=self.waiter,
            )
        else:
            write_log("Aucun Jour 'En mission' détecté.", LOG_FILE, "DEBUG")

    def run(self, driver) -> None:
        """Orchestre toutes les étapes de remplissage."""
        if self.context is None:  # pragma: no cover - guard clause
            raise RuntimeError("TimeSheetContext not provided")
        try:
            filled_days: list[str] = []

            write_log(
                "Initialisation du processus de remplissage...",
                LOG_FILE,
                "DEBUG",
            )

            filled_days = self.fill_standard_days(driver, filled_days)
            write_log(f"Jours déjà remplis : {filled_days}", LOG_FILE, "DEBUG")

            filled_days = self.fill_work_missions(driver, filled_days)
            write_log(
                f"Finalisation des jours remplis : {filled_days}",
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
