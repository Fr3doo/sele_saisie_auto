# saisie_automatiser_psatime.py

# ----------------------------------------------------------------------------- #
# ---------------- Import des bibliothèques nécessaires ----------------------- #
# ----------------------------------------------------------------------------- #

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from multiprocessing import shared_memory

from selenium.webdriver.common.by import By

from sele_saisie_auto import (
    console_ui,
    messages,
    plugins,
    remplir_jours_feuille_de_temps,
)
from sele_saisie_auto.additional_info_locators import AdditionalInfoLocators
from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.automation.additional_info_page import AdditionalInfoPage
from sele_saisie_auto.automation.browser_session import BrowserSession
from sele_saisie_auto.automation.date_entry_page import DateEntryPage
from sele_saisie_auto.automation.login_handler import LoginHandler
from sele_saisie_auto.config_manager import ConfigManager
from sele_saisie_auto.configuration import ServiceConfigurator, Services, build_services
from sele_saisie_auto.decorators import handle_selenium_errors
from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.exceptions import AutomationNotInitializedError
from sele_saisie_auto.locators import Locators
from sele_saisie_auto.logger_utils import initialize_logger, write_log
from sele_saisie_auto.logging_service import Logger, get_logger
from sele_saisie_auto.navigation import PageNavigator
from sele_saisie_auto.orchestration import AutomationOrchestrator
from sele_saisie_auto.resources.resource_manager import ResourceManager
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
from sele_saisie_auto.utils.misc import program_break_time

# ----------------------------------------------------------------------------- #
# ------------------------------- CONSTANTE ----------------------------------- #
# ----------------------------------------------------------------------------- #


@dataclass
class SaisieContext:
    """Container for runtime configuration and services."""

    config: "AppConfig"
    encryption_service: EncryptionService
    shared_memory_service: SharedMemoryService
    project_mission_info: dict[str, str]
    descriptions: list[dict[str, object]]


@dataclass
class Credentials:
    """Encrypted credentials and their shared memory handles."""

    aes_key: bytes
    mem_key: shared_memory.SharedMemory
    login: bytes
    mem_login: shared_memory.SharedMemory
    password: bytes
    mem_password: shared_memory.SharedMemory


@dataclass
class MemoryConfig:
    """Shared memory configuration constants."""

    cle_name: str = "memoire_partagee_cle"
    data_name: str = "memoire_partagee_donnees"
    key_size: int = 32  # AES-256
    block_size: int = 128  # padding block


__all__ = [
    "PSATimeAutomation",
    "SaisieContext",
    "Credentials",
    "MemoryConfig",
    "modifier_date_input",
    "send_keys_to_element",
    "click_element_without_wait",
]

