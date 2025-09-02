"""Helpers to fill the timesheet grid.

``DayFiller`` centralises the insertion logic while the thin module-level
functions preserve the historic functional API for compatibility.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto import messages
from sele_saisie_auto.constants import (
    ID_TO_KEY_MAPPING,
    JOURS_SEMAINE,
    LISTES_ID_INFORMATIONS_MISSION,
)
from sele_saisie_auto.interfaces import LoggerProtocol, WaiterProtocol
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT
from sele_saisie_auto.utils.mission import est_en_mission

if TYPE_CHECKING:
    from sele_saisie_auto.remplir_jours_feuille_de_temps import TimeSheetContext

__all__ = ["DayFiller"]

MAX_ATTEMPTS = 5
JOUR_TO_INDEX = {v: k for k, v in JOURS_SEMAINE.items()}


def _rjf() -> Any:
    from sele_saisie_auto import remplir_jours_feuille_de_temps as module

    return cast(Any, module)


def est_en_mission_presente(work_days: dict[str, tuple[str, str]]) -> bool:
    return any(value[0] == "En mission" for value in work_days.values())


def ajouter_jour_a_jours_remplis(jour: str, filled_days: list[str]) -> list[str]:
    if jour not in filled_days:
        filled_days.append(jour)
    return filled_days


def remplir_jours(
    driver: WebDriver,
    item_descriptions: list[str],
    week_days: dict[int, str],
    filled_days: list[str],
    context: "TimeSheetContext",
) -> list[str]:
    return DayFiller(context, logger=None).remplir_jours(
        driver, item_descriptions, week_days, filled_days
    )


def traiter_jour(
    driver: WebDriver,
    jour: str,
    description_cible: str,
    value_to_fill: str,
    filled_days: list[str],
    context: "TimeSheetContext",
) -> list[str]:
    return DayFiller(context, logger=None).traiter_jour(
        driver, jour, description_cible, value_to_fill, filled_days
    )


def remplir_mission_specifique(
    driver: WebDriver,
    jour: str,
    value_to_fill: str,
    filled_days: list[str],
    context: "TimeSheetContext",
) -> None:
    DayFiller(context, logger=None).remplir_mission_specifique(
        driver, jour, value_to_fill, filled_days
    )


def remplir_mission(
    driver: WebDriver,
    work_days: dict[str, tuple[str, str]],
    filled_days: list[str],
    context: "TimeSheetContext",
) -> list[str]:
    return DayFiller(context, logger=None).remplir_mission(
        driver, work_days, filled_days
    )


def insert_with_retries(
    driver: WebDriver,
    field_id: str,
    value: str,
    context: "TimeSheetContext",
    waiter: WaiterProtocol | None = None,
) -> bool:
    return DayFiller(context, logger=None, waiter=waiter).insert_with_retries(
        driver, field_id, value, waiter
    )


def traiter_champs_mission(
    driver: WebDriver,
    listes_id_informations_mission: list[str],
    id_to_key_mapping: dict[str, str],
    project_mission_info: dict[str, str],
    context: "TimeSheetContext",
    max_attempts: int = MAX_ATTEMPTS,
    waiter: WaiterProtocol | None = None,
) -> None:
    DayFiller(context, logger=None, waiter=waiter).traiter_champs_mission(
        driver,
        listes_id_informations_mission,
        id_to_key_mapping,
        project_mission_info,
        max_attempts=max_attempts,
        waiter=waiter,
    )


class DayFiller:
    """Encapsulates the day filling logic."""

    MAX_ATTEMPTS = MAX_ATTEMPTS

    def __init__(
        self,
        context: "TimeSheetContext",
        logger: LoggerProtocol | None,
        waiter: WaiterProtocol | None = None,
    ) -> None:
        self.context = context
        self.waiter = waiter
        self.logger = logger
        log_file = context.log_file if logger is None else logger.log_file
        self.log_file: str = log_file or ""

    def wait_for_dom(
        self, driver: WebDriver, waiter: WaiterProtocol | None = None
    ) -> None:
        from sele_saisie_auto.remplir_jours_feuille_de_temps import (
            wait_for_dom as external_wait_for_dom,
        )

        external_wait_for_dom(driver, waiter)

    @staticmethod
    def _should_skip_field(key: str | None) -> bool:
        return key is None or key == "sub_category_code"

    def _collect_filled_days_for_row(
        self, driver: WebDriver, row_index: int, week_days: dict[int, str]
    ) -> list[str]:
        collected: list[str] = []
        rjf = _rjf()

        for jour_index, jour_name in week_days.items():
            input_id = f"POL_TIME{jour_index}${row_index}"
            element = cast(Any, rjf.wait_for_element)(
                driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT
            )
            if element:
                jour_rempli = rjf.verifier_champ_jour_rempli(element, jour_name)
                if jour_rempli:
                    collected.append(jour_rempli)
        return collected

    def remplir_jours(
        self,
        driver: WebDriver,
        item_descriptions: list[str],
        week_days: dict[int, str],
        filled_days: list[str],
    ) -> list[str]:
        if not item_descriptions:
            return filled_days
        rjf = _rjf()

        for description_cible in item_descriptions:
            row_index = rjf.trouver_ligne_par_description(
                driver, description_cible, "POL_DESCR$"
            )
            if row_index is not None:
                filled_days.extend(
                    self._collect_filled_days_for_row(driver, row_index, week_days)
                )
        return filled_days

    def _get_day_element(
        self, driver: WebDriver, jour: str, description_cible: str
    ) -> tuple[str, Any | None]:
        rjf = _rjf()

        row_index = rjf.trouver_ligne_par_description(
            driver, description_cible, "POL_DESCR$"
        )
        if row_index is None:
            return "", None
        input_id = f"POL_TIME{JOUR_TO_INDEX[jour]}${row_index}"
        element = cast(Any, rjf.wait_for_element)(
            driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT
        )
        return input_id, element

    def traiter_jour(
        self,
        driver: WebDriver,
        jour: str,
        description_cible: str,
        value_to_fill: str,
        filled_days: list[str],
    ) -> list[str]:
        if jour in filled_days or not description_cible:
            return filled_days
        input_id, element = self._get_day_element(driver, jour, description_cible)
        waiter = self.waiter
        if element is None or not self.insert_with_retries(
            driver, input_id, value_to_fill, waiter
        ):
            return filled_days
        ajouter_jour_a_jours_remplis(jour, filled_days)
        rjf = _rjf()

        rjf.afficher_message_insertion(
            jour, value_to_fill, 0, "après insertion", self.log_file
        )
        return filled_days

    def remplir_mission_specifique(
        self,
        driver: WebDriver,
        jour: str,
        value_to_fill: str,
        filled_days: list[str],
    ) -> None:
        rjf = _rjf()

        input_id = f"TIME{JOUR_TO_INDEX[jour]}$0"
        element = cast(Any, rjf.wait_for_element)(
            driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT
        )
        waiter = self.waiter
        if element and self.insert_with_retries(
            driver, input_id, value_to_fill, waiter
        ):
            ajouter_jour_a_jours_remplis(jour, filled_days)
            rjf.afficher_message_insertion(
                jour, value_to_fill, 0, "après insertion", self.log_file
            )

    def remplir_mission(
        self,
        driver: WebDriver,
        work_days: dict[str, tuple[str, str]],
        filled_days: list[str],
    ) -> list[str]:
        for jour, (description_cible, value_to_fill) in work_days.items():
            if jour in filled_days or not description_cible:
                continue
            if est_en_mission(description_cible):
                self.remplir_mission_specifique(
                    driver, jour, value_to_fill, filled_days
                )
            else:
                self.traiter_jour(
                    driver, jour, description_cible, value_to_fill, filled_days
                )
        return filled_days

    def _wait_and_get_element(
        self, driver: WebDriver, field_id: str, waiter: WaiterProtocol | None
    ) -> Any | None:
        rjf = _rjf()

        self.wait_for_dom(driver, waiter)
        getter: Callable[..., Any] = (
            waiter.wait_for_element if waiter else cast(Any, rjf.wait_for_element)
        )
        return getter(driver, By.ID, field_id, timeout=DEFAULT_TIMEOUT)

    def _try_fill_once(self, driver: WebDriver, field_id: str, value: str) -> bool:
        rjf = _rjf()

        input_field, is_correct_value = rjf.detecter_et_verifier_contenu(
            driver, field_id, value
        )
        if input_field is None:
            raise RuntimeError("detecter_et_verifier_contenu returned None")
        if is_correct_value:
            rjf.write_log(
                f"Valeur correcte déjà présente pour '{field_id}'.",
                self.log_file,
                "DEBUG",
            )
            return True
        rjf.effacer_et_entrer_valeur(input_field, value)
        rjf.program_break_time(1, "Stabilisation du DOM après insertion.")
        rjf.write_log(messages.DOM_STABLE, self.log_file, "DEBUG")
        if cast(Callable[[Any, str], bool], rjf.controle_insertion)(input_field, value):
            rjf.write_log(
                f"Valeur '{value}' insérée avec succès pour '{field_id}'.",
                self.log_file,
                "DEBUG",
            )
            return True
        return False

    def _log_insert_failure(self, field_id: str, max_attempts: int) -> None:
        rjf = _rjf()

        rjf.write_log(
            f"{messages.ECHEC_INSERTION} pour '{field_id}' après {max_attempts} tentatives.",
            self.log_file,
            "ERROR",
        )

    def _insert_value_with_retries(
        self,
        driver: WebDriver,
        field_id: str,
        value: str,
        max_attempts: int,
        waiter: WaiterProtocol | None,
    ) -> bool:
        if not self._wait_and_get_element(driver, field_id, waiter):
            return False
        for attempt in range(max_attempts):
            try:
                if self._try_fill_once(driver, field_id, value):
                    return True
            except StaleElementReferenceException:
                rjf = _rjf()

                rjf.write_log(
                    f"{messages.REFERENCE_OBSOLETE} pour '{field_id}', tentative {attempt + 1}.",
                    self.log_file,
                    "ERROR",
                )
        self._log_insert_failure(field_id, max_attempts)
        return False

    def insert_with_retries(
        self,
        driver: WebDriver,
        field_id: str,
        value: str,
        waiter: WaiterProtocol | None = None,
    ) -> bool:
        waiter_to_use = waiter or self.waiter
        return self._insert_value_with_retries(
            driver, field_id, value, MAX_ATTEMPTS, waiter_to_use
        )

    # ------------------------------------------------------------------
    # High level helpers used by :class:`TimeSheetHelper`
    # ------------------------------------------------------------------

    def fill_standard_days(
        self, driver: WebDriver, filled_days: list[str]
    ) -> list[str]:
        return remplir_jours(
            driver,
            self.context.item_descriptions,
            JOURS_SEMAINE,
            filled_days,
            self.context,
        )

    def fill_work_missions(
        self, driver: WebDriver, filled_days: list[str]
    ) -> list[str]:
        return remplir_mission(
            driver, self.context.work_days, filled_days, self.context
        )

    def handle_additional_fields(self, driver: WebDriver) -> None:
        if est_en_mission_presente(self.context.work_days):
            traiter_champs_mission(
                driver,
                LISTES_ID_INFORMATIONS_MISSION,
                ID_TO_KEY_MAPPING,
                self.context.project_mission_info,
                self.context,
                waiter=self.waiter,
            )

    def traiter_champs_mission(
        self,
        driver: WebDriver,
        listes_id_informations_mission: list[str],
        id_to_key_mapping: dict[str, str],
        project_mission_info: dict[str, str],
        max_attempts: int = MAX_ATTEMPTS,
        waiter: WaiterProtocol | None = None,
    ) -> None:
        rjf = _rjf()

        for id in listes_id_informations_mission:
            key = id_to_key_mapping.get(id)
            if self._should_skip_field(key):
                continue
            key = cast(str, key)
            value_to_fill = project_mission_info.get(key)
            if not value_to_fill:
                rjf.write_log(
                    f"Aucune valeur trouvée pour le champ '{key}' (ID: {id}).",
                    self.log_file,
                    "DEBUG",
                )
                continue
            rjf.write_log(
                f"Traitement de l'élément : {key} avec ID : {id} et valeur : {value_to_fill}.",
                self.log_file,
                "DEBUG",
            )
            waiter_to_use = waiter or self.waiter
            self._insert_value_with_retries(
                driver, id, value_to_fill, max_attempts, waiter_to_use
            )
