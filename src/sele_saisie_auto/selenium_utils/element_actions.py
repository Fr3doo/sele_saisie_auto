# src\sele_saisie_auto\selenium_utils\element_actions.py
"""Utility functions for manipulating web elements."""

from __future__ import annotations

from typing import Callable, Iterable, NoReturn, cast

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


def _normalize_text(text: str) -> str:
    """Nettoie les espaces multiples et supprime les espaces de début/fin."""
    return " ".join((text or "").split())


def _text_contains(target: str, text: str) -> bool:
    """Vérifie si ``target`` est contenu dans ``text``."""
    return target in text


def _text_equals(target: str, text: str) -> bool:
    """Vérifie si ``text`` est exactement égal à ``target``."""
    return text == target


def _parse_index_from_id(row_id: str, row_prefix: str) -> int | None:
    """Extrait l'indice numérique à partir d'un identifiant d'élément."""
    if not row_id.startswith(row_prefix):
        return None
    prefix_len = len(row_prefix)
    suffix = row_id[prefix_len:]
    try:
        return int(suffix)
    except ValueError:
        return None


def _iter_existing_rows(
    driver: WebDriver, row_prefix: str
) -> Iterable[tuple[int, WebElement]]:
    """Itère sur les lignes présentes dans le DOM."""
    elements = driver.find_elements(By.CSS_SELECTOR, f"[id^='{row_prefix}']")
    for i, el in enumerate(elements):
        idx, real_el = _extract_index_and_element(driver, row_prefix, i, el)
        if idx is not None and real_el is not None:
            yield idx, real_el


def _extract_index_and_element(
    driver: WebDriver, row_prefix: str, index: int, el: WebElement
) -> tuple[int | None, WebElement | None]:
    """Retourne l'indice et l'élément réel correspondant à ``el``."""
    get_attr = getattr(el, "get_attribute", None)
    if callable(get_attr):
        row_id = (get_attr("id") or "").strip()
        idx = _parse_index_from_id(row_id, row_prefix)
        if idx is not None:
            return idx, el
    try:
        real_el = driver.find_element(By.ID, f"{row_prefix}{index}")
    except NoSuchElementException:
        return None, None
    return index, real_el


def _iter_range_rows(
    driver: WebDriver, row_prefix: str, max_rows: int
) -> Iterable[tuple[int, WebElement]]:
    """Itère sur les indices de 0 à ``max_rows`` - 1."""
    for i in range(max_rows):
        try:
            el = driver.find_element(By.ID, f"{row_prefix}{i}")
        except NoSuchElementException:
            continue
        yield i, el


def _iter_rows(
    driver: WebDriver, row_prefix: str, max_rows: int | None
) -> Iterable[tuple[int, WebElement]]:
    """Sélectionne le mode d'itération selon ``max_rows``."""
    return (
        _iter_existing_rows(driver, row_prefix)
        if max_rows is None
        else _iter_range_rows(driver, row_prefix, max_rows)
    )


def _find_row(
    driver: WebDriver,
    row_prefix: str,
    max_rows: int | None,
    compare: Callable[[str, str], bool],
    target: str,
    log_msg: str,
    raw_target: str,
    logger: Logger,
) -> int | None:
    """Parcourt les lignes et renvoie l'index correspondant ou ``None``."""
    for idx, element in _iter_rows(driver, row_prefix, max_rows):
        cleaned = _normalize_text(element.text)
        if compare(target, cleaned):
            logger.debug(f"{log_msg} pour '{raw_target}' à l'index {idx}")
            return idx
    return None


def _handle_detection_error(e: Exception, element_id: str, logger: Logger) -> NoReturn:
    """Gère les erreurs pour ``detecter_et_verifier_contenu`` et relance l'exception adéquate."""
    if isinstance(e, NoSuchElementException):
        logger.error(
            f"❌ Élément avec id='{element_id}' {messages.INTROUVABLE}. {str(e)}"
        )
        raise
    if isinstance(e, StaleElementReferenceException):
        logger.error(
            f"❌ {messages.REFERENCE_OBSOLETE} pour l'élément id='{element_id}'. {str(e)}"
        )
        raise
    logger.error(
        f"❌ {messages.ERREUR_INATTENDUE} lors de la détection et de la vérification du contenu : {str(e)}"
    )
    raise RuntimeError(
        f"{messages.ERREUR_INATTENDUE} lors de la détection et de la vérification du contenu"
    ) from e


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
    field_content = (day_field.get_attribute("value") or "").strip()
    if field_content:
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
    current_content = (day_input_field.get_attribute("value") or "").strip()
    if current_content:
        logger.debug(
            f"Le jour '{day_label}' contient déjà une valeur : {current_content}, rien à changer."
        )
        return
    day_input_field.clear()
    day_input_field.send_keys(input_value)
    logger.debug(f"Valeur '{input_value}' insérée dans le jour '{day_label}'")


def detecter_et_verifier_contenu(
    driver: WebDriver, element_id: str, input_value: str, logger: Logger | None = None
) -> tuple[WebElement | None, bool]:
    """Return element and whether its current value matches input_value."""
    logger = logger or get_default_logger()
    try:
        day_input_field = driver.find_element(By.ID, element_id)
        raw_content = day_input_field.get_attribute("value")
        current_content = (raw_content or "").strip()
        is_correct_value = current_content == input_value
        logger.debug(
            f"id trouvé : {element_id} / is_correct_value : {is_correct_value}"
        )
        return day_input_field, is_correct_value
    except Exception as e:  # noqa: BLE001
        _handle_detection_error(e, element_id, logger)


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
    """Retourne l'index de la ligne correspondant à la description, ou ``None``."""
    logger = logger or get_default_logger()
    target = _normalize_text(target_description)

    if partial_match:
        compare = _text_contains
        log_msg = "Ligne trouvée (correspondance partielle)"
    else:
        compare = _text_equals
        log_msg = "Ligne trouvée"

    idx = _find_row(
        driver,
        row_prefix,
        max_rows,
        compare,
        target,
        log_msg,
        target_description,
        logger,
    )
    if idx is None and max_rows is None:
        logger.warning(f"Aucune ligne trouvée pour '{target_description}'.")
    return idx


def detecter_doublons_jours(
    driver: WebDriver, logger: Logger | None = None, max_rows: int | None = None
) -> None:
    """Check if any day appears more than once across lines."""
    detector = DuplicateDayDetector(logger=logger)
    detector.detect(driver, max_rows=max_rows)
