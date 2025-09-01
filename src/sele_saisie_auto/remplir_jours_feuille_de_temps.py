# src\sele_saisie_auto\remplir_jours_feuille_de_temps.py


# Import des bibliothèques nécessaires
from __future__ import annotations

from configparser import ConfigParser
from dataclasses import dataclass
from typing import Protocol, cast, runtime_checkable

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto import messages
from sele_saisie_auto.app_config import AppConfig, AppConfigRaw, get_default_timeout
from sele_saisie_auto.constants import (
    ID_TO_KEY_MAPPING,
    JOURS_SEMAINE,
    LISTES_ID_INFORMATIONS_MISSION,
)
from sele_saisie_auto.day_filler import DayFiller
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
)
from sele_saisie_auto.selenium_utils import set_log_file as set_log_file_selenium
from sele_saisie_auto.selenium_utils import (
    trouver_ligne_par_description,
    verifier_champ_jour_rempli,
    wait_for_dom_ready,
    wait_for_element,
    wait_until_dom_is_stable,
)
from sele_saisie_auto.selenium_utils.wait_helpers import Waiter
from sele_saisie_auto.selenium_utils.waiter_factory import create_waiter
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT
from sele_saisie_auto.utils.misc import program_break_time
from sele_saisie_auto.utils.mission import est_en_mission

__all__ = [
    "TimeSheetContext",
    "TimeSheetHelper",
    "wait_for_dom",
    "est_en_mission_presente",
    "ajouter_jour_a_jours_remplis",
    "remplir_jours",
    "traiter_jour",
    "remplir_mission",
    "remplir_mission_specifique",
    "insert_with_retries",
    "traiter_champs_mission",
    "trouver_ligne_par_description",
    "wait_for_element",
    "detecter_et_verifier_contenu",
    "effacer_et_entrer_valeur",
    "controle_insertion",
    "verifier_champ_jour_rempli",
    "program_break_time",
    "afficher_message_insertion",
    "write_log",
]


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
MAX_ATTEMPTS = DayFiller.MAX_ATTEMPTS


# ------------------------------- Helpers "initialize" ------------------------------- #
def _parse_item_descriptions(config: ConfigParser) -> list[str]:
    return [
        item.strip().strip('"')
        for item in config.get("settings", "liste_items_planning").split(",")
        if item.strip()
    ]


def _parse_work_days(config: ConfigParser) -> dict[str, tuple[str, str]]:
    return {
        day: (value.partition(",")[0].strip(), value.partition(",")[2].strip())
        for day, value in config.items("work_schedule")
    }


def _load_billing_map(config: ConfigParser) -> dict[str, str]:
    if config.has_section("cgi_options_billing_action"):
        return {k.lower(): v for k, v in config.items("cgi_options_billing_action")}
    # fallback par défaut
    return {opt.label.lower(): opt.code for opt in default_cgi_options_billing_action}


def _build_project_mission_info(
    config: ConfigParser, billing_map: dict[str, str]
) -> dict[str, str]:
    return {
        item_projet: billing_map.get(value.lower(), value)
        for item_projet, value in config.items("project_information")
    }


def initialize(log_file: str) -> TimeSheetContext:
    """Load configuration and return a :class:`TimeSheetContext` (responsabilité unique)."""

    set_log_file_selenium(log_file)
    config = read_config_ini(log_file)
    billing_map = _load_billing_map(config)
    return TimeSheetContext(
        log_file=log_file,
        item_descriptions=_parse_item_descriptions(config),
        work_days=_parse_work_days(config),
        project_mission_info=_build_project_mission_info(config, billing_map),
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


# Compatibility wrappers delegating to :class:`DayFiller`.


def est_en_mission_presente(work_days: dict[str, tuple[str, str]]) -> bool:
    return DayFiller.est_en_mission_presente(work_days)


def ajouter_jour_a_jours_remplis(jour: str, filled_days: list[str]) -> list[str]:
    return DayFiller.ajouter_jour_a_jours_remplis(jour, filled_days)


def remplir_jours(
    driver: WebDriver,
    item_descriptions: list[str],
    week_days: dict[int, str],
    filled_days: list[str],
    context: TimeSheetContext,
) -> list[str]:
    return DayFiller(context).remplir_jours(
        driver, item_descriptions, week_days, filled_days
    )


def traiter_jour(
    driver: WebDriver,
    jour: str,
    description_cible: str,
    value_to_fill: str,
    filled_days: list[str],
    context: TimeSheetContext,
) -> list[str]:
    return DayFiller(context).traiter_jour(
        driver, jour, description_cible, value_to_fill, filled_days
    )


def remplir_mission(
    driver: WebDriver,
    work_days: dict[str, tuple[str, str]],
    filled_days: list[str],
    context: TimeSheetContext,
) -> list[str]:
    for jour, (description_cible, value_to_fill) in work_days.items():
        if jour in filled_days or not description_cible:
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
    DayFiller(context).remplir_mission_specifique(
        driver, jour, value_to_fill, filled_days
    )


def insert_with_retries(
    driver: WebDriver,
    field_id: str,
    value: str,
    waiter: WaiterProtocol | None = None,
) -> bool:
    ctx = TimeSheetContext(LOG_FILE, [], {}, {})
    return DayFiller(ctx, waiter).insert_with_retries(driver, field_id, value, waiter)


def traiter_champs_mission(
    driver: WebDriver,
    listes_id_informations_mission: list[str],
    id_to_key_mapping: dict[str, str],
    project_mission_info: dict[str, str],
    context: TimeSheetContext,
    max_attempts: int = 5,
    waiter: WaiterProtocol | None = None,
) -> None:
    DayFiller(context, waiter).traiter_champs_mission(
        driver,
        listes_id_informations_mission,
        id_to_key_mapping,
        project_mission_info,
        max_attempts=max_attempts,
        waiter=waiter,
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
        self.day_filler = DayFiller(context, self.waiter)
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
            raise RuntimeError("WebDriver not supplied")
        try:
            self._run_steps(driver)
        except (
            NoSuchElementException,
            TimeoutException,
            StaleElementReferenceException,
            WebDriverException,
        ) as exc:
            self._log_selenium_error(exc)
        except Exception as exc:  # pragma: no cover - sauvegarde générale
            log_error(f"{messages.ERREUR_INATTENDUE} : {exc}.", LOG_FILE)

    def _run_steps(self, driver: WebDriver) -> None:
        """Exécute les étapes principales de remplissage."""
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
            self.additional_info_page.submit_and_validate_additional_information(driver)
        if self.browser_session is not None:
            self.browser_session.go_to_default_content()
        self.logger.debug("Tous les jours et missions ont été traités avec succès.")

    def _log_selenium_error(self, error: Exception) -> None:
        """Journalise les erreurs Selenium courantes."""
        mapping: dict[type[Exception], str] = {
            NoSuchElementException: f"Élément {messages.INTROUVABLE}",
            TimeoutException: "Temps d'attente dépassé pour un élément",
            StaleElementReferenceException: f"{messages.REFERENCE_OBSOLETE} détectée",
            WebDriverException: f"Erreur {messages.WEBDRIVER}",
        }
        message = mapping.get(type(error), messages.ERREUR_INATTENDUE)
        log_error(f"{message} : {error}.", LOG_FILE)


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