# Legacy globals for plugins/tests
_AUTOMATION = None
_ORCHESTRATOR = None
context = None
LOG_FILE = None


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
        choix_user: bool = True,
        memory_config: MemoryConfig | None = None,
        *,
        logger: Logger | None = None,
        services: Services | None = None,
        shared_memory_service: SharedMemoryService | None = None,
    ) -> None:
        """Initialise la configuration et les dépendances."""

        self.log_file = log_file
        self.choix_user = choix_user
        self.memory_config = memory_config or MemoryConfig()
        set_log_file_selenium(log_file)
        initialize_logger(app_config.raw, log_level_override=app_config.debug_mode)
        self.logger = logger or get_logger(log_file)
        self.shared_memory_service = shared_memory_service or SharedMemoryService(
            self.logger
        )
        self.services = services or self._init_services(app_config)
        self.waiter = self.services.waiter
        self.browser_session = self.services.browser_session
        self.encryption_service = self.services.encryption_service
        self.context = SaisieContext(
            config=app_config,
            encryption_service=self.encryption_service,
            shared_memory_service=self.shared_memory_service,
            project_mission_info={
                item_projet: {
                    opt.label.lower(): opt.code
                    for opt in app_config.cgi_options_billing_action
                }.get(value.lower(), value)
                for item_projet, value in app_config.project_information.items()
            },
            descriptions=[
                {
                    "description_cible": "Temps de repos de 11h entre 2 jours travaillés respecté",
                    "id_value_ligne": AdditionalInfoLocators.ROW_DESCR100.value,
                    "id_value_jours": AdditionalInfoLocators.DAY_UC_DAILYREST.value,
                    "type_element": "select",
                    "valeurs_a_remplir": app_config.additional_information[
                        "periode_repos_respectee"
                    ],
                },
                {
                    "description_cible": (
                        "Mon temps de travail effectif a débuté entre 8h00 et 10h00 et Mon temps de travail effectif a pris fin entre 16h30 et 19h00"
                    ),
                    "id_value_ligne": AdditionalInfoLocators.ROW_DESCR100.value,
                    "id_value_jours": AdditionalInfoLocators.DAY_UC_DAILYREST.value,
                    "type_element": "select",
                    "valeurs_a_remplir": app_config.additional_information[
                        "horaire_travail_effectif"
                    ],
                },
                {
                    "description_cible": "J’ai travaillé plus d’une demi-journée",
                    "id_value_ligne": AdditionalInfoLocators.ROW_DESCR100.value,
                    "id_value_jours": AdditionalInfoLocators.DAY_UC_DAILYREST.value,
                    "type_element": "select",
                    "valeurs_a_remplir": app_config.additional_information[
                        "plus_demi_journee_travaillee"
                    ],
                },
                {
                    "description_cible": "Durée de la pause déjeuner",
                    "id_value_ligne": AdditionalInfoLocators.ROW_DESCR200.value,
                    "id_value_jours": AdditionalInfoLocators.DAY_UC_DAILYREST_SPECIAL.value,
                    "type_element": "input",
                    "valeurs_a_remplir": app_config.additional_information[
                        "duree_pause_dejeuner"
                    ],
                },
                {
                    "description_cible": "Matin",
                    "id_value_ligne": AdditionalInfoLocators.ROW_DESCR.value,
                    "id_value_jours": AdditionalInfoLocators.DAY_UC_LOCATION_A.value,
                    "type_element": "select",
                    "valeurs_a_remplir": app_config.work_location_am,
                },
                {
                    "description_cible": "Après-midi",
                    "id_value_ligne": AdditionalInfoLocators.ROW_DESCR.value,
                    "id_value_jours": AdditionalInfoLocators.DAY_UC_LOCATION_A.value,
                    "type_element": "select",
                    "valeurs_a_remplir": app_config.work_location_pm,
                },
            ],
        )
        self._login_handler: LoginHandler | None = None
        self._date_entry_page: DateEntryPage | None = None
        self._additional_info_page: AdditionalInfoPage | None = None

        # Initialise orchestrator helpers
        timesheet_ctx = remplir_jours_feuille_de_temps.context_from_app_config(
            app_config, log_file
        )  # pragma: no cover
        timesheet_helper = remplir_jours_feuille_de_temps.TimeSheetHelper(
            timesheet_ctx,
            self.logger,
            waiter=self.waiter,
        )  # pragma: no cover
        self.page_navigator = PageNavigator(  # pragma: no cover
            self.browser_session,
            self.login_handler,
            self.date_entry_page,
            self.additional_info_page,
            timesheet_helper,
        )
        self.resource_manager = ResourceManager(log_file)  # pragma: no cover
        self.orchestrator: AutomationOrchestrator | None = None

        self.log_configuration_details()

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------
    def __enter__(self) -> "PSATimeAutomation":
        """Open the underlying :class:`ResourceManager`."""

        self.resource_manager.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Delegate cleanup to :class:`ResourceManager`."""

        self.resource_manager.__exit__(exc_type, exc, tb)

    def log_configuration_details(self) -> None:
        """Enregistre les détails de la configuration dans les logs."""

        write_log(
            "📌 Chargement des configurations...", self.log_file, "DEBUG"
        )  # pragma: no cover
        write_log(
            f"👉 Login : {self.context.config.encrypted_login} - pas visible, normal",
            self.log_file,
            "DEBUG",
        )  # pragma: no cover
        write_log(
            f"👉 Password : {self.context.config.encrypted_mdp} - pas visible, normal",
            self.log_file,
            "DEBUG",
        )  # pragma: no cover
        write_log(
            f"👉 URL : {self.context.config.url}", self.log_file, "DEBUG"
        )  # pragma: no cover
        write_log(
            f"👉 Date cible : {self.context.config.date_cible}",
            self.log_file,
            "DEBUG",
        )  # pragma: no cover

        write_log(
            "👉 Planning de travail de la semaine:", self.log_file, "DEBUG"
        )  # pragma: no cover
        for day, (activity, hours) in self.context.config.work_schedule.items():
            write_log(
                f"🔹 '{day}': ('{activity}', '{hours}')",
                self.log_file,
                "DEBUG",
            )  # pragma: no cover

        write_log(
            "👉 Infos_supp_cgi_periode_repos_respectee:", self.log_file, "DEBUG"
        )  # pragma: no cover
        for day, status in self.context.config.additional_information[
            "periode_repos_respectee"
        ].items():
            write_log(
                f"🔹 '{day}': '{status}'", self.log_file, "DEBUG"
            )  # pragma: no cover

        write_log(
            "👉 Infos_supp_cgi_horaire_travail_effectif:", self.log_file, "DEBUG"
        )  # pragma: no cover
        for day, status in self.context.config.additional_information[
            "horaire_travail_effectif"
        ].items():
            write_log(
                f"🔹 '{day}': '{status}'", self.log_file, "DEBUG"
            )  # pragma: no cover

        write_log(
            "👉 Planning de travail de la semaine:", self.log_file, "DEBUG"
        )  # pragma: no cover
        for day, status in self.context.config.additional_information[
            "plus_demi_journee_travaillee"
        ].items():
            write_log(
                f"🔹 '{day}': '{status}'", self.log_file, "DEBUG"
            )  # pragma: no cover

        write_log(
            "👉 Infos_supp_cgi_duree_pause_dejeuner:", self.log_file, "DEBUG"
        )  # pragma: no cover
        for day, status in self.context.config.additional_information[
            "duree_pause_dejeuner"
        ].items():
            write_log(
                f"🔹 '{day}': '{status}'", self.log_file, "DEBUG"
            )  # pragma: no cover

        write_log(
            "👉 Lieu de travail Matin:", self.log_file, "DEBUG"
        )  # pragma: no cover
        for day, location in self.context.config.work_location_am.items():
            write_log(
                f"🔹 '{day}': '{location}'", self.log_file, "DEBUG"
            )  # pragma: no cover

        write_log(
            "👉 Lieu de travail Apres-midi:", self.log_file, "DEBUG"
        )  # pragma: no cover
        for day, location in self.context.config.work_location_pm.items():
            write_log(
                f"🔹 '{day}': '{location}'", self.log_file, "DEBUG"
            )  # pragma: no cover

    def _init_services(self, app_config: AppConfig) -> Services:
        """Initialise les services principaux via :func:`build_services`."""

        self.services = build_services(app_config, self.log_file)
        return self.services

    # ------------------------------------------------------------------
    # Lazy page/service instantiation
    # ------------------------------------------------------------------
    @property
    def login_handler(self) -> LoginHandler:
        if self._login_handler is None:
            cls = LoginHandler
            if hasattr(cls, "from_automation"):
                self._login_handler = cls.from_automation(self)
            else:  # pragma: no cover - fallback for patched classes
                self._login_handler = cls(
                    self.log_file,
                    self.encryption_service,
                    self.browser_session,
                )
        return self._login_handler

    @property
    def date_entry_page(self) -> DateEntryPage:
        if self._date_entry_page is None:
            cls = DateEntryPage
            if hasattr(cls, "from_automation"):
                self._date_entry_page = cls.from_automation(self, waiter=self.waiter)
            else:  # pragma: no cover - fallback for patched classes
                self._date_entry_page = cls(self, waiter=self.waiter)
        return self._date_entry_page

    @property
    def additional_info_page(self) -> AdditionalInfoPage:
        if self._additional_info_page is None:
            cls = AdditionalInfoPage
            if hasattr(cls, "from_automation"):
                self._additional_info_page = cls.from_automation(
                    self, waiter=self.waiter
                )
            else:  # pragma: no cover - fallback for patched classes
                self._additional_info_page = cls(self, waiter=self.waiter)
        return self._additional_info_page

    def log_initialisation(self) -> None:
        """Initialise les logs et vérifie les configurations essentielles."""
        if not self.log_file:
            raise RuntimeError(f"Fichier de log {messages.INTROUVABLE}.")
        write_log(
            "📌 Démarrage de la fonction 'saisie_automatiser_psatime.run()'",
            self.log_file,
            "INFO",
        )
        write_log(
            f"🔍 Chemin du fichier log : {self.log_file}",
            self.log_file,
            "DEBUG",
        )

    def initialize_shared_memory(self):
        """Récupère les données de la mémoire partagée pour le login."""
        credentials = self.context.encryption_service.retrieve_credentials()

        if (
            credentials.mem_login is None
            or credentials.mem_password is None
            or credentials.mem_key is None
        ):
            write_log(
                "🚨 La mémoire partagée n'a pas été initialisée correctement. Assurez-vous que les identifiants ont été chiffrés",
                self.log_file,
                "ERROR",
            )
            sys.exit(1)
        if hasattr(self.page_navigator, "prepare"):
            self.page_navigator.prepare(credentials, self.context.config.date_cible)

        return credentials

    def wait_for_dom(self, driver):
        """Wait until the DOM is stable using :class:`BrowserSession`."""
        self.browser_session.wait_for_dom(driver)

    @handle_selenium_errors(default_return=None)
    def setup_browser(
        self,
        session: BrowserSession | None = None,
        *,
        headless: bool = False,
        no_sandbox: bool = False,
    ):
        """Configure et démarre le navigateur via :class:`BrowserSession`."""
        return self.browser_session.open(
            self.context.config.url,
            fullscreen=False,
            headless=headless,
            no_sandbox=no_sandbox,
        )

    @wait_for_dom_after
    def switch_to_iframe_main_target_win0(self, driver):
        """Bascule vers l'iframe principale ``main_target_win0``."""
        switched_to_iframe = None
        element_present = self.waiter.wait_for_element(
            driver, By.ID, Locators.MAIN_FRAME.value, timeout=DEFAULT_TIMEOUT
        )
        if element_present:
            switched_to_iframe = self.browser_session.go_to_iframe(
                Locators.MAIN_FRAME.value
            )
        self.wait_for_dom(driver)
        if switched_to_iframe is None:
            raise NameError("main_target_win0 not found")
        return switched_to_iframe

    @handle_selenium_errors(default_return=False)
    def navigate_from_home_to_date_entry_page(self, driver):
        """Delegate navigation to :class:`PageNavigator`."""
        return self.page_navigator.navigate_from_home_to_date_entry_page(driver)

    @handle_selenium_errors(default_return=False)
    def submit_date_cible(self, driver):
        """Delegate submission to :class:`PageNavigator`."""
        return self.page_navigator.submit_date_cible(driver)

    @wait_for_dom_after
    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        """Delegate to :class:`PageNavigator`."""
        return self.page_navigator.navigate_from_work_schedule_to_additional_information_page(
            driver
        )

    @wait_for_dom_after
    def submit_and_validate_additional_information(self, driver):
        """Delegate to :class:`PageNavigator`."""
        return self.page_navigator.submit_and_validate_additional_information(driver)

    @wait_for_dom_after
    @handle_selenium_errors(default_return=False)
    def save_draft_and_validate(self, driver):
        """Delegate to :class:`PageNavigator`."""
        return self.page_navigator.save_draft_and_validate(driver)

    def cleanup_resources(
        self,
        session,
        memoire_cle,
        memoire_nom,
        memoire_mdp,
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
        write_log(
            "🏁 [FIN] Clé et données supprimées de manière sécurisée, des mémoires partagées du fichier saisie_automatiser_psatime.",
            self.log_file,
            "INFO",
        )

    def _handle_date_alert(self, driver) -> None:
        """Gère l'alerte liée à la date cible."""
        self.date_entry_page._handle_date_alert(driver)

    def _click_action_button(self, driver) -> None:
        """Clique sur le bouton d'action principal."""
        self.date_entry_page._click_action_button(driver, self.choix_user)

    def _process_date_entry(self, driver) -> None:
        """Renseigne la date cible dans l'interface."""
        self.date_entry_page.process_date(driver, self.context.config.date_cible)

    def _fill_and_save_timesheet(self, driver) -> None:
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
            self.logger,
            waiter=self.waiter,
        )
        self.page_navigator.timesheet_helper = helper
        self.page_navigator.fill_timesheet(driver)
        self.wait_for_dom(driver)
        if self.switch_to_iframe_main_target_win0(driver):
            detecter_doublons_jours(driver)
            plugins.call("before_submit", driver)
            self.page_navigator.submit_timesheet(driver)

    def run(
        self,
        *,
        headless: bool = False,
        no_sandbox: bool = False,
    ) -> None:  # pragma: no cover
        """Point d'entrée principal de l'automatisation."""

        service_configurator = ServiceConfigurator(self.context.config)
        self.orchestrator = AutomationOrchestrator.from_components(
            self.resource_manager,
            self.page_navigator,
            service_configurator,
            self.context,
            self.logger,
            choix_user=self.choix_user,
        )
        self.orchestrator.run(headless=headless, no_sandbox=no_sandbox)


