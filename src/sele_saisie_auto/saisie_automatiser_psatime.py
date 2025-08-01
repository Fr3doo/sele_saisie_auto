# src\sele_saisie_auto\saisie_automatiser_psatime.py

# ----------------------------------------------------------------------------- #
# ---------------- Import des bibliothèques nécessaires ----------------------- #
# ----------------------------------------------------------------------------- #

import sys
from dataclasses import dataclass
from multiprocessing import shared_memory
from types import TracebackType
from typing import Any, cast

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto import messages, remplir_jours_feuille_de_temps, shared_utils
from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.automation.additional_info_page import (
    AdditionalInfoPage,
    ensure_descriptions,
)
from sele_saisie_auto.automation.browser_session import BrowserSession
from sele_saisie_auto.automation.date_entry_page import DateEntryPage
from sele_saisie_auto.automation.login_handler import LoginHandler
from sele_saisie_auto.config_manager import ConfigManager
from sele_saisie_auto.configuration import Services, service_configurator_factory
from sele_saisie_auto.decorators import handle_selenium_errors
from sele_saisie_auto.encryption_utils import Credentials as EncryptionCredentials
from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.exceptions import (
    AutomationExitError,
    AutomationNotInitializedError,
)
from sele_saisie_auto.interfaces.protocols import LoggerProtocol
from sele_saisie_auto.locators import Locators
from sele_saisie_auto.logger_utils import show_log_separator, write_log
from sele_saisie_auto.logging_service import (
    Logger,
    LoggingConfigurator,
    get_logger,
    log_info,
)
from sele_saisie_auto.memory_config import MemoryConfig
from sele_saisie_auto.navigation import PageNavigator
from sele_saisie_auto.orchestration import AutomationOrchestrator
from sele_saisie_auto.remplir_jours_feuille_de_temps import ajouter_jour_a_jours_remplis
from sele_saisie_auto.resources.resource_manager import ResourceManager
from sele_saisie_auto.saisie_context import SaisieContext
from sele_saisie_auto.selenium_utils import (
    click_element_without_wait,
    detecter_doublons_jours,
    modifier_date_input,
    send_keys_to_element,
)
from sele_saisie_auto.selenium_utils import set_log_file as set_log_file_selenium
from sele_saisie_auto.selenium_utils import wait_for_dom_after
from sele_saisie_auto.shared_memory_service import SharedMemoryService
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT
from sele_saisie_auto.utils.date_utils import get_next_saturday_if_not_saturday
from sele_saisie_auto.utils.misc import program_break_time
from sele_saisie_auto.utils.mission import est_en_mission

# ----------------------------------------------------------------------------- #
# ------------------------------- CONSTANTE ----------------------------------- #
# ----------------------------------------------------------------------------- #


@dataclass
class Credentials:
    """Encrypted credentials and their shared memory handles."""

    aes_key: bytes
    mem_key: shared_memory.SharedMemory
    login: bytes
    mem_login: shared_memory.SharedMemory
    password: bytes
    mem_password: shared_memory.SharedMemory


__all__ = [
    "PSATimeAutomation",
    "Credentials",
    "modifier_date_input",
    "send_keys_to_element",
    "click_element_without_wait",
    "set_log_file_selenium",
    "detecter_doublons_jours",
    "AutomationExitError",
    "get_next_saturday_if_not_saturday",
    "est_en_mission",
    "ajouter_jour_a_jours_remplis",
]


def traiter_description(driver: WebDriver, config: dict[str, Any]) -> None:
    """Placeholder patched by :class:`AdditionalInfoPage`."""
    raise NotImplementedError


# ----------------------------------------------------------------------------
#
# --------------------------- CLASSE PRINCIPALE ------------------------------
#
# ----------------------------------------------------------------------------


