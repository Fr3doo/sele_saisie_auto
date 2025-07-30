# src\sele_saisie_auto\form_processing\description_processor.py
"""Processing helpers for descriptions and weekly day values."""

from __future__ import annotations

from typing import Any

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto import messages
from sele_saisie_auto.constants import JOURS_SEMAINE
from sele_saisie_auto.elements.element_id_builder import ElementIdBuilder
from sele_saisie_auto.logger_utils import write_log
from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.selenium_utils import (
    Waiter,
    remplir_champ_texte,
    select_by_text,
    trouver_ligne_par_description,
    verifier_champ_jour_rempli,
    wait_for_element,
)
from sele_saisie_auto.strategies import ElementFillingContext


def _get_element(
    driver: WebDriver, waiter: Waiter | None, element_id: str
) -> Any | None:
    """Retrieve a Selenium element either via :class:`Waiter` or default wait."""
    if waiter:
        return waiter.wait_for_element(driver, By.ID, element_id)
    return wait_for_element(driver, By.ID, element_id)


def _find_description_row(
    driver: WebDriver, description: str, id_value_row: str, log_file: str
) -> int | None:
    """Return the row index matching ``description`` and log the search result."""
    write_log(
        messages.DESCRIPTION_PROCESS_START.format(description=description),
        log_file,
        "DEBUG",
    )
    row_index = trouver_ligne_par_description(driver, description, id_value_row)
    if row_index is None:
        write_log(
            messages.DESCRIPTION_NOT_FOUND.format(
                description=description, id_value=id_value_row
            ),
            log_file,
            "DEBUG",
        )
    else:
        write_log(
            messages.DESCRIPTION_FOUND.format(description=description, index=row_index),
            log_file,
            "DEBUG",
        )
    return row_index


def _collect_filled_days(
    driver: WebDriver,
    waiter: Waiter | None,
    id_value_days: str,
    row_index: int,
    log_file: str,
    week_days: dict[int, str] | None = None,
) -> list[str]:
    """Return a list of already filled days for ``row_index``."""
    filled_days: list[str] = []
    week_days = week_days or JOURS_SEMAINE
    write_log(messages.CHECK_FILLED_DAYS, log_file, "DEBUG")
    for day_index in range(1, 8):
        input_id = ElementIdBuilder.build_day_input_id(
            id_value_days, day_index, row_index
        )
        element = _get_element(driver, waiter, input_id)
        if not element:
            write_log(
                messages.ELEMENT_NOT_FOUND_ID.format(id=input_id), log_file, "DEBUG"
            )
            continue

        day_name = week_days[day_index]
        write_log(
            messages.DAY_CHECK.format(jour=day_name, id=input_id),
            log_file,
            "DEBUG",
        )
        if verifier_champ_jour_rempli(element, day_name):
            filled_days.append(day_name)
            write_log(
                messages.DAY_ALREADY_FILLED.format(jour=day_name),
                log_file,
                "DEBUG",
            )
        else:
            write_log(
                messages.DAY_EMPTY.format(jour=day_name),
                log_file,
                "DEBUG",
            )
    return filled_days


def _fill_days(
    driver: WebDriver,
    waiter: Waiter | None,
    id_value_days: str,
    row_index: int,
    values_to_fill: dict[str, str],
    filled_days: list[str],
    type_element: str,
    log_file: str,
    week_days: dict[int, str] | None = None,
    filling_context: ElementFillingContext | None = None,
    logger: Logger | None = None,
) -> None:
    """Fill remaining empty days for the row."""
    week_days = week_days or JOURS_SEMAINE
    for day_index in range(1, 8):
        input_id = ElementIdBuilder.build_day_input_id(
            id_value_days, day_index, row_index
        )
        element = _get_element(driver, waiter, input_id)
        if not element:
            write_log(
                messages.ELEMENT_NOT_FOUND_ID.format(id=input_id), log_file, "DEBUG"
            )
            continue

        day_name = week_days[day_index]
        if day_name in filled_days:
            write_log(
                messages.DAY_ALREADY_FILLED_NO_CHANGE.format(jour=day_name),
                log_file,
                "DEBUG",
            )
            continue

        value = values_to_fill.get(day_name)
        if not value:
            write_log(
                f"⚠️ {messages.AUCUNE_VALEUR} définie pour le jour '{day_name}' dans 'valeurs_a_remplir'.",
                log_file,
                "DEBUG",
            )
            continue

        write_log(
            f"✏️ {messages.REMPLISSAGE} de '{day_name}' avec la valeur '{value}'.",
            log_file,
            "DEBUG",
        )
        if filling_context is not None:
            filling_context.fill(element, value, logger)
        else:
            if type_element == "select":
                select_by_text(element, value)
            elif type_element == "input":
                remplir_champ_texte(element, day_name, value)


def process_description(
    driver: WebDriver,
    config: dict[str, Any],
    log_file: str,
    waiter: Waiter | None = None,
    *,
    filling_context: ElementFillingContext | None = None,
    logger: Logger | None = None,
) -> None:
    """High level helper orchestrating description processing."""
    description = config["description_cible"]
    id_value_row = config["id_value_ligne"]
    id_value_days = config["id_value_jours"]
    type_element = config["type_element"]
    values_to_fill = config["valeurs_a_remplir"]

    row_index = _find_description_row(driver, description, id_value_row, log_file)
    if row_index is None:
        return

    filled_days = _collect_filled_days(
        driver, waiter, id_value_days, row_index, log_file
    )

    write_log(
        messages.FILL_EMPTY_DAYS.format(description=description), log_file, "DEBUG"
    )

    _fill_days(
        driver,
        waiter,
        id_value_days,
        row_index,
        values_to_fill,
        filled_days,
        type_element,
        log_file,
        filling_context=filling_context,
        logger=logger,
    )
