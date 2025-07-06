from sele_saisie_auto import saisie_automatiser_psatime as sap
from tests.test_saisie_automatiser_psatime_additional import setup_init


def test_wait_for_dom_after_decorator(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    monkeypatch.setattr(
        sap._AUTOMATION.waiter, "wait_for_element", lambda *a, **k: True
    )
    monkeypatch.setattr(sap, "send_keys_to_element", lambda *a, **k: None)
    calls = []
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: calls.append("dom")
    )
    sap.submit_date_cible(driver="drv")
    assert calls.count("dom") == 2