# ------------------------------------------------------------------------------------------------- #
# ----------------------------------- FONCTIONS UTILS --------------------------------------------- #
# ------------------------------------------------------------------------------------------------- #


def seprateur_menu_affichage_log(log_file: str) -> None:
    """Affiche un séparateur dans le fichier de log."""
    write_log(
        "*************************************************************",
        log_file,
        "INFO",
    )


def seprateur_menu_affichage_console():
    """Affiche un séparateur dans la console."""
    console_ui.show_separator()


def get_next_saturday_if_not_saturday(date_str):
    """Retourne le prochain samedi si la date donnée n'est pas déjà un samedi."""
    initial_date = datetime.strptime(date_str, "%d/%m/%Y")
    initial_weekday = initial_date.weekday()
    if initial_weekday != 5:
        days_to_next_saturday = (5 - initial_weekday) % 7
        next_saturday_date = initial_date + timedelta(days=days_to_next_saturday)
        return next_saturday_date.strftime("%d/%m/%Y")
    return date_str


def est_en_mission(description):
    """Renvoie True si la description indique un jour 'En mission'."""
    return description == "En mission"


def ajouter_jour_a_jours_remplis(jour, filled_days):
    """Ajoute un jour à la liste jours_remplis si ce n'est pas déjà fait."""
    if jour not in filled_days:
        filled_days.append(jour)
    return filled_days


