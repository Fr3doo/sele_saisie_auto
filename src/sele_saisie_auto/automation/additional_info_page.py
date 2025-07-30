from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec

from sele_saisie_auto.additional_info_locators import ADDITIONAL_INFO_LOCATORS
from sele_saisie_auto.alerts import AlertHandler
from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.decorators import handle_selenium_errors
from sele_saisie_auto.interfaces import WaiterProtocol
from sele_saisie_auto.locators import Locators
from sele_saisie_auto.logger_utils import format_message, write_log
from sele_saisie_auto.remplir_informations_supp_utils import ExtraInfoHelper
from sele_saisie_auto.saisie_context import SaisieContext
from sele_saisie_auto.selenium_utils import wait_for_dom_after
from sele_saisie_auto.selenium_utils.waiter_factory import create_waiter
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT

if TYPE_CHECKING:
    from sele_saisie_auto.saisie_automatiser_psatime import PSATimeAutomation


def ensure_descriptions(context: SaisieContext) -> None:
    """Populate ``context.descriptions`` from ``context.config`` if empty."""

    if getattr(context, "descriptions", None):
        return

    cfg = context.config
    context.descriptions = [
        {
            "description_cible": "Temps de repos de 11h entre 2 jours travaillés respecté",
            "id_value_ligne": ADDITIONAL_INFO_LOCATORS["ROW_DESCR100"],
            "id_value_jours": ADDITIONAL_INFO_LOCATORS["DAY_UC_DAILYREST"],
            "type_element": "select",
            "valeurs_a_remplir": cfg.additional_information.get(
                "periode_repos_respectee",
                {},
            ),
        },
        {
            "description_cible": (
                "Mon temps de travail effectif a débuté entre 8h00 et 10h00 et Mon temps de travail effectif a pris fin entre 16h30 et 19h00"
            ),
            "id_value_ligne": ADDITIONAL_INFO_LOCATORS["ROW_DESCR100"],
            "id_value_jours": ADDITIONAL_INFO_LOCATORS["DAY_UC_DAILYREST"],
            "type_element": "select",
            "valeurs_a_remplir": cfg.additional_information.get(
                "horaire_travail_effectif",
                {},
            ),
        },
        {
            "description_cible": "J\u2019ai travaillé plus d\u2019une demi-journée",
            "id_value_ligne": ADDITIONAL_INFO_LOCATORS["ROW_DESCR100"],
            "id_value_jours": ADDITIONAL_INFO_LOCATORS["DAY_UC_DAILYREST"],
            "type_element": "select",
            "valeurs_a_remplir": cfg.additional_information.get(
                "plus_demi_journee_travaillee",
                {},
            ),
        },
        {
            "description_cible": "Durée de la pause déjeuner",
            "id_value_ligne": ADDITIONAL_INFO_LOCATORS["ROW_DESCR200"],
            "id_value_jours": ADDITIONAL_INFO_LOCATORS["DAY_UC_DAILYREST_SPECIAL"],
            "type_element": "input",
            "valeurs_a_remplir": cfg.additional_information.get(
                "duree_pause_dejeuner",
                {},
            ),
        },
        {
            "description_cible": "Matin",
            "id_value_ligne": ADDITIONAL_INFO_LOCATORS["ROW_DESCR"],
            "id_value_jours": ADDITIONAL_INFO_LOCATORS["DAY_UC_LOCATION_A"],
            "type_element": "select",
            "valeurs_a_remplir": cfg.work_location_am,
        },
        {
            "description_cible": "Après-midi",
            "id_value_ligne": ADDITIONAL_INFO_LOCATORS["ROW_DESCR"],
            "id_value_jours": ADDITIONAL_INFO_LOCATORS["DAY_UC_LOCATION_A"],
            "type_element": "select",
            "valeurs_a_remplir": cfg.work_location_pm,
        },
    ]


