# src\sele_saisie_auto\remplir_jours_feuille_de_temps.py


# Import des bibliothèques nécessaires
from __future__ import annotations

from collections.abc import Callable
from configparser import ConfigParser
from dataclasses import dataclass
from typing import Any, Protocol, cast, runtime_checkable

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto import messages
from sele_saisie_auto.app_config import AppConfig, AppConfigRaw, get_default_timeout
from sele_saisie_auto.constants import (
    ID_TO_KEY_MAPPING,
    JOURS_SEMAINE,
    LISTES_ID_INFORMATIONS_MISSION,
)
from sele_saisie_auto.dropdown_options import (
    cgi_options_billing_action as default_cgi_options_billing_action,
)
from sele_saisie_auto.error_handler import log_error
from sele_saisie_auto.interfaces import (
    AdditionalInfoPageProtocol,
    BrowserSessionProtocol,
    LoggerProtocol,
    WaiterProtocol,
)
from sele_saisie_auto.logger_utils import afficher_message_insertion, write_log
from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.read_or_write_file_config_ini_utils import read_config_ini
from sele_saisie_auto.selenium_utils import (
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
from sele_saisie_auto.selenium_utils.wait_helpers import Waiter
from sele_saisie_auto.selenium_utils.waiter_factory import create_waiter
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT
from sele_saisie_auto.utils.misc import program_break_time
from sele_saisie_auto.utils.mission import est_en_mission


@dataclass
class TimeSheetContext:
    """Context loaded during :func:`initialize`."""

    log_file: str
    item_descriptions: list[str]
    work_days: dict[str, tuple[str, str]]
    project_mission_info: dict[str, str]
    config: ConfigParser | None = None


@runtime_checkable
class TimesheetHelperProtocol(Protocol):
    """Minimal interface for :class:`TimeSheetHelper`."""

    def run(self, driver: WebDriver) -> None: ...


def context_from_app_config(app_config: AppConfig, log_file: str) -> TimeSheetContext:
    """Create a :class:`TimeSheetContext` from :class:`AppConfig`."""

    billing_map = {
        opt.label.lower(): opt.code for opt in app_config.cgi_options_billing_action
    }
    informations: dict[str, str] = {
        item: billing_map.get(str(value).lower(), str(value))
        for item, value in app_config.project_information.items()
    }

    return TimeSheetContext(
        log_file=log_file,
        item_descriptions=app_config.liste_items_planning,
        work_days=cast(dict[str, tuple[str, str]], app_config.work_schedule),
        project_mission_info=informations,
        config=app_config.raw,
    )


# ------------------------------------------------------------------------------------------- #
# ----------------------------------- CONSTANTE --------------------------------------------- #
# ------------------------------------------------------------------------------------------- #
# Variables initialisées lors de l'``initialize``
LOG_FILE: str = ""

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


def wait_for_dom(driver: WebDriver, waiter: WaiterProtocol | None = None) -> None:
    """Attend que le DOM soit chargé et stable."""
    if waiter is None:
        wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)
        wait_for_dom_ready(driver, LONG_TIMEOUT)
    else:
        waiter.wait_until_dom_is_stable(driver, timeout=DEFAULT_TIMEOUT)
        waiter.wait_for_dom_ready(driver, LONG_TIMEOUT)


def est_en_mission_presente(work_days: dict[str, tuple[str, str]]) -> bool:
    """Vérifie si un jour de travail est marqué comme 'En mission'."""
    return any(value[0] == "En mission" for value in work_days.values())


def ajouter_jour_a_jours_remplis(jour: str, filled_days: list[str]) -> list[str]:
    """Ajoute un jour à la liste jours_remplis si ce n'est pas déjà fait."""
    if jour not in filled_days:
        filled_days.append(jour)
    return filled_days


