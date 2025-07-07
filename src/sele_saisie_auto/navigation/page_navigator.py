from __future__ import annotations

from sele_saisie_auto.automation import (
    AdditionalInfoPage,
    BrowserSession,
    DateEntryPage,
    LoginHandler,
)
from sele_saisie_auto.remplir_jours_feuille_de_temps import TimeSheetHelper


class PageNavigator:
    """Coordinate high level navigation between PSA Time pages."""

    def __init__(
        self,
        browser_session: BrowserSession,
        login_handler: LoginHandler,
        date_entry_page: DateEntryPage,
        additional_info_page: AdditionalInfoPage,
        timesheet_helper: TimeSheetHelper,
    ) -> None:
        self.browser_session = browser_session
        self.login_handler = login_handler
        self.date_entry_page = date_entry_page
        self.additional_info_page = additional_info_page
        self.timesheet_helper = timesheet_helper

    # ------------------------------------------------------------------
    # Delegated actions
    # ------------------------------------------------------------------
    def login(
        self,
        driver,
        aes_key: bytes,
        encrypted_login: bytes,
        encrypted_password: bytes,
    ) -> None:
        """Delegate user login to :class:`LoginHandler`."""
        self.login_handler.connect_to_psatime(
            driver, aes_key, encrypted_login, encrypted_password
        )

    def navigate_to_date_entry(self, driver, date_cible: str | None) -> None:
        """Navigate to the date entry page and select the period."""
        if self.date_entry_page.navigate_from_home_to_date_entry_page(driver):
            self.date_entry_page.process_date(driver, date_cible)

    def fill_timesheet(self, driver) -> None:
        """Fill the timesheet and additional information."""
        self.timesheet_helper.run(driver)
        self.additional_info_page.navigate_from_work_schedule_to_additional_information_page(
            driver
        )
        self.additional_info_page.submit_and_validate_additional_information(driver)
        self.browser_session.go_to_default_content()

    def submit_timesheet(self, driver) -> None:
        """Save the draft and trigger validation."""
        self.additional_info_page.save_draft_and_validate(driver)
