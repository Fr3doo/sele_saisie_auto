# src\sele_saisie_auto\selenium_utils\navigation.py
"""Browser navigation helpers."""

from __future__ import annotations

import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from typing_extensions import Literal

from sele_saisie_auto.logging_service import Logger

from . import get_default_logger


def verifier_accessibilite_url(url: str, logger: Logger | None = None) -> bool:
    """Teste l'accessibilité d'une URL."""
    logger = logger or get_default_logger()
    try:
        response = requests.get(url, timeout=10, verify=True)
        if response.status_code == 200:
            logger.info(f"🔹 URL accessible, avec vérification SSL : {url}")
            return True
        logger.error(
            f"❌ URL inaccessible, avec vérification SSL - statut : {response.status_code}"
        )
        return False
    except requests.exceptions.SSLError as ssl_err:
        logger.error(f"❌ Erreur SSL détectée : {ssl_err}")
        try:
            response = requests.get(url, timeout=10, verify=False)  # nosec B501
            if response.status_code == 200:
                logger.warning(f"⚠️ URL accessible, sans vérification SSL : {url}")
                return True
        except Exception as e:  # noqa: BLE001
            logger.error(f"❌ URL inaccessible, sans vérification SSL : {e}")
            return False
        # Si la requête sans vérification SSL n’a pas renvoyé 200
        logger.error(
            f"❌ URL inaccessible, même sans vérification SSL - statut : {response.status_code}"
        )
        return False
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"❌ Erreur de connexion à l'URL : {conn_err}")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"❌ Délai d'attente dépassé pour l'URL : {url}")
        return False
    except requests.exceptions.RequestException as req_err:
        logger.error(f"❌ Erreur de connexion à l'URL : {req_err}")
        return False


def switch_to_frame_by_id(
    driver: webdriver.Edge, frame_id: str, logger: Logger | None = None
) -> bool:
    """Switch into a frame identified by its DOM id."""
    logger = logger or get_default_logger()
    driver.switch_to.frame(driver.find_element(By.ID, frame_id))
    logger.debug(f"Bascule dans l'iframe '{frame_id}' réussie.")
    return True


def ouvrir_navigateur_sur_ecran_principal(
    plein_ecran: bool = False,
    url: str = "https://www.example.com",
    headless: bool = False,
    no_sandbox: bool = False,
    logger: Logger | None = None,
) -> webdriver.Edge | None:
    """Open the Edge browser and navigate to the URL."""
    logger = logger or get_default_logger()
    edge_browser_options = EdgeOptions()

    if headless:
        edge_browser_options.add_argument("--headless")
    if no_sandbox:
        edge_browser_options.add_argument("--no-sandbox")

    if not verifier_accessibilite_url(url, logger=logger):
        return None

    try:
        browser_instance = webdriver.Edge(options=edge_browser_options)
        browser_instance.get(url)
        if plein_ecran:
            browser_instance.maximize_window()
        return browser_instance
    except WebDriverException as e:
        if "ERR_CONNECTION_CLOSED" in str(e):
            logger.error("❌ La connexion au serveur a été fermée.")
        else:
            logger.error(f"❌ Erreur WebDriver : {str(e)}")
        return None


def definir_taille_navigateur(
    navigateur: webdriver.Edge, largeur: int, hauteur: int, logger: Logger | None = None
) -> webdriver.Edge:
    """Set the browser window size."""
    logger = logger or get_default_logger()
    navigateur.set_window_size(largeur, hauteur)
    logger.debug(f"Taille du navigateur définie à {largeur}x{hauteur}")
    return navigateur
