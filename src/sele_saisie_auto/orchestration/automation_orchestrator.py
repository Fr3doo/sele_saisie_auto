# pragma: no cover
from __future__ import annotations

import types
from typing import TYPE_CHECKING, Callable

from selenium.webdriver.common.by import By

from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.automation import (
    AdditionalInfoPage,
    BrowserSession,
    DateEntryPage,
    LoginHandler,
)
from sele_saisie_auto.config_manager import ConfigManager
from sele_saisie_auto.configuration import ServiceConfigurator
from sele_saisie_auto.locators import Locators
from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.navigation import PageNavigator
from sele_saisie_auto.remplir_jours_feuille_de_temps import (
    TimeSheetHelper,
    context_from_app_config,
)
from sele_saisie_auto.resources.resource_manager import ResourceManager
from sele_saisie_auto.selenium_utils import detecter_doublons_jours, wait_for_dom_after
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT

__all__ = ["AutomationOrchestrator", "detecter_doublons_jours"]

# pragma: no cover

if TYPE_CHECKING:
    from sele_saisie_auto.saisie_automatiser_psatime import SaisieContext


class AutomationOrchestrator:
    """Coordinate calls between the automation services.

    This orchestrator only sequences the high level steps required to fill a
    PSA Time sheet. Every domain specific operation (form interactions,
    alert handling, plugin execution, etc.) is handled by dedicated classes.
    Its single responsibility is therefore to call these helpers in the right
    order via the :meth:`run` entry point.
    """

    def __init__(
        self,
        config: AppConfig,
        logger: Logger,
        browser_session: BrowserSession,
        login_handler: LoginHandler,
        date_entry_page: DateEntryPage,
        additional_info_page: AdditionalInfoPage,
        context: SaisieContext,
        choix_user: bool = True,
        *,
        timesheet_helper_cls: type[TimeSheetHelper] = TimeSheetHelper,
        cleanup_resources: Callable[[object, object, object], None] | None = None,
        resource_manager: ResourceManager | None = None,
    ) -> None:
        self.config = config
        self.logger = logger
        self.browser_session = browser_session
        self.login_handler = login_handler
        self.date_entry_page = date_entry_page
        self.additional_info_page = additional_info_page
        self.context = context
        self.choix_user = choix_user
        self.timesheet_helper_cls = timesheet_helper_cls
        self._cleanup_callback = cleanup_resources
        self.resource_manager = resource_manager or ResourceManager(logger.log_file)
        self.page_navigator: PageNavigator | None = None
        try:
            self.resource_manager._encryption_service = context.encryption_service
            self.resource_manager._config_manager = types.SimpleNamespace(
                load=lambda: config
            )
            self.resource_manager._session = browser_session
            self.resource_manager._app_config = config
        except Exception:  # nosec B110 - best effort configuration
            pass

    # ------------------------------------------------------------------
    # Alternate constructor
    # ------------------------------------------------------------------
    @classmethod
    def from_components(
        cls,
        resource_manager: ResourceManager,
        page_navigator: PageNavigator,
        service_configurator: ServiceConfigurator,
        context: SaisieContext,
        logger: Logger,
        choix_user: bool = True,
        *,
        timesheet_helper_cls: type[TimeSheetHelper] = TimeSheetHelper,
        cleanup_resources: Callable[[object, object, object], None] | None = None,
    ) -> AutomationOrchestrator:
        """Create an orchestrator from high level components."""

        inst = cls(
            service_configurator.app_config,
            logger,
            page_navigator.browser_session,
            page_navigator.login_handler,
            page_navigator.date_entry_page,
            page_navigator.additional_info_page,
            context,
            choix_user,
            timesheet_helper_cls=timesheet_helper_cls,
            cleanup_resources=cleanup_resources,
            resource_manager=resource_manager,
        )
        inst.resource_manager = resource_manager
        inst.page_navigator = page_navigator
        inst.service_configurator = service_configurator
        return inst

    def initialize_shared_memory(self):  # pragma: no cover - tested elsewhere
        """Delegate credential retrieval to :class:`ResourceManager`."""

        return self.resource_manager.initialize_shared_memory(self.logger)

    def cleanup_resources(self, mem_key, mem_login, mem_pwd) -> None:
        """Release all held resources."""

        if self._cleanup_callback:
            self._cleanup_callback(mem_key, mem_login, mem_pwd)
        else:
            self.resource_manager.close()

    # ------------------------------------------------------------------
    # DOM & iframe helpers
    # ------------------------------------------------------------------
    def wait_for_dom(self, driver) -> None:  # pragma: no cover - simple wrapper
        """Delegate DOM wait to :class:`BrowserSession`."""

        self.browser_session.wait_for_dom(driver)

    @wait_for_dom_after
    def switch_to_iframe_main_target_win0(
        self, driver
    ):  # pragma: no cover - simple wrapper
        """Switch to the ``main_target_win0`` iframe."""

        waiter = self.browser_session.waiter
        switched_to_iframe = None
        element_present = waiter.wait_for_element(
            driver,
            By.ID,
            Locators.MAIN_FRAME.value,
            timeout=DEFAULT_TIMEOUT,
        )
        if element_present:
            switched_to_iframe = self.browser_session.go_to_iframe(
                Locators.MAIN_FRAME.value
            )
        self.wait_for_dom(driver)
        if switched_to_iframe is None:
            raise NameError("main_target_win0 not found")
        return switched_to_iframe

    def _process_date_entry(self, driver) -> None:  # pragma: no cover - simple wrapper
        """Renseigne la date cible dans l'interface."""

        self.date_entry_page.process_date(driver, self.config.date_cible)

    def navigate_from_home_to_date_entry_page(
        self, driver
    ):  # pragma: no cover - simple wrapper
        """Navigate to the date entry page."""

        return self.date_entry_page.navigate_from_home_to_date_entry_page(driver)

    def submit_date_cible(self, driver):  # pragma: no cover - simple wrapper
        """Submit the selected date."""

        return self.date_entry_page.submit_date_cible(driver)

    @wait_for_dom_after
    def navigate_from_work_schedule_to_additional_information_page(
        self, driver
    ):  # pragma: no cover - simple wrapper
        """Open the additional information modal."""

        return self.additional_info_page.navigate_from_work_schedule_to_additional_information_page(
            driver
        )

    @wait_for_dom_after
    def submit_and_validate_additional_information(
        self, driver
    ):  # pragma: no cover - simple wrapper
        """Fill in and submit the additional information."""

        return self.additional_info_page.submit_and_validate_additional_information(
            driver
        )

    @wait_for_dom_after
    def save_draft_and_validate(self, driver):  # pragma: no cover - simple wrapper
        """Save the current timesheet as draft."""

        return self.additional_info_page.save_draft_and_validate(driver)

    def _fill_and_save_timesheet(self, driver) -> None:
        """Delegate the complete timesheet workflow to :class:`PageNavigator`."""

        helper = self.timesheet_helper_cls(
            context_from_app_config(self.config, self.logger.log_file),
            self.logger,
            waiter=self.browser_session.waiter,
        )
        self.page_navigator.timesheet_helper = helper
        self.page_navigator.fill_timesheet(driver)
        self.page_navigator.finalize_timesheet(driver)

    def run(  # pragma: no cover - integration tested via main automation
        self,
        *,
        headless: bool = False,
        no_sandbox: bool = False,
    ) -> None:
        """Execute the high level automation sequence.

        This method only coordinates calls to the injected services.
        All domain specific logic is delegated outside this class.
        """

        if self.config is None:
            self.config = ConfigManager().load()

        with self.resource_manager as rm:
            creds = rm.initialize_shared_memory(self.logger)
            driver = rm.get_driver(headless=headless, no_sandbox=no_sandbox)
            try:
                if hasattr(self.page_navigator, "prepare") and hasattr(
                    self.page_navigator, "run"
                ):
                    self.page_navigator.prepare(creds, self.config.date_cible)
                    self.page_navigator.run(driver)
                else:
                    self.page_navigator.login(
                        driver,
                        creds.aes_key,
                        creds.login,
                        creds.password,
                    )
                    result = self.page_navigator.navigate_to_date_entry(
                        driver, self.config.date_cible
                    )
                    if result is not False:
                        self._fill_and_save_timesheet(driver)
            finally:
                self.cleanup_resources(
                    creds.mem_key,
                    creds.mem_login,
                    creds.mem_password,
                )