class AdditionalInfoPage:
    """Handle the additional information modal."""

    @classmethod
    def from_automation(
        cls, automation: PSATimeAutomation, waiter: WaiterProtocol | None = None
    ) -> AdditionalInfoPage:
        """Create a page instance from a :class:`PSATimeAutomation`."""
        return cls(automation, waiter=waiter)

    def __init__(
        self, automation: PSATimeAutomation, waiter: WaiterProtocol | None = None
    ) -> None:
        self._automation = automation
        self.context = getattr(automation, "context", None)
        self.browser_session = getattr(automation, "browser_session", None)
        self._log_file = automation.log_file
        self.logger = automation.logger
        cfg = None
        if isinstance(self.context, SaisieContext):
            cfg = self.context.config
        if waiter is not None:
            self.waiter = waiter
        else:
            base_waiter = getattr(automation, "waiter", None)
            if base_waiter is not None:
                self.waiter = base_waiter
            else:
                timeout = DEFAULT_TIMEOUT
                if cfg is not None and hasattr(cfg, "default_timeout"):
                    timeout = cfg.default_timeout
                self.waiter = create_waiter(timeout)
                if cfg is not None and hasattr(cfg, "long_timeout"):
                    self.waiter.wrapper.long_timeout = cfg.long_timeout
        self.alert_handler = AlertHandler(automation, waiter=self.waiter)
        self.helper = ExtraInfoHelper(
            logger=self.logger,
            waiter=self.waiter,
            page=self,
            app_config=cfg if cfg is not None else None,
        )
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        sap.traiter_description = self.helper.traiter_description
        if self.context is not None:
            ensure_descriptions(cast(SaisieContext, self.context))

    @property
    def log_file(self) -> str:
        return self._log_file

    @property
    def config(self) -> AppConfig | SimpleNamespace:
        cfg = None
        if isinstance(self.context, SaisieContext):
            cfg = self.context.config
        if cfg is None or not hasattr(cfg, "default_timeout"):
            return SimpleNamespace(
                default_timeout=DEFAULT_TIMEOUT,
                long_timeout=LONG_TIMEOUT,
            )
        return cfg

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def wait_for_dom(self, driver: WebDriver, max_attempts: int | None = None) -> None:
        self._automation.wait_for_dom(driver, max_attempts=max_attempts)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @wait_for_dom_after
    @handle_selenium_errors(default_return=False)
    def navigate_from_work_schedule_to_additional_information_page(
        self, driver: WebDriver
    ) -> bool:
        """Open the modal to fill additional informations."""
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        try:
            self.wait_for_dom(driver)
            element_present = self.waiter.wait_for_element(
                driver,
                By.ID,
                Locators.ADDITIONAL_INFO_LINK.value,
                ec.element_to_be_clickable,
                timeout=self.config.default_timeout,
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"❌ Error locating additional info link: {exc}")
            return False

        if not element_present:
            return False

        try:
            sap.click_element_without_wait(
                driver, cast(By, By.ID), Locators.ADDITIONAL_INFO_LINK.value
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"❌ Error clicking additional info link: {exc}")
            return False

        if self.browser_session is not None:
            self.browser_session.go_to_default_content()
        self.wait_for_dom(driver)
        return True

    @wait_for_dom_after
    @handle_selenium_errors(default_return=False)
    def submit_and_validate_additional_information(self, driver: WebDriver) -> bool:
        """Fill all additional info fields and validate the modal."""
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        try:
            element_present = self.waiter.wait_for_element(
                driver,
                By.ID,
                Locators.MODAL_FRAME.value,
                timeout=self.config.default_timeout,
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"❌ Error locating modal iframe: {exc}")
            return False

        switched_to_iframe = False
        if element_present and self.browser_session is not None:
            try:
                switched_to_iframe = self.browser_session.go_to_iframe(
                    Locators.MODAL_FRAME.value
                )
            except Exception as exc:  # noqa: BLE001
                self.logger.error(f"❌ Error switching to iframe: {exc}")
                return False

        if switched_to_iframe:
            descriptions = getattr(self.context, "descriptions", [])
            for config in descriptions:
                try:
                    sap.traiter_description(driver, config)
                except Exception as exc:  # noqa: BLE001
                    self.logger.error(
                        f"❌ Error processing description '{config}': {exc}"
                    )
                    return False
            write_log(
                format_message("ADDITIONAL_INFO_DONE", {}),
                self.log_file,
                "INFO",
            )

        try:
            element_present = self.waiter.wait_for_element(
                driver,
                By.ID,
                Locators.SAVE_ICON.value,
                ec.element_to_be_clickable,
                timeout=self.config.default_timeout,
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"❌ Error locating save icon: {exc}")
            return False

        if not element_present:
            return False

        try:
            sap.click_element_without_wait(
                driver, cast(By, By.ID), Locators.SAVE_ICON.value
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"❌ Error clicking save icon: {exc}")
            return False
        return True

    @wait_for_dom_after
    @handle_selenium_errors(default_return=False)
    def save_draft_and_validate(self, driver: WebDriver) -> bool:
        """Click the save draft button and wait for completion."""
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        try:
            element_present = self.waiter.wait_for_element(
                driver,
                By.ID,
                Locators.SAVE_DRAFT_BUTTON.value,
                ec.element_to_be_clickable,
                timeout=self.config.default_timeout,
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"❌ Error locating draft button: {exc}")
            return False

        if not element_present:
            return False

        try:
            sap.click_element_without_wait(
                driver, cast(By, By.ID), Locators.SAVE_DRAFT_BUTTON.value
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"❌ Error clicking draft button: {exc}")
            return False

        self.wait_for_dom(driver)
        self._handle_save_alerts(driver)
        return True

    @handle_selenium_errors(default_return=None)
    def _handle_save_alerts(self, driver: WebDriver) -> None:
        """Dismiss any alert shown after saving."""

        self.alert_handler.handle_alerts(driver, "save_alerts")

    def log_information_details(self) -> None:
        """Log the extra information configuration details."""

        if not isinstance(self.context, SaisieContext):
            return
        cfg = self.context.config

        sections = {
            "periode_repos_respectee": "👉 Infos_supp_cgi_periode_repos_respectee:",
            "horaire_travail_effectif": "👉 Infos_supp_cgi_horaire_travail_effectif:",
            "plus_demi_journee_travaillee": "👉 Planning de travail de la semaine:",
            "duree_pause_dejeuner": "👉 Infos_supp_cgi_duree_pause_dejeuner:",
        }

        for key, title in sections.items():
            write_log(title, self.log_file, "DEBUG")
            values = cast(dict[str, str], cfg.additional_information.get(key, {}))
            for day, status in values.items():
                write_log(f"🔹 '{day}': '{status}'", self.log_file, "DEBUG")
