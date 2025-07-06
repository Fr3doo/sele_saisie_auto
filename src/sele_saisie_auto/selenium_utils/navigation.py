"""Browser navigation helpers."""

from __future__ import annotations

import requests  # type: ignore[import]
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions

from sele_saisie_auto.logging_service import Logger

from . import get_default_logger


def verifier_accessibilite_url(url, logger: Logger | None = None):
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
    except requests.exceptions.RequestException as req_err:
        logger.error(f"❌ Erreur de connexion à l'URL : {req_err}")
        return False


def switch_to_frame_by_id(driver, frame_id, logger: Logger | None = None):
    """Switch into a frame identified by its DOM id."""
    logger = logger or get_default_logger()
    driver.switch_to.frame(driver.find_element(By.ID, frame_id))
    logger.debug(f"Bascule dans l'iframe '{frame_id}' réussie.")
    return True


def ouvrir_navigateur_sur_ecran_principal(
    plein_ecran=False,
    url="https://www.example.com",
    headless=False,
    no_sandbox=False,
    logger: Logger | None = None,
):
    """Open the Edge browser and navigate to the URL."""
    logger = logger or get_default_logger()
    edge_browser_options = EdgeOptions()
    edge_browser_options.use_chromium = True

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
    navigateur, largeur, hauteur, logger: Logger | None = None
):
    """Set the browser window size."""
    logger = logger or get_default_logger()
    navigateur.set_window_size(largeur, hauteur)
    logger.debug(f"Taille du navigateur définie à {largeur}x{hauteur}")
    return navigateur