def _collect_filled_days_for_row(
    driver: WebDriver, row_index: int, week_days: dict[int, str]
) -> list[str]:
    """Retourne les jours déjà remplis pour une ligne donnée."""

    collected: list[str] = []
    for jour_index, jour_name in week_days.items():
        input_id = f"POL_TIME{jour_index}${row_index}"

        element = cast(Any, wait_for_element)(
            driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT
        )
        if element:
            jour_rempli = verifier_champ_jour_rempli(element, jour_name)
            if jour_rempli:
                collected.append(jour_rempli)
    return collected


# ------------------------------------------------------------------------------------------- #
# ----------------------------------- FONCTIONS --------------------------------------------- #
# ------------------------------------------------------------------------------------------- #


def remplir_jours(
    driver: WebDriver,
    item_descriptions: list[str],
    week_days: dict[int, str],
    filled_days: list[str],
    context: TimeSheetContext,
) -> list[str]:
    """Remplir les jours dans l'application web."""
    if not item_descriptions:
        return filled_days

    # Parcourir chaque description dans item_descriptions
    for description_cible in item_descriptions:
        # Recherche de la ligne avec la description spécifiée pour le jour
        id_value = "POL_DESCR$"
        row_index = trouver_ligne_par_description(driver, description_cible, id_value)

        # Si la ligne est trouvée, collecter les jours remplis pour cette ligne
        if row_index is not None:
            filled_days.extend(
                _collect_filled_days_for_row(driver, row_index, week_days)
            )

    return filled_days


def traiter_jour(
    driver: WebDriver,
    jour: str,
    description_cible: str,
    value_to_fill: str,
    filled_days: list[str],
    context: TimeSheetContext,
) -> list[str]:
    """Traiter un jour spécifique pour le remplissage."""
    if jour in filled_days or not description_cible:
        return filled_days

    id_value = "POL_DESCR$"
    row_index = trouver_ligne_par_description(driver, description_cible, id_value)
    if row_index is None:
        return filled_days

    jour_index = list(JOURS_SEMAINE.keys())[list(JOURS_SEMAINE.values()).index(jour)]
    input_id = f"POL_TIME{jour_index}${row_index}"

    element = cast(Any, wait_for_element)(
        driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT
    )
    if not element:
        return filled_days

    if insert_with_retries(driver, input_id, value_to_fill, None):
        filled_days = ajouter_jour_a_jours_remplis(jour, filled_days)
        afficher_message_insertion(
            jour,
            value_to_fill,
            0,
            "après insertion",
            LOG_FILE,
        )
    return filled_days


def remplir_mission(
    driver: WebDriver,
    work_days: dict[str, tuple[str, str]],
    filled_days: list[str],
    context: TimeSheetContext,
) -> list[str]:
    """Remplir les jours de travail pour les missions."""
    for jour, (description_cible, value_to_fill) in work_days.items():
        if jour in filled_days:
            continue
        if not description_cible:
            continue
        if est_en_mission(description_cible):
            remplir_mission_specifique(
                driver, jour, value_to_fill, filled_days, context
            )
        else:
            traiter_jour(
                driver,
                jour,
                description_cible,
                value_to_fill,
                filled_days,
                context,
            )
    return filled_days


def remplir_mission_specifique(
    driver: WebDriver,
    jour: str,
    value_to_fill: str,
    filled_days: list[str],
    context: TimeSheetContext,
) -> None:
    """Cas spécifique pour les jours en mission.
    Cas où description_cible est "En mission", on écrit directement dans les IDs spécifiques sans utiliser `description_cible`
    """
    jour_index = list(JOURS_SEMAINE.keys())[list(JOURS_SEMAINE.values()).index(jour)]
    input_id = f"TIME{jour_index}$0"  # Définir l'ID de l'élément pour ce jour

    element = cast(Any, wait_for_element)(
        driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT
    )

    if element and insert_with_retries(driver, input_id, value_to_fill, None):
        filled_days = ajouter_jour_a_jours_remplis(jour, filled_days)
        afficher_message_insertion(
            jour,
            value_to_fill,
            0,
            "après insertion",
            LOG_FILE,
        )


