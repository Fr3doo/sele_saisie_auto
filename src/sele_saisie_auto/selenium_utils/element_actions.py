"""Utility functions for manipulating web elements."""

from __future__ import annotations

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from sele_saisie_auto import messages
from sele_saisie_auto.constants import JOURS_SEMAINE
from sele_saisie_auto.logging_service import Logger

from . import get_default_logger
from .navigation import switch_to_frame_by_id


def modifier_date_input(
    date_field, new_date, update_message, logger: Logger | None = None
):
    """Change the value of a date input field and log the update."""
    logger = logger or get_default_logger()
    date_field.clear()
    date_field.send_keys(new_date)
    logger.debug(f"{update_message} : {new_date}")


def switch_to_iframe_by_id_or_name(
    driver, iframe_identifier, logger: Logger | None = None
):
    """Switch into the iframe identified by id or name."""
    logger = logger or get_default_logger()
    return switch_to_frame_by_id(driver, iframe_identifier, logger=logger)


def switch_to_default_content(driver, logger: Logger | None = None):
    """Return to the main document context."""
    logger = logger or get_default_logger()
    driver.switch_to.default_content()
    logger.debug("Retour au contexte principal.")


def click_element_without_wait(driver, by, locator_value, logger: Logger | None = None):
    """Click an element directly without waiting."""
    logger = logger or get_default_logger()
    target_element = driver.find_element(by, locator_value)
    target_element.click()
    logger.debug(f"Élément {by}='{locator_value}' cliqué avec succès.")


def send_keys_to_element(
    driver, by, locator_value, input_text, logger: Logger | None = None
):
    """Send keys to a located element."""
    logger = logger or get_default_logger()
    target_element = driver.find_element(by, locator_value)
    target_element.send_keys(input_text)


def verifier_champ_jour_rempli(day_field, day_label, logger: Logger | None = None):
    """Check if a day's field already contains a value."""
    logger = logger or get_default_logger()
    field_content = day_field.get_attribute("value")

    if field_content.strip():
        logger.debug(f"Jour '{day_label}' contient une valeur : {field_content}")
        return day_label

    logger.debug(f"Jour '{day_label}' est vide")
    return None


def remplir_champ_texte(
    day_input_field, day_label, input_value, logger: Logger | None = None
):
    """Fill a day's input if empty."""
    logger = logger or get_default_logger()
    current_content = day_input_field.get_attribute("value")

    if not current_content.strip():
        day_input_field.clear()
        day_input_field.send_keys(input_value)
        logger.debug(f"Valeur '{input_value}' insérée dans le jour '{day_label}'")
    else:
        logger.debug(
            f"Le jour '{day_label}' contient déjà une valeur : {current_content}, rien à changer."
        )


def detecter_et_verifier_contenu(
    driver, element_id, input_value, logger: Logger | None = None
):
    """Return element and whether its current value matches input_value."""
    logger = logger or get_default_logger()
    try:
        day_input_field = driver.find_element(By.ID, element_id)
        current_content = day_input_field.get_attribute("value").strip()
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
        raise


def effacer_et_entrer_valeur(
    day_input_field, input_value, logger: Logger | None = None
):
    """Clear the field then enter the provided value."""
    logger = logger or get_default_logger()
    day_input_field.clear()
    day_input_field.send_keys(input_value)
    logger.debug(f"Valeur '{input_value}' insérée dans le champ avec succès.")


def controle_insertion(day_input_field, input_value):
    """Check that the field now contains the expected value."""
    return day_input_field.get_attribute("value").strip() == input_value


def select_by_text(element, text, logger: Logger | None = None):
    """Select ``text`` from a Selenium ``Select`` element."""
    logger = logger or get_default_logger()
    try:
        selector = Select(element)
        selector.select_by_visible_text(text)
        logger.debug(f"Valeur '{text}' sélectionnée.")
    except Exception as e:  # noqa: BLE001
        logger.error(f"❌ Erreur lors de la sélection de la valeur '{text}' : {str(e)}")


def selectionner_option_menu_deroulant_type_select(
    dropdown_field, visible_text, logger: Logger | None = None
):
    """Choisit ``visible_text`` dans un ``Select`` Selenium."""
    select_by_text(dropdown_field, visible_text, logger=logger)


def trouver_ligne_par_description(
    driver,
    target_description,
    row_prefix,
    partial_match=False,
    logger: Logger | None = None,
    max_rows: int | None = None,
):
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
    driver, logger: Logger | None = None, max_rows: int | None = None
):
    """Check if any day appears more than once across lines."""
    logger = logger or get_default_logger()
    filled_days_tracker = {}
    if max_rows is None:
        row_elements = driver.find_elements(By.CSS_SELECTOR, "[id^='POL_DESCR$']")
        row_range = range(len(row_elements))
    else:
        row_range = range(max_rows)

    for row_index in row_range:
        try:
            current_line_description = driver.find_element(
                By.ID, f"POL_DESCR${row_index}"
            )
        except NoSuchElementException:
            if max_rows is None:
                logger.debug(f"Fin de l'analyse des lignes à l'index {row_index}")
                break
            continue

        line_description = current_line_description.text.strip()
        logger.debug(f"Analyse de la ligne '{line_description}' à l'index {row_index}")

        for day_counter in range(1, 8):
            day_input_id = f"POL_TIME{day_counter}${row_index}"
            try:
                day_field = driver.find_element(By.ID, day_input_id)
                day_content = day_field.get_attribute("value")

                if day_content.strip():
                    day_name = JOURS_SEMAINE[day_counter]
                    if day_name in filled_days_tracker:
                        filled_days_tracker[day_name].append(line_description)
                    else:
                        filled_days_tracker[day_name] = [line_description]
            except NoSuchElementException:
                logger.warning(
                    f"{messages.IMPOSSIBLE_DE_TROUVER} l'élément pour le jour '{JOURS_SEMAINE[day_counter]}' avec l'ID '{day_input_id}'"
                )

    for day_name, lines in filled_days_tracker.items():
        if len(lines) > 1:
            logger.warning(
                f"Doublon détecté pour le jour '{day_name}' dans les lignes : {', '.join(lines)}"
            )
        else:
            logger.debug(f"Aucun doublon détecté pour le jour '{day_name}'")
