# src\sele_saisie_auto\selenium_utils\duplicate_day_detector.py
"""Detect duplicate days in time sheet entries."""
from __future__ import annotations

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto import messages
from sele_saisie_auto.constants import JOURS_SEMAINE
from sele_saisie_auto.elements.element_id_builder import ElementIdBuilder
from sele_saisie_auto.logging_service import Logger

from . import get_default_logger


class DuplicateDayDetector:
    """Detect if a weekday is filled on multiple lines of the time sheet."""

    def __init__(self, logger: Logger | None = None) -> None:
        self.logger = logger or get_default_logger()

    @staticmethod
    def _update_tracker(
        tracker: dict[str, list[str]], day_counter: int, description: str
    ) -> None:
        day_name = JOURS_SEMAINE[day_counter]
        tracker.setdefault(day_name, []).append(description)

    def _iter_row_descriptions(self, driver: WebDriver, max_rows: int | None):
        """Yield (row_index, description) for each description row."""
        row_elements = driver.find_elements(By.CSS_SELECTOR, "[id^='POL_DESCR$']")
        if max_rows is not None:
            row_elements = row_elements[:max_rows]

        self.logger.debug(f"{len(row_elements)} ligne(s) de description détectée(s).")

        for index in range(len(row_elements)):
            try:
                elem = driver.find_element(By.ID, f"POL_DESCR${index}")
            except NoSuchElementException:
                if max_rows is None:
                    self.logger.debug(f"Fin de l'analyse des lignes à l'index {index}")
                    break
                continue
            description = (elem.text or "").strip()
            self.logger.debug(f"Analyse de la ligne '{description}' à l'index {index}")
            yield index, description

    def _is_day_filled(
        self, driver: WebDriver, row_index: int, day_counter: int
    ) -> bool:
        """Return True if the cell for (row_index, day_counter) is non-empty."""
        day_input_id = ElementIdBuilder.build_day_input_id(
            "POL_TIME", day_counter, row_index
        )
        try:
            day_field = driver.find_element(By.ID, day_input_id)
        except NoSuchElementException:
            self.logger.warning(
                f"{messages.IMPOSSIBLE_DE_TROUVER} l'élément pour le jour "
                f"'{JOURS_SEMAINE[day_counter]}' avec l'ID '{day_input_id}'"
            )
            return False

        value: str | None = day_field.get_attribute("value")
        return bool(value and value.strip())

    def _report_duplicates(self, filled_days: dict[str, list[str]]) -> None:
        for day_name, lines in filled_days.items():
            if len(lines) > 1:
                self.logger.warning(
                    f"Doublon détecté pour le jour '{day_name}' dans les lignes : "
                    f"{', '.join(lines)}"
                )
            else:
                self.logger.debug(f"Aucun doublon détecté pour le jour '{day_name}'")

    def detect(self, driver: WebDriver, max_rows: int | None = None) -> None:
        """Log duplicate days across description lines."""
        filled_days: dict[str, list[str]] = {}

        for row_index, description in self._iter_row_descriptions(driver, max_rows):
            self.logger.debug(
                f"Analyse de la ligne '{description}' à l'index {row_index}"
            )
            for day_counter in range(1, 8):
                if self._is_day_filled(driver, row_index, day_counter):
                    self._update_tracker(filled_days, day_counter, description)

        self._report_duplicates(filled_days)