def afficher_message_insertion(jour, valeur, tentative, message, log_file: str) -> None:
    """Affiche un message d'insertion de la valeur."""
    if message == messages.TENTATIVE_INSERTION:
        write_log(
            f"⚠️ Valeur '{valeur}' confirmée pour le jour '{jour}' ({message}{tentative + 1})",
            log_file,
            "DEBUG",
        )
    else:
        write_log(
            f"⚠️ Valeur '{valeur}' confirmée pour le jour '{jour}' {message})",
            log_file,
            "DEBUG",
        )


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
) -> None:  # pragma: no cover
    """Point d'entrée principal du script.

    Parameters
    ----------
    log_file : str | None, optional
        Chemin du fichier log. S'il vaut ``None``, il sera déterminé via
        :func:`get_log_file`.
    """
    if log_file is None:
        from sele_saisie_auto.shared_utils import get_log_file

        log_file = get_log_file()

    with get_logger(log_file):
        cfg = ConfigManager(log_file=log_file).load()
        PSATimeAutomation(log_file, cfg).run(
            headless=headless,
            no_sandbox=no_sandbox,
        )


# ----------------------------------------------------------------------------
# Wrapper API pour compatibilité
# ----------------------------------------------------------------------------

_AUTOMATION: PSATimeAutomation | None = None
_ORCHESTRATOR: AutomationOrchestrator | None = None
context: SaisieContext | None = None
LOG_FILE: str | None = None


