from __future__ import annotations

from sele_saisie_auto import plugins
from sele_saisie_auto.automation import (
    AdditionalInfoPage,
    BrowserSession,
    DateEntryPage,
    LoginHandler,
)
from sele_saisie_auto.remplir_jours_feuille_de_temps import TimeSheetHelper
from sele_saisie_auto.selenium_utils import detecter_doublons_jours

__all__ = ["PageNavigator"]


class PageNavigator:
    """Drive the navigation between PSA Time pages.

    The navigator's single responsibility is to chain page objects to achieve
    a complete submission of the timesheet while leaving all business logic to
    those pages.
    """

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
        """Connecte l'utilisateur à PSA Time via :class:`LoginHandler`."""
        self.login_handler.connect_to_psatime(
            driver, aes_key, encrypted_login, encrypted_password
        )

    def navigate_to_date_entry(self, driver, date_cible: str | None) -> None:
        """Ouvre la page de sélection de période et choisit ``date_cible``."""
        if self.date_entry_page.navigate_from_home_to_date_entry_page(driver):
            self.date_entry_page.process_date(driver, date_cible)

    def fill_timesheet(self, driver) -> None:
        """Remplit la feuille de temps puis les informations additionnelles."""
        self.timesheet_helper.run(driver)
        self.additional_info_page.navigate_from_work_schedule_to_additional_information_page(
            driver
        )
        self.additional_info_page.submit_and_validate_additional_information(driver)
        self.browser_session.go_to_default_content()

    def submit_timesheet(self, driver) -> None:
        """Enregistre le brouillon et lance la validation finale."""
        self.additional_info_page.save_draft_and_validate(driver)

    def finalize_timesheet(self, driver) -> None:
        """Detect duplicates, run hooks and submit the draft."""

        detecter_doublons_jours(driver)
        plugins.call("before_submit", driver)
        self.submit_timesheet(driver)

    # ------------------------------------------------------------------
    # Low level delegations used by legacy APIs
    # ------------------------------------------------------------------

    def navigate_from_home_to_date_entry_page(self, driver):
        """Simple wrapper around :class:`DateEntryPage` navigation."""
        return self.date_entry_page.navigate_from_home_to_date_entry_page(driver)

    def submit_date_cible(self, driver):
        """Delegate date submission to :class:`DateEntryPage`."""
        return self.date_entry_page.submit_date_cible(driver)

    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        """Open the additional information dialog from the schedule grid."""
        return self.additional_info_page.navigate_from_work_schedule_to_additional_information_page(
            driver
        )

    def submit_and_validate_additional_information(self, driver):
        """Submit the additional information form."""
        return self.additional_info_page.submit_and_validate_additional_information(
            driver
        )

    def save_draft_and_validate(self, driver):
        """Delegate draft saving to :class:`AdditionalInfoPage`."""
        return self.additional_info_page.save_draft_and_validate(driver)
