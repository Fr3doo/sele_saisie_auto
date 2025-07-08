from __future__ import annotations

from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By

from sele_saisie_auto import messages
from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.form_processing.description_processor import process_description
from sele_saisie_auto.logger_utils import write_log
from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.selenium_utils import Waiter
from sele_saisie_auto.strategies import (
    ElementFillingContext,
    InputFillingStrategy,
    SelectFillingStrategy,
)
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT

# remplir_informations_supp_france.py

if TYPE_CHECKING:  # pragma: no cover
    from sele_saisie_auto.automation.additional_info_page import AdditionalInfoPage


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
    driver,
    config,
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
    ) -> None:
        """Initialise l'assistant avec ``Logger`` et ``Waiter``."""
        if waiter is None:
            timeout = app_config.default_timeout if app_config else DEFAULT_TIMEOUT
            long_timeout = app_config.long_timeout if app_config else LONG_TIMEOUT
            self.waiter = Waiter(default_timeout=timeout, long_timeout=long_timeout)
        else:
            self.waiter = waiter
        self.page = page
        self.logger = logger
        self.log_file = logger.log_file

    def set_page(self, page: AdditionalInfoPage) -> None:
        """Définit la page d'informations supplémentaires."""
        self.page = page

    def traiter_description(self, driver, config):
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
    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        """Ouvre la fenêtre des informations supplémentaires."""
        if not self.page:
            raise RuntimeError("AdditionalInfoPage not configured")
        return self.page.navigate_from_work_schedule_to_additional_information_page(
            driver
        )

    def submit_and_validate_additional_information(self, driver):
        """Valide les informations supplémentaires et ferme la fenêtre."""
        if not self.page:
            raise RuntimeError("AdditionalInfoPage not configured")
        return self.page.submit_and_validate_additional_information(driver)
