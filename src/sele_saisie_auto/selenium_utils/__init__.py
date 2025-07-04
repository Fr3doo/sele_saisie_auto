"""Convenience exports for Selenium helper functions."""

# ruff: noqa: E402
# flake8: noqa: E402
import time

import requests  # type: ignore[import]
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait

from sele_saisie_auto.logger_utils import write_log

LOG_FILE: str | None = None


def set_log_file(log_file: str) -> None:
    """Inject log file path for helper modules."""
    global LOG_FILE
    LOG_FILE = log_file


DEFAULT_TIMEOUT = 10
LONG_TIMEOUT = 20

from .element_actions import (
    click_element_without_wait,
    controle_insertion,
    detecter_doublons_jours,
    detecter_et_verifier_contenu,
    effacer_et_entrer_valeur,
    modifier_date_input,
    remplir_champ_texte,
    selectionner_option_menu_deroulant_type_select,
    send_keys_to_element,
    switch_to_default_content,
    switch_to_iframe_by_id_or_name,
    trouver_ligne_par_description,
    verifier_champ_jour_rempli,
)
from .navigation import (
    definir_taille_navigateur,
    ouvrir_navigateur_sur_ecran_principal,
    switch_to_frame_by_id,
    verifier_accessibilite_url,
)
from .wait_helpers import (
    Waiter,
    find_clickable,
    find_present,
    find_visible,
    is_document_complete,
    wait_for_dom_after,
    wait_for_dom_ready,
    wait_for_element,
    wait_until_dom_is_stable,
)

__all__ = [
    "set_log_file",
    "LOG_FILE",
    "DEFAULT_TIMEOUT",
    "LONG_TIMEOUT",
    "is_document_complete",
    "wait_for_dom_ready",
    "wait_until_dom_is_stable",
    "wait_for_dom_after",
    "wait_for_element",
    "find_clickable",
    "find_visible",
    "find_present",
    "Waiter",
    "modifier_date_input",
    "switch_to_frame_by_id",
    "switch_to_iframe_by_id_or_name",
    "switch_to_default_content",
    "click_element_without_wait",
    "send_keys_to_element",
    "verifier_champ_jour_rempli",
    "remplir_champ_texte",
    "detecter_et_verifier_contenu",
    "effacer_et_entrer_valeur",
    "controle_insertion",
    "selectionner_option_menu_deroulant_type_select",
    "trouver_ligne_par_description",
    "detecter_doublons_jours",
    "verifier_accessibilite_url",
    "ouvrir_navigateur_sur_ecran_principal",
    "definir_taille_navigateur",
    "write_log",
    "time",
    "requests",
    "webdriver",
    "WebDriverWait",
    "ec",
    "Select",
    "NoSuchElementException",
    "StaleElementReferenceException",
    "WebDriverException",
]
