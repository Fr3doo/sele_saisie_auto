# src\sele_saisie_auto\remplir_informations_supp_utils.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.form_processing.description_processor import process_description
from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.selenium_utils import Waiter
from sele_saisie_auto.selenium_utils.waiter_factory import create_waiter
from sele_saisie_auto.strategies import (
    ElementFillingContext,
    InputFillingStrategy,
    SelectFillingStrategy,
)
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT

# remplir_informations_supp_france.py

if TYPE_CHECKING:
    from sele_saisie_auto.automation.additional_info_page import AdditionalInfoPage
    from sele_saisie_auto.remplir_jours_feuille_de_temps import TimeSheetHelper


# ------------------------------------------------------------------------------------------- #
# ----------------------------------- HELPERS ---------------------------------
# ------------------------------------------------------------------------------


def _context_from_type(type_element: str) -> ElementFillingContext | None:
    """Return an :class:`ElementFillingContext` for ``type_element``."""
    if type_element == "select":
        return ElementFillingContext(SelectFillingStrategy())
    if type_element == "input":
        return ElementFillingContext(InputFillingStrategy())
    return None


def traiter_description(
    driver: WebDriver,
    config: dict[str, str],
    log_file: str,
    waiter: Waiter | None = None,
    *,
    logger: Logger | None = None,
) -> None:
    """Wrapper around :func:`process_description`."""
    context = _context_from_type(config.get("type_element", ""))
    process_description(
        driver,
        config,
        log_file,
        waiter=waiter,
        filling_context=context,
        logger=logger,
    )


class ExtraInfoHelper:
    """Facade class using ``traiter_description`` with a shared ``Waiter``."""

    def __init__(
        self,
        logger: Logger,
        waiter: Waiter | None = None,
        page: AdditionalInfoPage | None = None,
        app_config: AppConfig | None = None,
        timesheet_helper: "TimeSheetHelper" | None = None,
    ) -> None:
        """Initialise l'assistant avec ``Logger`` et ``Waiter``."""
        if waiter is None:
            timeout = DEFAULT_TIMEOUT
            if hasattr(app_config, "default_timeout"):
                timeout = app_config.default_timeout
            self.waiter = create_waiter(timeout)
            if hasattr(app_config, "long_timeout"):
                self.waiter.wrapper.long_timeout = app_config.long_timeout
        else:
            self.waiter = waiter
        self.page = page
        self.logger = logger
        self.log_file = logger.log_file
        self.timesheet_helper = timesheet_helper

    def set_page(self, page: AdditionalInfoPage) -> None:
        """Définit la page d'informations supplémentaires."""
        self.page = page

    def set_timesheet_helper(self, helper: "TimeSheetHelper") -> None:
        """Injecte une instance de :class:`TimeSheetHelper`."""
        self.timesheet_helper = helper

    def traiter_description(self, driver: WebDriver, config: dict[str, str]) -> None:
        """Applique :func:`traiter_description` en utilisant l'instance courante."""
        traiter_description(
            driver,
            config,
            self.log_file,
            waiter=self.waiter,
            logger=self.logger,
        )

    # ------------------------------------------------------------------
    # Delegation to :class:`AdditionalInfoPage`
    # ------------------------------------------------------------------
    def navigate_from_work_schedule_to_additional_information_page(
        self, driver: WebDriver
    ) -> Any:
        """Ouvre la fenêtre des informations supplémentaires."""
        if not self.page:
            raise RuntimeError("AdditionalInfoPage not configured")
        return self.page.navigate_from_work_schedule_to_additional_information_page(
            driver
        )

    def submit_and_validate_additional_information(self, driver: WebDriver) -> Any:
        """Valide les informations supplémentaires et ferme la fenêtre."""
        if not self.page:
            raise RuntimeError("AdditionalInfoPage not configured")
        return self.page.submit_and_validate_additional_information(driver)
