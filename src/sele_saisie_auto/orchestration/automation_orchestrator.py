from __future__ import annotations

from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.automation import (
    AdditionalInfoPage,
    BrowserSession,
    DateEntryPage,
    LoginHandler,
)
from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.remplir_jours_feuille_de_temps import (
    TimeSheetHelper,
    context_from_app_config,
)


class AutomationOrchestrator:
    """High level orchestrator composed of smaller automation services."""

    def __init__(
        self,
        config: AppConfig,
        logger: Logger,
        browser_session: BrowserSession,
        login_handler: LoginHandler,
        date_entry_page: DateEntryPage,
        additional_info_page: AdditionalInfoPage,
        *,
        timesheet_helper_cls: type[TimeSheetHelper] = TimeSheetHelper,
    ) -> None:
        self.config = config
        self.logger = logger
        self.browser_session = browser_session
        self.login_handler = login_handler
        self.date_entry_page = date_entry_page
        self.additional_info_page = additional_info_page
        self.timesheet_helper_cls = timesheet_helper_cls

    def run(
        self,
        aes_key: bytes,
        encrypted_login: bytes,
        encrypted_password: bytes,
        *,
        headless: bool = False,
        no_sandbox: bool = False,
    ) -> None:
        """Execute the full PSA Time automation flow."""
        with self.browser_session as session:
            driver = session.open(
                self.config.url,
                headless=headless,
                no_sandbox=no_sandbox,
            )
            self.login_handler.connect_to_psatime(
                driver, aes_key, encrypted_login, encrypted_password
            )
            if self.date_entry_page.navigate_from_home_to_date_entry_page(driver):
                self.date_entry_page.process_date(driver, self.config.date_cible)
                helper = self.timesheet_helper_cls(
                    context_from_app_config(self.config, self.logger.log_file),
                    self.logger,
                    waiter=session.waiter,
                )
                helper.run(driver)
                self.additional_info_page.navigate_from_work_schedule_to_additional_information_page(
                    driver
                )
                self.additional_info_page.submit_and_validate_additional_information(
                    driver
                )
                session.go_to_default_content()
                self.additional_info_page.save_draft_and_validate(driver)
