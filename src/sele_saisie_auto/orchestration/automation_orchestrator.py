# src\sele_saisie_auto\orchestration\automation_orchestrator.py
# pragma: no cover
from __future__ import annotations

import types
from typing import TYPE_CHECKING, Any, Callable, cast

from selenium.webdriver.common.by import By

from sele_saisie_auto.alerts import AlertHandler
from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.config_manager import ConfigManager
from sele_saisie_auto.configuration import ServiceConfigurator
from sele_saisie_auto.interfaces import (
    AdditionalInfoPageProtocol,
    BrowserSessionProtocol,
    DateEntryPageProtocol,
    LoggerProtocol,
    LoginHandlerProtocol,
    TimeSheetHelperProtocol,
)
from sele_saisie_auto.locators import Locators
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
        logger: LoggerProtocol,
        browser_session: BrowserSessionProtocol,
        login_handler: LoginHandlerProtocol,
        date_entry_page: DateEntryPageProtocol,
        additional_info_page: AdditionalInfoPageProtocol,
        context: SaisieContext,
        choix_user: bool = True,
        *,
        alert_handler: AlertHandler | None = None,
        timesheet_helper_cls: type[TimeSheetHelperProtocol] = TimeSheetHelper,
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
        self.resource_manager = resource_manager or ResourceManager(
            cast(str, logger.log_file)  # logger.log_file peut être None
        )
        self.page_navigator: PageNavigator | None = None
        self.service_configurator: ServiceConfigurator | None = None
        self.log_file = logger.log_file
        self.waiter = getattr(browser_session, "waiter", None)
        # AlertHandler attend `PSATimeAutomation`; on force le type pour éviter
        # l’incompatibilité de type avec AlertHandlerProtocol.
        self.alert_handler = alert_handler or AlertHandler(self, waiter=self.waiter)  # type: ignore[arg-type]
        try:
            self.resource_manager._encryption_service = context.encryption_service
            self.resource_manager._config_manager = cast(
                Any, types.SimpleNamespace(load=lambda: config)
            )
            self.resource_manager._session = browser_session
            setattr(self.resource_manager, "_app_config", config)
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
        logger: LoggerProtocol,
        choix_user: bool = True,
        *,
        alert_handler: AlertHandler | None = None,
        timesheet_helper_cls: type[TimeSheetHelperProtocol] = TimeSheetHelper,
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
            alert_handler=alert_handler,
            timesheet_helper_cls=timesheet_helper_cls,
            cleanup_resources=cleanup_resources,
            resource_manager=resource_manager,
        )
        inst.resource_manager = resource_manager
        inst.page_navigator = page_navigator
        inst.service_configurator = service_configurator
        return inst

    def initialize_shared_memory(self) -> Any:
        """Delegate credential retrieval to :class:`ResourceManager`."""

        # ResourceManager attend Logger | None ; on passe None pour éviter
        # l’incompatibilité de type avec LoggerProtocol.
        return self.resource_manager.initialize_shared_memory(None)

    def cleanup_resources(
        self, mem_key: object, mem_login: object, mem_pwd: object
    ) -> None:
        """Release all held resources."""

        if self._cleanup_callback:
            self._cleanup_callback(mem_key, mem_login, mem_pwd)
        else:
            self.resource_manager.close()

    # ------------------------------------------------------------------
    # DOM & iframe helpers
    # ------------------------------------------------------------------
    def wait_for_dom(self, driver: Any) -> None:  # pragma: no cover
        """Delegate DOM wait to :class:`BrowserSession`."""

        self.browser_session.wait_for_dom(driver)

    @wait_for_dom_after  # type: ignore[misc]
    def switch_to_iframe_main_target_win0(self, driver: Any) -> bool:
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

    def _process_date_entry(self, driver: Any) -> None:
        """Renseigne la date cible dans l'interface."""

        self.date_entry_page.process_date(driver, self.config.date_cible)

    def navigate_from_home_to_date_entry_page(self, driver: Any) -> bool:
        """Navigate to the date entry page."""

        return self.date_entry_page.navigate_from_home_to_date_entry_page(driver)

    def submit_date_cible(self, driver: Any) -> None:
        """Submit the selected date."""

        self.date_entry_page.submit_date_cible(driver)

    @wait_for_dom_after  # type: ignore[misc]
    def navigate_from_work_schedule_to_additional_information_page(
        self, driver: Any
    ) -> bool:
        """Open the additional information modal."""

        return self.additional_info_page.navigate_from_work_schedule_to_additional_information_page(
            driver
        )

    @wait_for_dom_after  # type: ignore[misc]
    def submit_and_validate_additional_information(self, driver: Any) -> None:
        """Fill in and submit the additional information."""

        self.additional_info_page.submit_and_validate_additional_information(driver)

    @wait_for_dom_after  # type: ignore[misc]
    def save_draft_and_validate(
        self, driver: Any
    ) -> None:  # pragma: no cover - simple wrapper
        """Save the current timesheet as draft."""

        self.additional_info_page.save_draft_and_validate(driver)

    def _fill_and_save_timesheet(self, driver: Any) -> None:
        """Delegate the complete timesheet workflow to :class:`PageNavigator`."""
        assert self.page_navigator is not None  # nosec B101
        # Initialize the timesheet helper with the context and logger
        helper = cast(
            TimeSheetHelper,
            self.timesheet_helper_cls(  # type: ignore[call-arg]
                context_from_app_config(
                    self.config,
                    cast(str, self.logger.log_file),
                ),
                self.logger,
                waiter=self.browser_session.waiter,
                additional_info_page=self.additional_info_page,
                browser_session=self.browser_session,
            ),
        )
        assert self.page_navigator is not None  # nosec B101
        self.page_navigator.timesheet_helper = helper
        if hasattr(helper, "additional_info_page"):
            helper.additional_info_page = self.additional_info_page
        if hasattr(helper, "browser_session"):
            helper.browser_session = self.browser_session
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
            creds = rm.initialize_shared_memory(None)
            driver = rm.get_driver(headless=headless, no_sandbox=no_sandbox)
            try:
                if hasattr(self.page_navigator, "prepare") and hasattr(
                    self.page_navigator, "run"
                ):
                    assert self.page_navigator is not None  # nosec B101
                    self.page_navigator.prepare(
                        creds, cast(str, self.config.date_cible)
                    )
                    self.page_navigator.run(driver)
                else:
                    assert self.page_navigator is not None  # nosec B101
                    self.page_navigator.login(
                        driver,
                        creds.aes_key,
                        creds.login,
                        creds.password,
                    )
                    result = self.page_navigator.navigate_to_date_entry(
                        driver, cast(str, self.config.date_cible)
                    )
                    if result is not False:
                        self._fill_and_save_timesheet(driver)
            finally:
                self.cleanup_resources(
                    creds.mem_key,
                    creds.mem_login,
                    creds.mem_password,
                )