def _insert_value_with_retries(
    driver: WebDriver,
    field_id: str,
    value: str,
    max_attempts: int,
    waiter: WaiterProtocol | None,
) -> bool:
    """Essaye d'insérer la valeur plusieurs fois si nécessaire."""
    if waiter is not None:
        wait_for_dom(driver, waiter=waiter)
    else:
        wait_for_dom(driver)
    element = (
        cast(Any, waiter.wait_for_element)(
            driver, By.ID, field_id, timeout=DEFAULT_TIMEOUT
        )
        if waiter
        else cast(Any, wait_for_element)(
            driver, By.ID, field_id, timeout=DEFAULT_TIMEOUT
        )
    )
    if not element:
        return False
    attempt = 0
    while attempt < max_attempts:
        try:
            input_field, is_correct_value = detecter_et_verifier_contenu(
                driver, field_id, value
            )
            if input_field is None:
                raise RuntimeError("detecter_et_verifier_contenu returned None")
            if is_correct_value:
                write_log(
                    f"Valeur correcte déjà présente pour '{field_id}'.",
                    LOG_FILE,
                    "DEBUG",
                )
                return True
            effacer_et_entrer_valeur(input_field, value)
            program_break_time(1, "Stabilisation du DOM après insertion.")
            write_log(messages.DOM_STABLE, LOG_FILE, "DEBUG")
            if cast(Callable[[Any, str], bool], controle_insertion)(input_field, value):
                write_log(
                    f"Valeur '{value}' insérée avec succès pour '{field_id}'.",
                    LOG_FILE,
                    "DEBUG",
                )
                return True
        except StaleElementReferenceException:
            write_log(
                f"{messages.REFERENCE_OBSOLETE} pour '{field_id}', tentative {attempt + 1}.",
                LOG_FILE,
                "ERROR",
            )
        attempt += 1
    write_log(
        f"{messages.ECHEC_INSERTION} pour '{field_id}' après {max_attempts} tentatives.",
        LOG_FILE,
        "ERROR",
    )
    return False


def insert_with_retries(
    driver: WebDriver,
    field_id: str,
    value: str,
    waiter: WaiterProtocol | None = None,
) -> bool:
    """Generic helper using :func:`_insert_value_with_retries` with default attempts."""

    return _insert_value_with_retries(driver, field_id, value, MAX_ATTEMPTS, waiter)


