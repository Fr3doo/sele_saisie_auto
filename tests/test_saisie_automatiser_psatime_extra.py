import types

import pytest

from sele_saisie_auto import saisie_automatiser_psatime as sap
from sele_saisie_auto import shared_utils
from tests.test_saisie_automatiser_psatime import (
    DummyEnc,
    DummyManager,
    DummySHM,
    DummySHMService,
    setup_init,
)

pytestmark = pytest.mark.slow


def test_initialize_date_none(monkeypatch, sample_config):
    cfg = sample_config
    cfg["settings"]["date_cible"] = "none"
    from sele_saisie_auto.app_config import AppConfig

    app_cfg = AppConfig.from_parser(cfg)
    monkeypatch.setattr(sap, "set_log_file_selenium", lambda lf: None)
    monkeypatch.setattr(sap, "set_log_file_infos", lambda lf: None)
    monkeypatch.setattr(sap, "EncryptionService", lambda lf, shm=None: DummyEnc())
    sap.initialize("log.html", app_cfg)
    monkeypatch.setattr(
        sap,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: app_cfg),
    )
    assert sap.context.config.date_cible is None


def test_clear_screen_windows(monkeypatch):
    called = []
    monkeypatch.setattr(
        shared_utils,
        "os",
        types.SimpleNamespace(name="nt"),
        raising=False,
    )
    monkeypatch.setattr(
        shared_utils.subprocess,
        "run",
        lambda cmd, *a, **k: called.append(cmd),
    )
    shared_utils.clear_screen()
    assert "cls" in called[0]


def test_ajouter_jour_a_jours_remplis_existing():
    jours = ["lundi"]
    assert sap.ajouter_jour_a_jours_remplis("lundi", jours) == ["lundi"]


def test_afficher_message_insertion_other(monkeypatch):
    logs = []
    monkeypatch.setattr(sap, "write_log", lambda msg, f, level: logs.append(msg))
    sap.afficher_message_insertion("mardi", "8", 1, "ok", "log.html")
    assert logs


def test_log_initialisation_no_log():
    sap._AUTOMATION = None
    with pytest.raises(RuntimeError):
        sap.log_initialisation()


def test_initialize_shared_memory_error(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    monkeypatch.setattr(
        sap, "shared_memory", types.SimpleNamespace(SharedMemory=DummySHM)
    )
    sap.context.encryption_service = DummyEnc()
    sap.context.shared_memory_service = DummySHMService()
    monkeypatch.setattr(
        sap.context.shared_memory_service,
        "recuperer_de_memoire_partagee",
        lambda *a, **k: (None, b"k" * 32),
    )
    exit_called = {}
    monkeypatch.setattr(
        sap.sys, "exit", lambda code=0: exit_called.setdefault("exit", code)
    )
    monkeypatch.setattr(sap, "write_log", lambda *a, **k: None)
    sap.initialize_shared_memory()
    assert exit_called["exit"] == 1


def test_switch_to_iframe_main_target_win0_false(monkeypatch):
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: True)
    monkeypatch.setattr(sap, "switch_to_iframe_by_id_or_name", lambda *a, **k: False)
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    assert sap.switch_to_iframe_main_target_win0("drv") is False


def test_handle_date_input_no_change(monkeypatch):
    class Input:
        def __init__(self):
            self.val = "06/07/2024"

        def get_attribute(self, _):
            return self.val

    inp = Input()
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: inp)
    monkeypatch.setattr(
        sap, "get_next_saturday_if_not_saturday", lambda d: "06/07/2024"
    )
    monkeypatch.setattr(
        sap,
        "modifier_date_input",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError()),
    )
    logs = []
    monkeypatch.setattr(sap, "write_log", lambda msg, f, level: logs.append(msg))
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    sap.handle_date_input("drv", None)
    assert "Aucune modification" in logs[0]


def test_submit_date_cible_no_element(monkeypatch):
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: False)
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    assert sap.submit_date_cible("drv") is False


def test_navigate_from_work_schedule_without_element(monkeypatch):
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: False)
    called = {}
    monkeypatch.setattr(
        sap, "switch_to_default_content", lambda *a, **k: called.setdefault("sw", True)
    )
    sap.navigate_from_work_schedule_to_additional_information_page("drv")
    assert called["sw"] is True


def test_submit_and_validate_additional_information_no_iframe(monkeypatch):
    seq = iter([True, False])
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: next(seq))
    monkeypatch.setattr(sap, "switch_to_iframe_by_id_or_name", lambda *a, **k: False)
    monkeypatch.setattr(sap, "write_log", lambda *a, **k: None)
    monkeypatch.setattr(sap, "click_element_without_wait", lambda *a, **k: None)
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    sap.submit_and_validate_additional_information("drv")


def test_save_draft_and_validate_no_element(monkeypatch):
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: False)
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    assert sap.save_draft_and_validate("drv") is False


def test_cleanup_resources_calls():
    enc = DummyEnc()
    manager = DummyManager("log.html")
    sap.context.encryption_service = enc
    shm_service = DummySHMService()
    sap.context.shared_memory_service = shm_service
    sap.cleanup_resources(manager, "c", "n", None)
    assert shm_service.removed == ["c", "n"]
    assert manager.driver is None
