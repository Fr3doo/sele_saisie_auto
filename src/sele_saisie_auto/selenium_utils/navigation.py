"""Browser navigation helpers."""

from __future__ import annotations

from typing import Optional, Tuple

import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions

from sele_saisie_auto.logging_service import Logger

from . import get_default_logger

# Constantes pour éviter les "magic numbers"
_DEFAULT_TIMEOUT = 10


def _get_status(
    url: str, *, verify: bool, timeout: int = _DEFAULT_TIMEOUT
) -> Tuple[Optional[int], Optional[Exception]]:
    """Effectue une requête GET et renvoie (status_code, error)."""
    try:
        response = requests.get(url, timeout=timeout, verify=verify)
        return response.status_code, None
    except (
        requests.exceptions.RequestException
    ) as err:  # pragma: no cover - branches tested
        return None, err


def verifier_accessibilite_url(url: str, logger: Logger | None = None) -> bool:
    """Teste l'accessibilité d'une URL avec vérification SSL, puis fallback sans SSL en cas d'erreur SSL."""
    logger = logger or get_default_logger()

    status, err = _get_status(url, verify=True)
    if status == 200:
        logger.info(f"🔹 URL accessible, avec vérification SSL : {url}")
        return True

    if isinstance(err, requests.exceptions.SSLError):
        logger.error(f"❌ Erreur SSL détectée : {err}")
        return _check_url_without_ssl(url, logger)

    logger.error(f"❌ URL inaccessible (status={status}) : {err}")
    return False


def _check_url_without_ssl(url: str, logger: Logger) -> bool:
    """Second essai sans vérification SSL."""
    status, err = _get_status(url, verify=False)  # nosec B501
    if status == 200:
        logger.warning(f"⚠️ URL accessible, sans vérification SSL : {url}")
        return True
    logger.error(
        f"❌ URL inaccessible, sans vérification SSL (status={status}) : {err}"
    )
    return False


def switch_to_frame_by_id(
    driver: webdriver.Edge, frame_id: str, logger: Logger | None = None
) -> bool:
    """Switch into a frame identified by its DOM id."""
    logger = logger or get_default_logger()
    driver.switch_to.frame(driver.find_element(By.ID, frame_id))
    logger.debug(f"Bascule dans l'iframe '{frame_id}' réussie.")
    return True


def _build_edge_options(*, headless: bool, no_sandbox: bool) -> EdgeOptions:
    """Construit les options Edge de manière déclarative (réduit la complexité de la fonction appelante)."""
    opts = EdgeOptions()
    if headless:
        opts.add_argument("--headless")
    if no_sandbox:
        opts.add_argument("--no-sandbox")
    return opts


def _log_webdriver_exception(e: WebDriverException, logger: Logger) -> None:
    """Centralise le mapping message d’erreur WebDriver -> log."""
    msg = str(e)
    if "ERR_CONNECTION_CLOSED" in msg:
        logger.error("❌ La connexion au serveur a été fermée.")
    else:
        logger.error(f"❌ Erreur WebDriver : {msg}")


def ouvrir_navigateur_sur_ecran_principal(
    plein_ecran: bool = False,
    url: str = "https://www.example.com",
    headless: bool = False,
    no_sandbox: bool = False,
    logger: Logger | None = None,
) -> webdriver.Edge | None:
    """Open the Edge browser and navigate to the URL."""
    logger = logger or get_default_logger()
    options = _build_edge_options(headless=headless, no_sandbox=no_sandbox)

    if not verifier_accessibilite_url(url, logger=logger):
        return None

    try:
        return _start_browser(options, url, plein_ecran)
    except WebDriverException as e:
        _log_webdriver_exception(e, logger)
        return None


def definir_taille_navigateur(
    navigateur: webdriver.Edge, largeur: int, hauteur: int, logger: Logger | None = None
) -> webdriver.Edge:
    """Set the browser window size."""
    logger = logger or get_default_logger()
    navigateur.set_window_size(largeur, hauteur)
    logger.debug(f"Taille du navigateur définie à {largeur}x{hauteur}")
    return navigateur


def _start_browser(options: EdgeOptions, url: str, plein_ecran: bool) -> webdriver.Edge:
    """Lance le navigateur avec les options fournies."""
    browser_instance = webdriver.Edge(options=options)
    browser_instance.get(url)
    if plein_ecran:
        browser_instance.maximize_window()
    return browser_instance