def traiter_champs_mission(
    driver: WebDriver,
    listes_id_informations_mission: list[str],
    id_to_key_mapping: dict[str, str],
    project_mission_info: dict[str, str],
    context: TimeSheetContext,
    max_attempts: int = 5,
    waiter: WaiterProtocol | None = None,
) -> None:
    """Traite les champs associés aux missions ('En mission') en insérant les valeurs nécessaires."""
    for id in listes_id_informations_mission:
        key = id_to_key_mapping.get(id)
        if (
            key is None or key == "sub_category_code"
        ):  # Exclure les champs non concernés
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

    def __init__(
        self,
        context: TimeSheetContext,
        logger: LoggerProtocol,
        waiter: WaiterProtocol | None = None,
        *,
        additional_info_page: AdditionalInfoPageProtocol | None = None,
        browser_session: BrowserSessionProtocol | None = None,
    ) -> None:
        """Initialise l'assistant avec un ``Logger`` et un ``Waiter``."""
        self.context = context
        self.logger = logger
        self.log_file = logger.log_file
        self.waiter: WaiterProtocol
        if waiter is None:
            cfg = context.config
            app_cfg = None
            timeout = DEFAULT_TIMEOUT
            if isinstance(cfg, ConfigParser):
                app_cfg = AppConfig.from_raw(AppConfigRaw(cfg))
                timeout = get_default_timeout(app_cfg)
            w: Waiter = create_waiter(timeout)
            if app_cfg is not None:
                w.wrapper.long_timeout = app_cfg.long_timeout
            self.waiter = w
        else:
            self.waiter = waiter
        self.additional_info_page = additional_info_page
        self.browser_session = browser_session
        global LOG_FILE
        LOG_FILE = self.log_file  # type: ignore[assignment]

    def wait_for_dom(self, driver: WebDriver) -> None:
        """Attend que le DOM soit prêt via ``Waiter``."""
        self.waiter.wait_until_dom_is_stable(driver)
        self.waiter.wait_for_dom_ready(driver)

    def initialize(self) -> TimeSheetContext:
        """Return the current context without reloading from disk."""
        return self.context

    def fill_standard_days(
        self, driver: WebDriver, filled_days: list[str]
    ) -> list[str]:
        """Remplit les jours hors mission."""
        self.logger.debug("Début du remplissage des jours hors mission...")
        liste = [] if self.context is None else self.context.item_descriptions
        ctx = self.context or TimeSheetContext(self.log_file or "", [], {}, {})
        return remplir_jours(driver, liste, JOURS_SEMAINE, filled_days, ctx)

    def fill_work_missions(
        self, driver: WebDriver, filled_days: list[str]
    ) -> list[str]:
        """Traite les jours en mission."""
        self.logger.debug("Début du traitement des jours de travail et des missions...")
        work_days = {} if self.context is None else self.context.work_days
        ctx = self.context or TimeSheetContext(self.log_file or "", [], {}, {})
        return remplir_mission(driver, work_days, filled_days, ctx)

    def handle_additional_fields(self, driver: WebDriver) -> None:
        """Insère les champs complémentaires liés aux missions."""
        if self.context and est_en_mission_presente(self.context.work_days):
            self.logger.debug(
                "Jour 'En mission' détecté. Traitement des champs associés..."
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
            self.logger.debug("Aucun Jour 'En mission' détecté.")

    def run(self, driver: WebDriver | None) -> None:
        """Orchestre toutes les étapes de remplissage."""
        if self.context is None:
            raise RuntimeError("TimeSheetContext not provided")
        if driver is None:
            raise ValueError("WebDriver instance is required for filling the timesheet")
        if driver is None:
            raise RuntimeError("WebDriver not supplied")
        assert (
            driver is not None
        )  # garantit à mypy que driver est bien un WebDriver  # nosec B101
        try:
            filled_days: list[str] = []

            self.logger.debug("Initialisation du processus de remplissage...")

            filled_days = self.fill_standard_days(driver, filled_days)
            self.logger.debug(f"Jours déjà remplis : {filled_days}")

            if len(set(filled_days)) == len(JOURS_SEMAINE):
                self.logger.info(messages.TIMESHEET_ALREADY_COMPLETE)
                return

            filled_days = self.fill_work_missions(driver, filled_days)
            self.logger.debug(f"Finalisation des jours remplis : {filled_days}")

            self.handle_additional_fields(driver)
            if self.additional_info_page is not None:
                self.additional_info_page.navigate_from_work_schedule_to_additional_information_page(
                    driver
                )
                self.additional_info_page.submit_and_validate_additional_information(
                    driver
                )
            if self.browser_session is not None:
                self.browser_session.go_to_default_content()
            self.logger.debug("Tous les jours et missions ont été traités avec succès.")

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


def main(driver: WebDriver | None, log_file: str) -> None:
    """Minimal orchestrator creating the helper and launching the process."""
    ctx = initialize(log_file)
    if ctx is None:
        ctx = TimeSheetContext(log_file, [], {}, {})
    logger = Logger(log_file)
    TimeSheetHelper(ctx, cast(LoggerProtocol, logger)).run(driver)


if __name__ == "__main__":
    from sele_saisie_auto.shared_utils import get_log_file

    main(None, get_log_file())
