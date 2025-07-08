from __future__ import annotations

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from sele_saisie_auto import messages
from sele_saisie_auto.constants import JOURS_SEMAINE
from sele_saisie_auto.elements.element_id_builder import ElementIdBuilder
from sele_saisie_auto.logging_service import Logger

from . import get_default_logger

# pragma: no cover





class DuplicateDayDetector:
    """Detect if a weekday is filled on multiple lines of the time sheet."""

    def __init__(self, logger: Logger | None = None) -> None:
        self.logger = logger or get_default_logger()

    @staticmethod
    def _determine_row_range(driver, max_rows: int | None):
        if max_rows is None:
            row_elements = driver.find_elements(By.CSS_SELECTOR, "[id^='POL_DESCR$']")
            return range(len(row_elements))
        return range(max_rows)

    @staticmethod
    def _update_tracker(
        tracker: dict[str, list[str]], day_counter: int, description: str
    ) -> None:
        day_name = JOURS_SEMAINE[day_counter]
        tracker.setdefault(day_name, []).append(description)

    def detect(self, driver, max_rows: int | None = None) -> None:
        """Log duplicate days across description lines."""
        filled_days: dict[str, list[str]] = {}
        row_range = self._determine_row_range(driver, max_rows)

        for row_index in row_range:
            try:
                current_line_description = driver.find_element(
                    By.ID, f"POL_DESCR${row_index}"
                )
            except NoSuchElementException:
                if max_rows is None:  # pragma: no cover - rare branch
                    self.logger.debug(
                        f"Fin de l'analyse des lignes à l'index {row_index}"
                    )
                    break
                continue  # pragma: no cover - rare branch

            description = current_line_description.text.strip()
            self.logger.debug(
                f"Analyse de la ligne '{description}' à l'index {row_index}"
            )

            for day_counter in range(1, 8):
                day_input_id = ElementIdBuilder.build_day_input_id(
                    "POL_TIME", day_counter, row_index
                )
                try:
                    day_field = driver.find_element(By.ID, day_input_id)
                    day_content = day_field.get_attribute("value")
                    if day_content.strip():
                        self._update_tracker(filled_days, day_counter, description)
                except NoSuchElementException:  # pragma: no cover - best effort
                    self.logger.warning(
                        f"{messages.IMPOSSIBLE_DE_TROUVER} l'élément pour le jour '{JOURS_SEMAINE[day_counter]}' avec l'ID '{day_input_id}'"
                    )

        for day_name, lines in filled_days.items():
            if len(lines) > 1:
                self.logger.warning(
                    f"Doublon détecté pour le jour '{day_name}' dans les lignes : {', '.join(lines)}"
                )
            else:
                self.logger.debug(f"Aucun doublon détecté pour le jour '{day_name}'")
