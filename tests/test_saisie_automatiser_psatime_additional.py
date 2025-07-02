import sys
from pathlib import Path

import console_ui

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

import types  # noqa: E402
from configparser import ConfigParser  # noqa: E402

from selenium.common.exceptions import (  # noqa: E402
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)

import saisie_automatiser_psatime as sap  # noqa: E402


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


def make_config():
    cfg = ConfigParser()
    cfg["credentials"] = {"login": "enc_login", "mdp": "enc_pwd"}
    cfg["settings"] = {
        "url": "http://test",
        "date_cible": "01/07/2024",
        "liste_items_planning": '"desc1", "desc2"',
    }
    cfg["work_schedule"] = {"lundi": "En mission,8"}
    cfg["project_information"] = {"billing_action": "Facturable"}
    cfg["additional_information_rest_period_respected"] = {"lundi": "Oui"}
    cfg["additional_information_work_time_range"] = {"lundi": "8-16"}
    cfg["additional_information_half_day_worked"] = {"lundi": "Non"}
    cfg["additional_information_lunch_break_duration"] = {"lundi": "1"}
    cfg["work_location_am"] = {"lundi": "CGI"}
    cfg["work_location_pm"] = {"lundi": "CGI"}
    return cfg


def setup_init(monkeypatch):
    cfg = make_config()
    from app_config import AppConfig

    app_cfg = AppConfig.from_parser(cfg)
    monkeypatch.setattr(sap, "set_log_file_selenium", lambda lf: None)
    monkeypatch.setattr(sap, "set_log_file_infos", lambda lf: None)
    monkeypatch.setattr(sap, "EncryptionService", lambda lf, shm=None: DummyEnc())
    monkeypatch.setattr(sap, "SharedMemoryService", lambda lf: DummySHMService())
    sap.initialize("log.html", app_cfg)
    monkeypatch.setattr(
        sap,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: app_cfg),
    )


def test_connect_to_psatime(monkeypatch):
    setup_init(monkeypatch)
    actions = []
    monkeypatch.setattr(
        sap.PSATimeAutomation,
        "wait_for_dom",
        lambda self, *a, **k: actions.append("dom"),
    )
    monkeypatch.setattr(
        sap,
        "send_keys_to_element",
        lambda driver, by, ident, value: actions.append((ident, value)),
    )
    sap.context.encryption_service = DummyEnc()
    sap.connect_to_psatime("drv", b"key", b"user", b"pass")
    assert ("userid", "user") in actions
    assert ("pwd", "pass") in actions
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


def test_handle_date_input(monkeypatch):
    class Input:
        def __init__(self):
            self.val = "01/07/2024"

        def get_attribute(self, _):
            return self.val

    inp = Input()
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: inp)
    result = {}
    monkeypatch.setattr(
        sap, "modifier_date_input", lambda elem, val, msg: result.setdefault("v", val)
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    sap.handle_date_input("drv", "10/07/2024")
    assert result["v"] == "10/07/2024"


def test_handle_date_input_auto(monkeypatch):
    class Input:
        def __init__(self):
            self.val = "01/07/2024"

        def get_attribute(self, _):
            return self.val

    inp = Input()
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: inp)
    monkeypatch.setattr(
        sap, "get_next_saturday_if_not_saturday", lambda d: "06/07/2024"
    )
    result = {}
    monkeypatch.setattr(
        sap, "modifier_date_input", lambda elem, val, msg: result.setdefault("v", val)
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    sap.handle_date_input("drv", None)
    assert result["v"] == "06/07/2024"


def test_submit_date_cible(monkeypatch):
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: True)
    called = {}
    monkeypatch.setattr(
        sap,
        "send_keys_to_element",
        lambda *a, **k: called.setdefault("done", True),
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    assert sap.submit_date_cible("drv") is True
    assert called["done"] is True


def test_navigation_pages(monkeypatch):
    setup_init(monkeypatch)
    seq = iter([True, True])

    def fake_wait(*a, **k):
        try:
            return next(seq)
        except StopIteration:
            return False

    called = []
    monkeypatch.setattr(sap, "wait_for_element", fake_wait)
    monkeypatch.setattr(
        sap, "click_element_without_wait", lambda *a, **k: called.append("clk")
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation,
        "switch_to_iframe_main_target_win0",
        lambda self, *a, **k: called.append("sw") or True,
    )
    assert sap.navigate_from_home_to_date_entry_page("drv") is True
    assert called.count("clk") == 2
    assert "sw" in called


def test_additional_information(monkeypatch):
    seq = iter([True, True])
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: next(seq))
    monkeypatch.setattr(
        sap,
        "switch_to_iframe_by_id_or_name",
        lambda *a, **k: True,
    )
    collected = []
    monkeypatch.setattr(
        sap, "traiter_description", lambda *a, **k: collected.append("desc")
    )
    monkeypatch.setattr(sap, "write_log", lambda *a, **k: collected.append("log"))
    monkeypatch.setattr(
        sap, "click_element_without_wait", lambda *a, **k: collected.append("ok")
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    sap.context.descriptions = [
        {
            "description_cible": "d",
            "id_value_ligne": "x",
            "id_value_jours": "y",
            "type_element": "select",
            "valeurs_a_remplir": {"lundi": "1"},
        }
    ]
    sap.submit_and_validate_additional_information("drv")
    assert "desc" in collected
    assert "ok" in collected


def test_save_draft_and_validate(monkeypatch):
    setup_init(monkeypatch)
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: True)
    called = []
    monkeypatch.setattr(
        sap, "click_element_without_wait", lambda *a, **k: called.append("clk")
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    assert sap.save_draft_and_validate("drv") is True
    assert "clk" in called


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


def test_main_exceptions(monkeypatch):
    setup_init(monkeypatch)
    sap.CHOIX_USER = True
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
    monkeypatch.setattr(sap, "SeleniumDriverManager", DummyManager)
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: True)
    monkeypatch.setattr(sap, "modifier_date_input", lambda *a, **k: None)
    monkeypatch.setattr(sap, "switch_to_iframe_by_id_or_name", lambda *a, **k: True)
    monkeypatch.setattr(sap, "click_element_without_wait", lambda *a, **k: None)
    monkeypatch.setattr(sap, "send_keys_to_element", lambda *a, **k: None)
    monkeypatch.setattr(sap, "wait_for_dom", lambda *a, **k: None)
    monkeypatch.setattr(sap, "wait_until_dom_is_stable", lambda *a, **k: None)
    monkeypatch.setattr(sap, "wait_for_dom_ready", lambda *a, **k: None)
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