class PSATimeAutomation:
    """Automatise la saisie de la feuille de temps PSA Time."""

    def __init__(
        self,
        log_file: str,
        app_config: AppConfig,
        memory_config: MemoryConfig | None = None,
        *,
        logger: Logger | None = None,
        services: Services | None = None,
        shared_memory_service: SharedMemoryService | None = None,
    ) -> None:
        """Initialise la configuration et les dépendances."""

        self.log_file: str = log_file
        self.memory_config = memory_config or MemoryConfig()
        LoggingConfigurator.setup(log_file, app_config.debug_mode, app_config.raw)
        self.logger = logger or get_logger(log_file)
        self.shared_memory_service = shared_memory_service or SharedMemoryService(
            self.logger
        )
        self.services = services or self._init_services(app_config)
        self.waiter = self.services.waiter
        self.browser_session = self.services.browser_session
        self.encryption_service = self.services.encryption_service
        self._login_handler = getattr(self.services, "login_handler", None)
        self.context = SaisieContext(
            config=app_config,
            encryption_service=self.encryption_service,
            shared_memory_service=self.shared_memory_service,
            project_mission_info={
                item_projet: {
                    opt.label.lower(): opt.code
                    for opt in app_config.cgi_options_billing_action
                }.get(str(value).lower(), str(value))
                for item_projet, value in app_config.project_information.items()
            },
            descriptions=[],
        )
        ensure_descriptions(self.context)

        self._date_entry_page: DateEntryPage | None = None
        self._additional_info_page: AdditionalInfoPage | None = None

        # Initialise orchestrator helpers
        self.page_navigator = self._create_page_navigator()
        self.resource_manager = ResourceManager(log_file)
        self.orchestrator: AutomationOrchestrator | None = None

        self.log_configuration_details()

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------
    def __enter__(self) -> "PSATimeAutomation":
        """Open the underlying :class:`ResourceManager`."""

        self.resource_manager.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Delegate cleanup to :class:`ResourceManager`."""

        self.resource_manager.__exit__(exc_type, exc, tb)

    def log_configuration_details(self) -> None:
        """Enregistre les détails de la configuration dans les logs."""

        write_log("📌 Chargement des configurations...", self.log_file, "DEBUG")
        write_log(
            f"👉 Login : {self.context.config.encrypted_login} - pas visible, normal",
            self.log_file,
            "DEBUG",
        )
        write_log(
            f"👉 Password : {self.context.config.encrypted_mdp} - pas visible, normal",
            self.log_file,
            "DEBUG",
        )
        write_log(f"👉 URL : {self.context.config.url}", self.log_file, "DEBUG")
        write_log(
            f"👉 Date cible : {self.context.config.date_cible}",
            self.log_file,
            "DEBUG",
        )

        write_log("👉 Planning de travail de la semaine:", self.log_file, "DEBUG")
        # Log work schedule details
        work_schedule: dict[str, tuple[str, str]] = cast(
            dict[str, tuple[str, str]],
            self.context.config.work_schedule,
        )
        for day, (activity, hours) in work_schedule.items():
            write_log(
                f"🔹 '{day}': ('{activity}', '{hours}')",
                self.log_file,
                "DEBUG",
            )

        # Additional information sections
        sections = {
            "periode_repos_respectee": "👉 Infos_supp_cgi_periode_repos_respectee:",
            "horaire_travail_effectif": "👉 Infos_supp_cgi_horaire_travail_effectif:",
            "plus_demi_journee_travaillee": "👉 Planning de travail de la semaine:",
            "duree_pause_dejeuner": "👉 Infos_supp_cgi_duree_pause_dejeuner:",
        }
        add_info = self.context.config.additional_information
        for key, title in sections.items():
            write_log(title, self.log_file, "DEBUG")
            values = cast(dict[str, str], add_info.get(key, {}))
            for day, status in values.items():
                write_log(f"🔹 '{day}': '{status}'", self.log_file, "DEBUG")

        write_log("👉 Lieu de travail Matin:", self.log_file, "DEBUG")
        for day, location in self.context.config.work_location_am.items():
            write_log(f"🔹 '{day}': '{location}'", self.log_file, "DEBUG")

        write_log("👉 Lieu de travail Apres-midi:", self.log_file, "DEBUG")
        for day, location in self.context.config.work_location_pm.items():
            write_log(f"🔹 '{day}': '{location}'", self.log_file, "DEBUG")

    def _init_services(self, app_config: AppConfig) -> Services:
        """Initialise les services principaux via :class:`ServiceConfigurator`."""

        configurator = service_configurator_factory(app_config)
        return configurator.build_services(self.log_file)

    def _create_page_navigator(self) -> PageNavigator:
        """Instantiate a :class:`PageNavigator` with helper dependencies."""

        timesheet_ctx = remplir_jours_feuille_de_temps.context_from_app_config(
            self.context.config,
            self.log_file,
        )
        helper = remplir_jours_feuille_de_temps.TimeSheetHelper(
            timesheet_ctx,
            cast(LoggerProtocol, self.logger),
            waiter=self.waiter,
            additional_info_page=self.additional_info_page,
            browser_session=self.browser_session,
        )
        return PageNavigator(
            self.browser_session,
            self.login_handler,
            self.date_entry_page,
            self.additional_info_page,
            helper,
        )

    # ------------------------------------------------------------------
    # Lazy page/service instantiation
    # ------------------------------------------------------------------
    @property
    def login_handler(self) -> LoginHandler:
        if self._login_handler is None:
            handler = getattr(self.services, "login_handler", None)
            if handler is not None:
                self._login_handler = handler
            else:
                self._login_handler = LoginHandler(
                    self.log_file,
                    self.encryption_service,
                    self.browser_session,
                )
        return self._login_handler

    @property
    def date_entry_page(self) -> DateEntryPage:
        if self._date_entry_page is None:
            self._date_entry_page = DateEntryPage(self, waiter=self.waiter)
        return self._date_entry_page

    @property
    def additional_info_page(self) -> AdditionalInfoPage:
        if self._additional_info_page is None:
            self._additional_info_page = AdditionalInfoPage(self, waiter=self.waiter)
        return self._additional_info_page

    def log_initialisation(self) -> None:
        """Initialise les logs et vérifie les configurations essentielles."""
        if not self.log_file:
            raise RuntimeError(f"Fichier de log {messages.INTROUVABLE}.")
        log_info(
            "📌 Démarrage de la fonction 'saisie_automatiser_psatime.run()'",
            self.log_file,
        )
        write_log(
            f"🔍 Chemin du fichier log : {self.log_file}",
            self.log_file,
            "DEBUG",
        )

    def initialize_shared_memory(self) -> EncryptionCredentials:
        """Récupère les données chiffrées via :class:`ResourceManager`."""

        credentials = self.resource_manager.initialize_shared_memory(self.logger)
        if hasattr(self.page_navigator, "prepare"):
            self.page_navigator.prepare(
                credentials,
                cast(str, self.context.config.date_cible),
            )
        return credentials

    def wait_for_dom(self, driver: WebDriver, max_attempts: int | None = None) -> None:
        """Wait until the DOM is stable using :class:`BrowserSession`."""
        if max_attempts is None:
            self.browser_session.wait_for_dom(driver)
        else:
            self.browser_session.wait_for_dom(driver, max_attempts=max_attempts)

    @handle_selenium_errors()
    def setup_browser(
        self,
        session: BrowserSession | None = None,
        *,
        headless: bool = False,
        no_sandbox: bool = False,
    ) -> WebDriver | None:
        """Configure et démarre le navigateur via :class:`BrowserSession`."""
        return cast(
            WebDriver,
            self.browser_session.open(
                self.context.config.url,
                fullscreen=False,
                headless=headless,
                no_sandbox=no_sandbox,
            ),
        )

    @wait_for_dom_after
    def switch_to_iframe_main_target_win0(self, driver: WebDriver) -> bool:
        """Bascule vers l'iframe principale ``main_target_win0``."""
        switched_to_iframe: bool | None = None
        element_present = self.waiter.wait_for_element(
            driver, By.ID, Locators.MAIN_FRAME.value, timeout=DEFAULT_TIMEOUT
        )
        if element_present:
            switched_to_iframe = self.browser_session.go_to_iframe(
                Locators.MAIN_FRAME.value
            )
        self.wait_for_dom(driver)
        if not switched_to_iframe:
            raise NameError("main_target_win0 not found")
        return switched_to_iframe

    @handle_selenium_errors(default_return=False)
    def navigate_from_home_to_date_entry_page(self, driver: WebDriver) -> bool:
        """Delegate navigation to :class:`PageNavigator`."""
        return cast(
            bool,
            self.page_navigator.navigate_from_home_to_date_entry_page(driver),
        )

    @handle_selenium_errors(default_return=False)
    def submit_date_cible(self, driver: WebDriver) -> bool:
        """Delegate submission to :class:`PageNavigator`."""
        return cast(
            bool,
            self.page_navigator.submit_date_cible(driver),
        )

    @wait_for_dom_after
    def navigate_from_work_schedule_to_additional_information_page(
        self, driver: WebDriver
    ) -> bool:
        """Delegate to :class:`PageNavigator`."""
        return cast(
            bool,
            self.page_navigator.navigate_from_work_schedule_to_additional_information_page(
                driver
            ),
        )

    @wait_for_dom_after
    def submit_and_validate_additional_information(self, driver: WebDriver) -> bool:
        """Delegate to :class:`PageNavigator`."""
        return cast(
            bool,
            self.page_navigator.submit_and_validate_additional_information(driver),
        )

    @wait_for_dom_after
    @handle_selenium_errors(default_return=False)
    def save_draft_and_validate(self, driver: WebDriver) -> bool:
        """Delegate to :class:`PageNavigator`."""
        return cast(
            bool,
            self.page_navigator.save_draft_and_validate(driver),
        )

    def cleanup_resources(
        self,
        session: BrowserSession | None,
        memoire_cle: shared_memory.SharedMemory | None,
        memoire_nom: shared_memory.SharedMemory | None,
        memoire_mdp: shared_memory.SharedMemory | None,
    ) -> None:
        """Ferme le navigateur et libère les mémoires partagées."""
        if memoire_cle:
            self.context.shared_memory_service.supprimer_memoire_partagee_securisee(
                memoire_cle
            )
        if memoire_nom:
            self.context.shared_memory_service.supprimer_memoire_partagee_securisee(
                memoire_nom
            )
        if memoire_mdp:
            self.context.shared_memory_service.supprimer_memoire_partagee_securisee(
                memoire_mdp
            )
        if session is not None:
            session.close()
        log_info(
            "🏁 [FIN] Clé et données supprimées de manière sécurisée, des mémoires partagées du fichier saisie_automatiser_psatime.",
            self.log_file,
        )

    def _handle_date_alert(self, driver: WebDriver) -> None:
        """Gère l'alerte liée à la date cible."""
        self.date_entry_page._handle_date_alert(driver)

    def _click_action_button(self, driver: WebDriver) -> None:
        """Clique sur le bouton d'action principal."""
        self.date_entry_page._click_action_button(driver)

    def _process_date_entry(self, driver: WebDriver) -> None:
        """Renseigne la date cible dans l'interface."""
        self.date_entry_page.process_date(driver, self.context.config.date_cible)

    def _fill_and_save_timesheet(self, driver: WebDriver) -> None:
        """Remplit la feuille de temps puis la sauvegarde."""
        self.wait_for_dom(driver)
        self.switch_to_iframe_main_target_win0(driver)
        program_break_time(
            1,
            messages.WAIT_STABILISATION,
        )
        write_log(messages.DOM_STABLE, self.log_file, "DEBUG")
        self._click_action_button(driver)
        self.wait_for_dom(driver)
        ctx = remplir_jours_feuille_de_temps.context_from_app_config(
            self.context.config, self.log_file
        )
        helper = remplir_jours_feuille_de_temps.TimeSheetHelper(
            ctx,
            cast(LoggerProtocol, self.logger),
            waiter=self.waiter,
        )
        page_navigator = self.page_navigator
        helper.run(driver)
        page_navigator.finalize_timesheet(driver)

    def run(
        self,
        *,
        headless: bool = False,
        no_sandbox: bool = False,
    ) -> None:
        """Point d'entrée principal de l'automatisation."""

        service_configurator = service_configurator_factory(self.context.config)
        self.orchestrator = AutomationOrchestrator.from_components(
            self.resource_manager,
            self.page_navigator,
            service_configurator,
            self.context,
            cast(LoggerProtocol, self.logger),
        )
        self.orchestrator.run(headless=headless, no_sandbox=no_sandbox)


