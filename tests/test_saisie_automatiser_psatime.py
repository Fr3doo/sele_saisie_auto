import sys
import types
from configparser import ConfigParser
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

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


class DummySHM:
    def __init__(self, name):
        self.name = name
        if "nom" in name:
            self.buf = bytearray(b"user")
        else:
            self.buf = bytearray(b"pass")

    def close(self):
        pass

    def unlink(self):
        pass


class DummyManager:
    def __init__(self, log_file):
        self.log_file = log_file
        self.driver = "driver"

    def open(self, url, fullscreen=False, headless=False, no_sandbox=False):
        return self.driver

    def close(self):
        self.driver = None


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
    monkeypatch.setattr(
        sap,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: cfg),
    )
    monkeypatch.setattr(sap, "set_log_file_selenium", lambda lf: None)
    monkeypatch.setattr(sap, "set_log_file_infos", lambda lf: None)
    monkeypatch.setattr(sap, "EncryptionService", lambda lf: DummyEnc())
    sap.initialize("log.html")


def test_helpers(monkeypatch):
    messages = []
    monkeypatch.setattr(sap, "LOG_FILE", "log.html", raising=False)
    monkeypatch.setattr(sap, "write_log", lambda msg, f, level: messages.append(msg))
    assert sap.get_next_saturday_if_not_saturday("01/07/2024") == "06/07/2024"
    assert sap.get_next_saturday_if_not_saturday("06/07/2024") == "06/07/2024"
    assert sap.est_en_mission("En mission") is True
    jours = []
    assert sap.ajouter_jour_a_jours_remplis("lundi", jours) == ["lundi"]
    sap.afficher_message_insertion("lundi", "8", 0, "tentative d'insertion n°")
    monkeypatch.setattr(sap.os, "system", lambda cmd: messages.append(cmd))
    sap.clear_screen()
    sap.seprateur_menu_affichage_log()
    with monkeypatch.context() as m:
        printed = []
        m.setattr("builtins.print", lambda msg: printed.append(msg))
        sap.seprateur_menu_affichage_console()
    sap.log_initialisation()
    assert messages


def test_initialize_sets_globals(monkeypatch):
    setup_init(monkeypatch)
    assert sap.URL == "http://test"
    assert sap.JOURS_DE_TRAVAIL["lundi"] == ("En mission", "8")
    assert sap.INFORMATIONS_PROJET_MISSION["billing_action"] == "B"


def test_initialize_shared_memory(monkeypatch):
    setup_init(monkeypatch)
    monkeypatch.setattr(
        sap, "shared_memory", types.SimpleNamespace(SharedMemory=DummySHM)
    )
    sap.encryption_service = DummyEnc()
    monkeypatch.setattr(sap, "write_log", lambda *a, **k: None)
    result = sap.initialize_shared_memory()
    assert result[2] == b"user"
    assert result[4] == b"pass"


def test_main_flow(monkeypatch):
    setup_init(monkeypatch)
    sap.LOG_FILE = "log.html"
    sap.URL = "http://test"
    sap.DATE_CIBLE = "06/07/2024"
    sap.CHOIX_USER = True

    monkeypatch.setattr(sap, "log_initialisation", lambda: None)
    monkeypatch.setattr(
        sap,
        "initialize_shared_memory",
        lambda: [b"k", object(), b"user", object(), b"pass", object()],
    )
    monkeypatch.setattr(sap, "SeleniumDriverManager", DummyManager)

    def fake_wait(driver, by, ident, *a, **k):
        class Elem:
            def __init__(self):
                self.val = "01/07/2024"

            def get_attribute(self, name):
                return self.val

            def clear(self):
                pass

            def send_keys(self, v):
                self.val = v

        if ident == "EX_TIME_ADD_VW_PERIOD_END_DT":
            return Elem()
        return object()

    monkeypatch.setattr(sap, "wait_for_element", fake_wait)
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
    monkeypatch.setattr(sap, "sys", types.SimpleNamespace(exit=lambda: None))
    cleanup_called = {}
    monkeypatch.setattr(
        sap,
        "cleanup_resources",
        lambda *a, **k: cleanup_called.setdefault("done", True),
    )
    monkeypatch.setattr(sap, "seprateur_menu_affichage_console", lambda: None)
    monkeypatch.setattr(__import__("builtins"), "input", lambda *a, **k: None)
    monkeypatch.setattr(sap, "write_log", lambda *a, **k: None)

    sap.main("log.html")

    assert cleanup_called["done"] is True
