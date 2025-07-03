"""Utility functions for manipulating web elements."""

from __future__ import annotations

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from sele_saisie_auto.constants import JOURS_SEMAINE

from . import LOG_FILE, write_log


def modifier_date_input(date_field, new_date, update_message):
    """Change the value of a date input field and log the update."""
    date_field.clear()
    date_field.send_keys(new_date)
    write_log(f"{update_message} : {new_date}", LOG_FILE, "DEBUG")


def switch_to_iframe_by_id_or_name(driver, iframe_identifier):
    """Switch into the iframe identified by id or name."""
    driver.switch_to.frame(driver.find_element(By.ID, iframe_identifier))
    write_log(
        f"Bascule dans l'iframe '{iframe_identifier}' réussie.", LOG_FILE, "DEBUG"
    )
    return True


def switch_to_default_content(driver):
    """Return to the main document context."""
    driver.switch_to.default_content()
    write_log("Retour au contexte principal.", LOG_FILE, "DEBUG")


def click_element_without_wait(driver, by, locator_value):
    """Click an element directly without waiting."""
    target_element = driver.find_element(by, locator_value)
    target_element.click()
    write_log(f"Élément {by}='{locator_value}' cliqué avec succès.", LOG_FILE, "DEBUG")


def send_keys_to_element(driver, by, locator_value, input_text):
    """Send keys to a located element."""
    target_element = driver.find_element(by, locator_value)
    target_element.send_keys(input_text)


def verifier_champ_jour_rempli(day_field, day_label):
    """Check if a day's field already contains a value."""
    field_content = day_field.get_attribute("value")

    if field_content.strip():
        write_log(
            f"Jour '{day_label}' contient une valeur : {field_content}",
            LOG_FILE,
            "DEBUG",
        )
        return day_label

    write_log(f"Jour '{day_label}' est vide", LOG_FILE, "DEBUG")
    return None


def remplir_champ_texte(day_input_field, day_label, input_value):
    """Fill a day's input if empty."""
    current_content = day_input_field.get_attribute("value")

    if not current_content.strip():
        day_input_field.clear()
        day_input_field.send_keys(input_value)
        write_log(
            f"Valeur '{input_value}' insérée dans le jour '{day_label}'",
            LOG_FILE,
            "DEBUG",
        )
    else:
        write_log(
            f"Le jour '{day_label}' contient déjà une valeur : {current_content}, rien à changer.",
            LOG_FILE,
            "DEBUG",
        )


def detecter_et_verifier_contenu(driver, element_id, input_value):
    """Return element and whether its current value matches input_value."""
    try:
        day_input_field = driver.find_element(By.ID, element_id)
        current_content = day_input_field.get_attribute("value").strip()
        is_correct_value = current_content == input_value
        write_log(
            f"id trouvé : {element_id} / is_correct_value : {is_correct_value}",
            LOG_FILE,
            "DEBUG",
        )
        return day_input_field, is_correct_value
    except NoSuchElementException as e:
        write_log(
            f"❌ Élément avec id='{element_id}' introuvable. {str(e)}",
            LOG_FILE,
            "ERROR",
        )
        raise
    except StaleElementReferenceException as e:
        write_log(
            f"❌ Référence obsolète pour l'élément id='{element_id}'. {str(e)}",
            LOG_FILE,
            "ERROR",
        )
        raise
    except Exception as e:  # noqa: BLE001
        write_log(
            f"❌ Erreur inattendue lors de la détection et de la vérification du contenu : {str(e)}",
            LOG_FILE,
            "ERROR",
        )
        raise


def effacer_et_entrer_valeur(day_input_field, input_value):
    """Clear the field then enter the provided value."""
    day_input_field.clear()
    day_input_field.send_keys(input_value)
    write_log(
        f"Valeur '{input_value}' insérée dans le champ avec succès.", LOG_FILE, "DEBUG"
    )


def controle_insertion(day_input_field, input_value):
    """Check that the field now contains the expected value."""
    return day_input_field.get_attribute("value").strip() == input_value


def selectionner_option_menu_deroulant_type_select(dropdown_field, visible_text):
    try:
        select = Select(dropdown_field)
        select.select_by_visible_text(visible_text)
        write_log(f"Valeur '{visible_text}' sélectionnée.", LOG_FILE, "DEBUG")
    except Exception as e:  # noqa: BLE001
        write_log(
            f"❌ Erreur lors de la sélection de la valeur '{visible_text}' : {str(e)}",
            LOG_FILE,
            "ERROR",
        )


def trouver_ligne_par_description(
    driver, target_description, row_prefix, partial_match=False
):
    """Return the row index matching a description or None."""
    matched_row_index = None
    row_counter = 0

    while True:
        try:
            current_description_element = driver.find_element(
                By.ID, f"{row_prefix}{row_counter}"
            )
            raw_text = current_description_element.text.strip()
            cleaned_text = " ".join(raw_text.split())

            if partial_match:
                if target_description in cleaned_text:
                    write_log(
                        f"Ligne trouvée (correspondance partielle) pour '{target_description}' à l'index {row_counter}",
                        LOG_FILE,
                        "DEBUG",
                    )
                    matched_row_index = row_counter
                    break
            else:
                if cleaned_text == target_description:
                    write_log(
                        f"Ligne trouvée pour '{target_description}' à l'index {row_counter}",
                        LOG_FILE,
                        "DEBUG",
                    )
                    matched_row_index = row_counter
                    break
            row_counter += 1
        except NoSuchElementException:
            write_log(
                f"Aucune ligne trouvée pour '{target_description}'.",
                LOG_FILE,
                "WARNING",
            )
            break
    return matched_row_index


def detecter_doublons_jours(driver):
    """Check if any day appears more than once across lines."""
    filled_days_tracker = {}
    row_index = 0
    while True:
        try:
            current_line_description = driver.find_element(
                By.ID, f"POL_DESCR${row_index}"
            )
            line_description = current_line_description.text.strip()
            write_log(
                f"Analyse de la ligne '{line_description}' à l'index {row_index}",
                LOG_FILE,
                "DEBUG",
            )

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
                    write_log(
                        f"Impossible de trouver l'élément pour le jour '{JOURS_SEMAINE[day_counter]}' avec l'ID '{day_input_id}'",
                        LOG_FILE,
                        "WARNING",
                    )

            row_index += 1
        except NoSuchElementException:
            write_log(
                f"Fin de l'analyse des lignes à l'index {row_index}", LOG_FILE, "DEBUG"
            )
            break

    for day_name, lines in filled_days_tracker.items():
        if len(lines) > 1:
            write_log(
                f"Doublon détecté pour le jour '{day_name}' dans les lignes : {', '.join(lines)}",
                LOG_FILE,
                "WARNING",
            )
        else:
            write_log(
                f"Aucun doublon détecté pour le jour '{day_name}'", LOG_FILE, "DEBUG"
            )