def initialize(
    log_file: str,
    app_config: AppConfig,
    choix_user: bool = True,
    memory_config: MemoryConfig | None = None,
) -> None:
    """Instancie l'automatisation."""
    global _AUTOMATION, _ORCHESTRATOR, context, LOG_FILE
    _AUTOMATION = PSATimeAutomation(
        log_file,
        app_config,
        choix_user=choix_user,
        memory_config=memory_config,
    )
    context = _AUTOMATION.context
    LOG_FILE = log_file
    service_configurator = ServiceConfigurator(_AUTOMATION.context.config)
    _ORCHESTRATOR = AutomationOrchestrator.from_components(
        _AUTOMATION.resource_manager,
        _AUTOMATION.page_navigator,
        service_configurator,
        _AUTOMATION.context,
        _AUTOMATION.logger,
        choix_user=_AUTOMATION.choix_user,
    )
    _AUTOMATION.orchestrator = _ORCHESTRATOR


def log_initialisation() -> None:
    """Enregistre les informations initiales dans les logs."""
    if not _AUTOMATION:
        raise AutomationNotInitializedError("Automation non initialisée")
    _AUTOMATION.log_initialisation()


def initialize_shared_memory():
    """Récupère les identifiants chiffrés depuis la mémoire partagée."""
    if not _ORCHESTRATOR:
        raise AutomationNotInitializedError("Automation non initialisée")
    return _ORCHESTRATOR.initialize_shared_memory()


def setup_browser(
    session: BrowserSession,
    *,
    headless: bool = False,
    no_sandbox: bool = False,
):
    """Instancie le navigateur Selenium."""
    if not _ORCHESTRATOR:
        raise AutomationNotInitializedError("Automation non initialisée")
    _ORCHESTRATOR.browser_session = session
    return _ORCHESTRATOR.browser_session.open(
        _ORCHESTRATOR.config.url,
        fullscreen=False,
        headless=headless,
        no_sandbox=no_sandbox,
    )


def connect_to_psatime(driver, cle_aes, login_c, pwd_c):
    """Ouvre la session PSA Time avec les identifiants fournis."""
    if not _ORCHESTRATOR:
        raise AutomationNotInitializedError("Automation non initialisée")
    return _ORCHESTRATOR.login_handler.connect_to_psatime(
        driver, cle_aes, login_c, pwd_c
    )


def switch_to_iframe_main_target_win0(driver):
    """Bascule vers l'iframe principale."""
    if not _ORCHESTRATOR:
        raise AutomationNotInitializedError("Automation non initialisée")
    return _ORCHESTRATOR.switch_to_iframe_main_target_win0(driver)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
