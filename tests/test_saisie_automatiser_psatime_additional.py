import sys
from pathlib import Path

import pytest

from sele_saisie_auto import console_ui

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import types  # noqa: E402

from selenium.common.exceptions import (  # noqa: E402
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)

from sele_saisie_auto import saisie_automatiser_psatime as sap  # noqa: E402

pytestmark = pytest.mark.slow
from sele_saisie_auto.locators import Locators  # noqa: E402


class DummyEnc:
    def __init__(self):
        self.removed = []

    def recuperer_de_memoire_partagee(self, name, size):
        return object(), b"k" * size

    def dechiffrer_donnees(self, data, key):
        return data.decode() if isinstance(data, bytes) else data

    def supprimer_memoire_partagee_securisee(self, mem):
        self.removed.append(mem)


class DummySHMService:
    def __init__(self):
        self.removed = []

    def recuperer_de_memoire_partagee(self, name, size):
        return object(), b"k" * size

    def supprimer_memoire_partagee_securisee(self, mem):
        self.removed.append(mem)


class DummyManager:
    def __init__(self, log_file):
        self.log_file = log_file
        self.driver = "driver"

    def open(self, url, fullscreen=False, headless=False, no_sandbox=False):
        return self.driver

    def close(self):
        self.driver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


def setup_init(monkeypatch, cfg):
    from sele_saisie_auto.app_config import AppConfig

    app_cfg = AppConfig.from_parser(cfg)
    monkeypatch.setattr(sap, "set_log_file_selenium", lambda lf: None)
    monkeypatch.setattr(sap, "EncryptionService", lambda lf, shm=None: DummyEnc())
    monkeypatch.setattr(sap, "SharedMemoryService", lambda lf: DummySHMService())
    sap.initialize(
        "log.html",
        app_cfg,
        choix_user=True,
        memory_config=sap.MemoryConfig(),
    )
    monkeypatch.setattr(
        sap,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: app_cfg),
    )


def test_connect_to_psatime(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    actions = []
    from sele_saisie_auto.automation import login_handler as lh

    monkeypatch.setattr(
        lh,
        "send_keys_to_element",
        lambda driver, by, ident, value: actions.append((ident, value)),
    )
    sap.context.encryption_service = DummyEnc()
    sap._AUTOMATION.login_handler.browser_session.wait_for_dom = (
        lambda d: actions.append("dom")
    )
    sap._AUTOMATION.login_handler.connect_to_psatime("drv", b"key", b"user", b"pass")
    assert (Locators.USERNAME.value, "user") in actions
    assert (Locators.PASSWORD.value, "pass") in actions
    assert "dom" in actions


def test_switch_to_iframe(monkeypatch):
    calls = []
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: True)
    monkeypatch.setattr(
        sap,
        "switch_to_iframe_by_id_or_name",
        lambda *a, **k: calls.append("sw") or True,
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: calls.append("dom")
    )
    assert sap.switch_to_iframe_main_target_win0("drv") is True
    assert "sw" in calls
    assert "dom" in calls


def test_submit_date_cible(monkeypatch):
    called = {}
    monkeypatch.setattr(
        sap._AUTOMATION.date_entry_page,
        "submit_date_cible",
        lambda driver: called.setdefault("done", True) or True,
    )
    assert sap.submit_date_cible("drv") is True
    assert called["done"] is True


def test_navigation_pages(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    called = {}
    monkeypatch.setattr(
        sap._AUTOMATION.date_entry_page,
        "navigate_from_home_to_date_entry_page",
        lambda driver: called.setdefault("nav", True),
    )
    assert sap.navigate_from_home_to_date_entry_page("drv") is True
    assert called["nav"] is True


def test_additional_information(monkeypatch):
    called = {}
    monkeypatch.setattr(
        sap._AUTOMATION.additional_info_page,
        "submit_and_validate_additional_information",
        lambda driver: called.setdefault("done", True),
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    sap.submit_and_validate_additional_information("drv")
    assert called["done"] is True


def test_save_draft_and_validate(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    called = {}
    monkeypatch.setattr(
        sap._AUTOMATION.additional_info_page,
        "save_draft_and_validate",
        lambda driver: called.setdefault("done", True) or True,
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    assert sap.save_draft_and_validate("drv") is True
    assert called["done"] is True


def test_cleanup_resources(monkeypatch):
    called = []
    manager = types.SimpleNamespace(close=lambda: called.append("close"))
    enc = DummyEnc()
    sap.context.encryption_service = enc
    shm_service = DummySHMService()
    sap.context.shared_memory_service = shm_service
    sap.cleanup_resources(manager, "c", "n", "p")
    assert shm_service.removed == ["c", "n", "p"]
    assert "close" in called


EXCEPTIONS = [
    NoSuchElementException("boom"),
    TimeoutException("boom"),
    WebDriverException("boom"),
    Exception("boom"),
]


def test_main_exceptions(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    sap._AUTOMATION.choix_user = True
    monkeypatch.setattr(sap, "log_initialisation", lambda: None)
    monkeypatch.setattr(
        sap.PSATimeAutomation,
        "initialize_shared_memory",
        lambda self: sap.Credentials(
            aes_key=b"k",
            mem_key=object(),
            login=b"user",
            mem_login=object(),
            password=b"pass",
            mem_password=object(),
        ),
    )
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: True)
    monkeypatch.setattr(sap, "modifier_date_input", lambda *a, **k: None)
    monkeypatch.setattr(sap, "switch_to_iframe_by_id_or_name", lambda *a, **k: True)
    monkeypatch.setattr(sap, "click_element_without_wait", lambda *a, **k: None)
    monkeypatch.setattr(sap, "send_keys_to_element", lambda *a, **k: None)
    monkeypatch.setattr(sap, "wait_for_dom", lambda *a, **k: None)
    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.wait_until_dom_is_stable",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.wait_for_dom_ready",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(sap, "program_break_time", lambda *a, **k: None)
    monkeypatch.setattr(
        sap.remplir_jours_feuille_de_temps, "main", lambda *a, **k: None
    )
    monkeypatch.setattr(sap, "traiter_description", lambda *a, **k: None)
    monkeypatch.setattr(sap, "detecter_doublons_jours", lambda *a, **k: None)
    monkeypatch.setattr(sap, "seprateur_menu_affichage_console", lambda: None)
    monkeypatch.setattr(
        console_ui,
        "ask_continue",
        lambda *a, **k: (_ for _ in ()).throw(ValueError()),
    )
    cleanup = {}
    monkeypatch.setattr(
        sap.PSATimeAutomation,
        "cleanup_resources",
        lambda self, *a, **k: cleanup.setdefault("done", True),
    )
    for exc in EXCEPTIONS:
        monkeypatch.setattr(
            sap, "setup_browser", lambda *a, **k: (_ for _ in ()).throw(exc)
        )
        sap.main("log.html")
    assert cleanup["done"] is True
