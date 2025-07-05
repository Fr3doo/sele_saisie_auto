"""Browser navigation helpers."""

from __future__ import annotations

import requests  # type: ignore[import]
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions

from . import LOG_FILE, write_log


def verifier_accessibilite_url(url):
    """Teste l'accessibilité d'une URL."""
    try:
        response = requests.get(url, timeout=10, verify=True)
        if response.status_code == 200:
            write_log(
                f"🔹 URL accessible, avec vérification SSL : {url}", LOG_FILE, "INFO"
            )
            return True
        write_log(
            f"❌ URL inaccessible, avec vérification SSL - statut : {response.status_code}",
            LOG_FILE,
            "ERROR",
        )
        return False
    except requests.exceptions.SSLError as ssl_err:
        write_log(f"❌ Erreur SSL détectée : {ssl_err}", LOG_FILE, "ERROR")
        try:
            response = requests.get(url, timeout=10, verify=False)  # nosec B501
            if response.status_code == 200:
                write_log(
                    f"⚠️ URL accessible, sans vérification SSL : {url}",
                    LOG_FILE,
                    "WARNING",
                )
                return True
        except Exception as e:  # noqa: BLE001
            write_log(
                f"❌ URL inaccessible, sans vérification SSL : {e}", LOG_FILE, "ERROR"
            )
            return False
    except requests.exceptions.RequestException as req_err:
        write_log(f"❌ Erreur de connexion à l'URL : {req_err}", LOG_FILE, "ERROR")
        return False


def switch_to_frame_by_id(driver, frame_id):
    """Switch into a frame identified by its DOM id."""
    driver.switch_to.frame(driver.find_element(By.ID, frame_id))
    write_log(
        f"Bascule dans l'iframe '{frame_id}' réussie.",
        LOG_FILE,
        "DEBUG",
    )
    return True


def ouvrir_navigateur_sur_ecran_principal(
    plein_ecran=False,
    url="https://www.example.com",
    headless=False,
    no_sandbox=False,
):
    """Open the Edge browser and navigate to the URL."""
    edge_browser_options = EdgeOptions()
    edge_browser_options.use_chromium = True

    if headless:
        edge_browser_options.add_argument("--headless")
    if no_sandbox:
        edge_browser_options.add_argument("--no-sandbox")

    if not verifier_accessibilite_url(url):
        return None

    try:
        browser_instance = webdriver.Edge(options=edge_browser_options)
        browser_instance.get(url)
        if plein_ecran:
            browser_instance.maximize_window()
        return browser_instance
    except WebDriverException as e:
        if "ERR_CONNECTION_CLOSED" in str(e):
            write_log("❌ La connexion au serveur a été fermée.", LOG_FILE, "ERROR")
        else:
            write_log(f"❌ Erreur WebDriver : {str(e)}", LOG_FILE, "ERROR")
        return None


def definir_taille_navigateur(navigateur, largeur, hauteur):
    """Set the browser window size."""
    navigateur.set_window_size(largeur, hauteur)
    return navigateur