# ------------------------------------------------------------------------------------------------- #
# ----------------------------------- FONCTIONS UTILS --------------------------------------------- #
# ------------------------------------------------------------------------------------------------- #


def seprateur_menu_affichage_log(log_file: str) -> None:
    """Affiche un séparateur dans le fichier de log."""
    show_log_separator(log_file)


def seprateur_menu_affichage_console() -> None:
    """Affiche un séparateur dans la console."""
    show_log_separator(shared_utils.get_log_file(), "DEBUG")


# ------------------------------------------------------------------------------------------------- #
# ----------------------------------- FONCTIONS PRINCIPALES --------------------------------------- #
# ------------------------------------------------------------------------------------------------- #


# ------------------------------------------------------------------------------------------------------------------ #
# -------------------------------------------- CODE PRINCIPAL ------------------------------------------------------ #
# ------------------------------------------------------------------------------------------------------------------ #


def main(
    log_file: str | None = None,
    *,
    headless: bool = False,
    no_sandbox: bool = False,
) -> None:
    """Point d'entrée principal du script."""

    from sele_saisie_auto.cli import cli_main

    cli_main(
        log_file,
        headless=headless,
        no_sandbox=no_sandbox,
    )


# ----------------------------------------------------------------------------
# Wrapper API pour compatibilité
# ----------------------------------------------------------------------------

_AUTOMATION: PSATimeAutomation | None = None
_ORCHESTRATOR: AutomationOrchestrator | None = None
orchestrator: AutomationOrchestrator | None = None
LOG_FILE: str | None = None


if __name__ == "__main__":
    main()
