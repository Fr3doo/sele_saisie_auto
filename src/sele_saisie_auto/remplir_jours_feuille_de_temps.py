# src\sele_saisie_auto\remplir_jours_feuille_de_temps.py


# Import des bibliothèques nécessaires
"""Orchestrateur de saisie de feuille de temps.

Résumé interne (rôles & règles) :
- :class:`TimeSheetHelper` orchestre et délègue au :class:`DayFiller` (unique instance).
- Les *wrappers* exposés ici sont de minces passe-plats vers le ``DayFiller`` pour
  préserver la compatibilité — aucune logique métier dans ces wrappers.
- Pas de variable globale de log ; on passe toujours par ``self.log_file``.
- Les insertions utilisent ``insert_with_retries`` pour maintenir une cc faible (≤ 5).
- La surface publique est maîtrisée via ``__all__`` : les helpers internes du
  ``DayFiller`` ne sont pas exportés.
"""

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
    JOURS_SEMAINE,
)
from sele_saisie_auto.day_filler import (
    DayFiller,
    ajouter_jour_a_jours_remplis,
    est_en_mission_presente,
    insert_with_retries,
    remplir_jours,
    remplir_mission,
    remplir_mission_specifique,
    traiter_champs_mission,
    traiter_jour,
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
from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.read_or_write_file_config_ini_utils import read_config_ini
from sele_saisie_auto.selenium_utils import set_log_file as set_log_file_selenium
from sele_saisie_auto.selenium_utils import (
    wait_for_dom_ready,
    wait_until_dom_is_stable,
)
from sele_saisie_auto.selenium_utils.wait_helpers import Waiter
from sele_saisie_auto.selenium_utils.waiter_factory import create_waiter
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT

__all__ = [
    "TimeSheetContext",
    "TimeSheetHelper",
    "context_from_app_config",
    "initialize",
    "wait_for_dom",
    # Compatibility wrappers
    "est_en_mission_presente",
    "ajouter_jour_a_jours_remplis",
    "remplir_jours",
    "traiter_jour",
    "remplir_mission",
    "remplir_mission_specifique",
    "insert_with_retries",
    "traiter_champs_mission",
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
MAX_ATTEMPTS = DayFiller.MAX_ATTEMPTS

# Mapping centralisé des erreurs Selenium → message lisible (réduit la complexité cyclomatique).
# N.B. : Ne pas exporter cette constante ; elle est interne au module d'orchestration.
SELENIUM_ERROR_MESSAGES: dict[type[Exception], str] = {
    NoSuchElementException: f"Élément {messages.INTROUVABLE}",
    TimeoutException: "Temps d'attente dépassé pour un élément",
    StaleElementReferenceException: f"{messages.REFERENCE_OBSOLETE} détectée",
    WebDriverException: f"Erreur {messages.WEBDRIVER}",
}

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
        self.log_file: str = logger.log_file or ""
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
        self.day_filler = DayFiller(context, self.logger, self.waiter)

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
        return self.day_filler.fill_standard_days(driver, filled_days)

    def fill_work_missions(
        self, driver: WebDriver, filled_days: list[str]
    ) -> list[str]:
        """Traite les jours en mission."""
        self.logger.debug("Début du traitement des jours de travail et des missions...")
        return self.day_filler.fill_work_missions(driver, filled_days)

    def handle_additional_fields(self, driver: WebDriver) -> None:
        """Insère les champs complémentaires liés aux missions."""
        self.day_filler.handle_additional_fields(driver)

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
            log_error(f"{messages.ERREUR_INATTENDUE} : {exc}.", self.log_file)

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
        """Journalise les erreurs Selenium courantes (via mapping centralisé)."""
        message = SELENIUM_ERROR_MESSAGES.get(
            type(error), messages.ERREUR_INATTENDUE
        )
        log_error(f"{message} : {error}.", self.log_file)


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
