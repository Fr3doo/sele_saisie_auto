from __future__ import annotations

from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By

from sele_saisie_auto import messages
from sele_saisie_auto.constants import JOURS_SEMAINE
from sele_saisie_auto.logger_utils import write_log
from sele_saisie_auto.selenium_utils import (
    Waiter,
    remplir_champ_texte,
    selectionner_option_menu_deroulant_type_select,
    trouver_ligne_par_description,
    verifier_champ_jour_rempli,
    wait_for_element,
)
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT

# remplir_informations_supp_france.py

if TYPE_CHECKING:  # pragma: no cover
    from sele_saisie_auto.automation.additional_info_page import AdditionalInfoPage

# ------------------------------------------------------------------------------------------- #
# ----------------------------------- CONSTANTE --------------------------------------------- #
# ------------------------------------------------------------------------------------------- #
LOG_FILE: str | None = None


def set_log_file(log_file: str) -> None:
    """Inject log file path for the module."""
    global LOG_FILE
    LOG_FILE = log_file


# ------------------------------------------------------------------------------------------- #
# ----------------------------------- FONCTIONS --------------------------------------------- #
# ------------------------------------------------------------------------------------------- #


def _build_input_id(id_value_jours: str, idx: int, row_index: int) -> str:
    if "UC_TIME_LIN_WRK_UC_DAILYREST" in id_value_jours:
        return f"{id_value_jours}{10 + idx}$0"
    return f"{id_value_jours}{idx}${row_index}"


def _get_element(driver, waiter: Waiter | None, input_id: str):
    if waiter:
        return waiter.wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)
    return wait_for_element(driver, By.ID, input_id, timeout=DEFAULT_TIMEOUT)


def _collect_filled_days(driver, waiter, id_value_jours, row_index, jours_semaine):
    jours_remplis = []
    write_log("🔍 Vérification des jours déjà remplis...", LOG_FILE, "DEBUG")
    for i in range(1, 8):
        input_id = _build_input_id(id_value_jours, i, row_index)
        element = _get_element(driver, waiter, input_id)
        if element:
            jour = jours_semaine[i]
            write_log(
                f"👉 Vérification du jour : {jour} (ID: {input_id})", LOG_FILE, "DEBUG"
            )
            if verifier_champ_jour_rempli(element, jour):
                jours_remplis.append(jour)
                write_log(f"✅ Jour '{jour}' déjà rempli.", LOG_FILE, "DEBUG")
            else:
                write_log(f"❌ Jour '{jour}' vide.", LOG_FILE, "DEBUG")
        else:
            write_log(
                f"❌ Élément non trouvé pour l'ID : {input_id}", LOG_FILE, "DEBUG"
            )
    return jours_remplis


def _fill_missing_days(
    driver,
    waiter,
    id_value_jours,
    row_index,
    jours_semaine,
    jours_remplis,
    valeurs_a_remplir,
    type_element,
):
    for i in range(1, 8):
        input_id = _build_input_id(id_value_jours, i, row_index)
        element = _get_element(driver, waiter, input_id)
        if element:
            jour = jours_semaine[i]
            if jour not in jours_remplis:
                valeur_a_remplir = valeurs_a_remplir.get(jour)
                if valeur_a_remplir:
                    write_log(
                        f"✏️ {messages.REMPLISSAGE} de '{jour}' avec la valeur '{valeur_a_remplir}'.",
                        LOG_FILE,
                        "DEBUG",
                    )
                    if type_element == "select":
                        selectionner_option_menu_deroulant_type_select(
                            element, valeur_a_remplir
                        )
                    elif type_element == "input":
                        remplir_champ_texte(element, jour, valeur_a_remplir)
                else:
                    write_log(
                        f"⚠️ {messages.AUCUNE_VALEUR} définie pour le jour '{jour}' dans 'valeurs_a_remplir'.",
                        LOG_FILE,
                        "DEBUG",
                    )
            else:
                write_log(
                    f"🔄 Jour '{jour}' déjà rempli, aucun changement.",
                    LOG_FILE,
                    "DEBUG",
                )
        else:
            write_log(
                f"❌ {messages.IMPOSSIBLE_DE_TROUVER} l'élément pour l'ID : {input_id}",
                LOG_FILE,
                "DEBUG",
            )


def traiter_description(driver, config, waiter: Waiter | None = None):
    """
    Traite une description en fonction d'une configuration donnée.

    Args:
        driver (webdriver): Instance du navigateur Selenium.
        config (dict): Configuration contenant toutes les informations nécessaires.
            - "description_cible" : Description à rechercher.
            - "id_value_ligne" : Préfixe des IDs pour identifier les lignes.
            - "id_value_jours" : Préfixe des IDs pour manipuler les jours.
            - "type_element" : Type des éléments à manipuler ("select" ou "input").
            - "valeurs_a_remplir" : Dictionnaire contenant les valeurs à remplir par jour.
    """
    description_cible = config["description_cible"]
    id_value_ligne = config["id_value_ligne"]  # Pour trouver la ligne
    id_value_jours = config["id_value_jours"]  # Pour les jours de la semaine
    type_element = config["type_element"]
    valeurs_a_remplir = config["valeurs_a_remplir"]
    jours_semaine = JOURS_SEMAINE

    write_log(
        f"🔍 Début du traitement pour la description : '{description_cible}'",
        LOG_FILE,
        "DEBUG",
    )
    row_index = trouver_ligne_par_description(driver, description_cible, id_value_ligne)
    if row_index is None:
        write_log(
            f"❌ Description '{description_cible}' non trouvée avec l'id_value '{id_value_ligne}'.",
            LOG_FILE,
            "DEBUG",
        )
        return
    write_log(
        f"✅ Description '{description_cible}' trouvée à l'index {row_index}.",
        LOG_FILE,
        "DEBUG",
    )

    jours_remplis = _collect_filled_days(
        driver, waiter, id_value_jours, row_index, jours_semaine
    )
    write_log(
        f"✍️ Remplissage des jours vides pour '{description_cible}'.",
        LOG_FILE,
        "DEBUG",
    )
    _fill_missing_days(
        driver,
        waiter,
        id_value_jours,
        row_index,
        jours_semaine,
        jours_remplis,
        valeurs_a_remplir,
        type_element,
    )


class ExtraInfoHelper:
    """Facade class using ``traiter_description`` with a shared ``Waiter``."""

    def __init__(
        self,
        waiter: Waiter | None = None,
        page: "AdditionalInfoPage" | None = None,
    ) -> None:
        self.waiter = waiter or Waiter()
        self.page = page

    def set_page(self, page: "AdditionalInfoPage") -> None:
        self.page = page

    def traiter_description(self, driver, config):
        traiter_description(driver, config, waiter=self.waiter)

    # ------------------------------------------------------------------
    # Delegation to :class:`AdditionalInfoPage`
    # ------------------------------------------------------------------
    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        if not self.page:
            raise RuntimeError("AdditionalInfoPage not configured")
        return self.page.navigate_from_work_schedule_to_additional_information_page(
            driver
        )

    def submit_and_validate_additional_information(self, driver):
        if not self.page:
            raise RuntimeError("AdditionalInfoPage not configured")
        return self.page.submit_and_validate_additional_information(driver)
