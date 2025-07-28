# src\sele_saisie_auto\selenium_utils\element_actions.py
"""Utility functions for manipulating web elements."""

from __future__ import annotations

from typing import cast

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.webdriver import WebDriver as EdgeWebDriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select

from sele_saisie_auto import messages
from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.selenium_utils.duplicate_day_detector import DuplicateDayDetector

from . import get_default_logger
from .navigation import switch_to_frame_by_id


def modifier_date_input(
    date_field: WebElement,
    new_date: str,
    update_message: str,
    logger: Logger | None = None,
) -> None:
    """Change the value of a date input field and log the update."""
    logger = logger or get_default_logger()
    date_field.clear()
    date_field.send_keys(new_date)
    logger.debug(f"{update_message} : {new_date}")


def switch_to_iframe_by_id_or_name(
    driver: WebDriver, iframe_identifier: str, logger: Logger | None = None
) -> None:
    """Switch into the iframe identified by id or name."""
    logger = logger or get_default_logger()
    switch_to_frame_by_id(cast(EdgeWebDriver, driver), iframe_identifier, logger=logger)


def switch_to_default_content(driver: WebDriver, logger: Logger | None = None) -> None:
    """Return to the main document context."""
    logger = logger or get_default_logger()
    driver.switch_to.default_content()
    logger.debug("Retour au contexte principal.")


def click_element_without_wait(
    driver: WebDriver, by: By, locator_value: str, logger: Logger | None = None
) -> None:
    """Click an element directly without waiting."""
    logger = logger or get_default_logger()
    target_element = driver.find_element(by, locator_value)
    target_element.click()
    logger.debug(f"Élément {by}='{locator_value}' cliqué avec succès.")


def send_keys_to_element(
    driver: WebDriver,
    by: By,
    locator_value: str,
    input_text: str,
    logger: Logger | None = None,
) -> None:
    """Send keys to a located element."""
    logger = logger or get_default_logger()
    target_element = driver.find_element(by, locator_value)
    target_element.send_keys(input_text)


def verifier_champ_jour_rempli(
    day_field: WebElement, day_label: str, logger: Logger | None = None
) -> str | None:
    """Check if a day's field already contains a value."""
    logger = logger or get_default_logger()
    field_content: str | None = day_field.get_attribute("value")
    # On vérifie que l’attribut existe et n’est pas vide après strip
    if field_content and field_content.strip():
        logger.debug(f"Jour '{day_label}' contient une valeur : {field_content}")
        return day_label

    logger.debug(f"Jour '{day_label}' est vide")
    return None


def remplir_champ_texte(
    day_input_field: WebElement,
    day_label: str,
    input_value: str,
    logger: Logger | None = None,
) -> None:
    """Fill a day's input if empty."""
    logger = logger or get_default_logger()
    current_content: str | None = day_input_field.get_attribute("value")

    if current_content is None or not current_content.strip():
        day_input_field.clear()
        day_input_field.send_keys(input_value)
        logger.debug(f"Valeur '{input_value}' insérée dans le jour '{day_label}'")
    else:
        logger.debug(
            f"Le jour '{day_label}' contient déjà une valeur : {current_content}, rien à changer."
        )


def detecter_et_verifier_contenu(
    driver: WebDriver, element_id: str, input_value: str, logger: Logger | None = None
) -> tuple[WebElement | None, bool]:
    """Return element and whether its current value matches input_value."""
    logger = logger or get_default_logger()
    try:
        day_input_field = driver.find_element(By.ID, element_id)
        raw_content: str | None = day_input_field.get_attribute("value")
        current_content = raw_content.strip() if raw_content else ""
        is_correct_value = current_content == input_value
        logger.debug(
            f"id trouvé : {element_id} / is_correct_value : {is_correct_value}"
        )
        return day_input_field, is_correct_value
    except NoSuchElementException as e:
        logger.error(
            f"❌ Élément avec id='{element_id}' {messages.INTROUVABLE}. {str(e)}"
        )
        raise
    except StaleElementReferenceException as e:
        logger.error(
            f"❌ {messages.REFERENCE_OBSOLETE} pour l'élément id='{element_id}'. {str(e)}"
        )
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(
            f"❌ {messages.ERREUR_INATTENDUE} lors de la détection et de la vérification du contenu : {str(e)}"
        )
        raise RuntimeError(
            f"{messages.ERREUR_INATTENDUE} lors de la détection et de la vérification du contenu"
        ) from e


def effacer_et_entrer_valeur(
    day_input_field: WebElement, input_value: str, logger: Logger | None = None
) -> None:
    """Clear the field then enter the provided value."""
    logger = logger or get_default_logger()
    day_input_field.clear()
    day_input_field.send_keys(input_value)
    logger.debug(f"Valeur '{input_value}' insérée dans le champ avec succès.")


def controle_insertion(day_input_field: WebElement, input_value: str) -> bool:
    """Check that the field now contains the expected value."""
    value: str | None = day_input_field.get_attribute("value")
    return value is not None and value.strip() == input_value


def select_by_text(
    element: WebElement, text: str, logger: Logger | None = None
) -> None:
    """Select ``text`` from a Selenium ``Select`` element."""
    logger = logger or get_default_logger()
    try:
        selector = Select(element)
        selector.select_by_visible_text(text)
        logger.debug(f"Valeur '{text}' sélectionnée.")
    except Exception as e:  # noqa: BLE001
        logger.error(f"❌ Erreur lors de la sélection de la valeur '{text}' : {str(e)}")


def selectionner_option_menu_deroulant_type_select(
    dropdown_field: WebElement, visible_text: str, logger: Logger | None = None
) -> None:
    """Choisit ``visible_text`` dans un ``Select`` Selenium."""
    select_by_text(dropdown_field, visible_text, logger=logger)


def trouver_ligne_par_description(
    driver: WebDriver,
    target_description: str,
    row_prefix: str,
    partial_match: bool = False,
    logger: Logger | None = None,
    max_rows: int | None = None,
) -> int | None:
    """Return the row index matching a description or None."""
    logger = logger or get_default_logger()
    matched_row_index = None

    if max_rows is None:
        row_elements = driver.find_elements(By.CSS_SELECTOR, f"[id^='{row_prefix}']")
        row_range = range(len(row_elements))
    else:
        row_range = range(max_rows)

    for row_counter in row_range:
        try:
            current_description_element = driver.find_element(
                By.ID, f"{row_prefix}{row_counter}"
            )
        except NoSuchElementException:
            if max_rows is None:
                logger.warning(f"Aucune ligne trouvée pour '{target_description}'.")
                break
            continue

        raw_text = current_description_element.text.strip()
        cleaned_text = " ".join(raw_text.split())

        if partial_match:
            if target_description in cleaned_text:
                logger.debug(
                    f"Ligne trouvée (correspondance partielle) pour '{target_description}' à l'index {row_counter}"
                )
                matched_row_index = row_counter
                break
        else:
            if cleaned_text == target_description:
                logger.debug(
                    f"Ligne trouvée pour '{target_description}' à l'index {row_counter}"
                )
                matched_row_index = row_counter
                break
    return matched_row_index


def detecter_doublons_jours(
    driver: WebDriver, logger: Logger | None = None, max_rows: int | None = None
) -> None:
    """Check if any day appears more than once across lines."""
    detector = DuplicateDayDetector(logger=logger)
    detector.detect(driver, max_rows=max_rows)
