import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import sele_saisie_auto.form_processing.description_processor as dp  # noqa: E402
from sele_saisie_auto.strategies.element_filling_strategy import (  # noqa: E402
    ElementFillingContext,
    InputFillingStrategy,
)

CFG = {
    "description_cible": "desc",
    "id_value_ligne": "row",
    "id_value_jours": "days",
    "type_element": "input",
    "valeurs_a_remplir": {},
}


def test_process_description_main(monkeypatch):
    captured = {}
    monkeypatch.setattr(dp, "_find_description_row", lambda *a, **k: 0)
    monkeypatch.setattr(dp, "_collect_filled_days", lambda *a, **k: [])

    def fake_fill(*args, **kwargs):
        captured["strategy"] = kwargs.get("filling_context").strategy.__class__

    monkeypatch.setattr(dp, "_fill_days", fake_fill)
    ctx = ElementFillingContext(InputFillingStrategy())
    dp.process_description(None, CFG, "log", filling_context=ctx)
    assert captured["strategy"] is InputFillingStrategy


def test_process_description_row_missing(monkeypatch):
    monkeypatch.setattr(dp, "_find_description_row", lambda *a, **k: None)
    dp.process_description(None, CFG, "log")


def test_fill_days_integration(monkeypatch):
    sequence = []

    class DummyElement:
        pass

    monkeypatch.setattr(dp, "_find_description_row", lambda *a, **k: 0)
    monkeypatch.setattr(dp, "_collect_filled_days", lambda *a, **k: [])
    monkeypatch.setattr(dp, "_get_element", lambda *a, **k: DummyElement())
    monkeypatch.setattr(dp, "verifier_champ_jour_rempli", lambda *a, **k: False)

    def fake_fill(element, value, logger=None):
        sequence.append(value)

    ctx = ElementFillingContext()
    ctx.set_strategy(InputFillingStrategy())
    monkeypatch.setattr(ctx, "fill", lambda el, val, logger=None: fake_fill(el, val))

    cfg = CFG | {"valeurs_a_remplir": {"lundi": "1"}}
    dp.process_description(None, cfg, "log", filling_context=ctx)
    assert "1" in sequence


def test_collect_filled_days_no_elements(monkeypatch):
    monkeypatch.setattr(dp, "_get_element", lambda *a, **k: None)
    result = dp._collect_filled_days(None, None, "days", 0, "log")
    assert result == []


def test_fill_days_skips(monkeypatch):
    called = []

    class DummyElement:
        pass

    monkeypatch.setattr(dp, "_get_element", lambda *a, **k: DummyElement())
    ctx = ElementFillingContext(InputFillingStrategy())
    monkeypatch.setattr(ctx, "fill", lambda *a, **k: called.append("filled"))

    dp._fill_days(
        None,
        None,
        "days",
        0,
        {"mardi": "1"},
        ["lundi"],
        "input",
        "log",
        filling_context=ctx,
    )
    assert called == ["filled"]


def test_collect_filled_days_detects(monkeypatch):
    monkeypatch.setattr(dp, "_get_element", lambda *a, **k: object())

    def fake_verifier(element, day_name):
        return day_name if day_name in {"lundi", "mercredi"} else None

    monkeypatch.setattr(dp, "verifier_champ_jour_rempli", fake_verifier)
    result = dp._collect_filled_days(None, None, "days", 0, "log")
    assert result == ["lundi", "mercredi"]


def test_fill_days_uses_strategy(monkeypatch):
    recorded = []
    dummy = object()
    monkeypatch.setattr(dp, "_get_element", lambda *a, **k: dummy)
    ctx = ElementFillingContext(InputFillingStrategy())
    monkeypatch.setattr(ctx, "fill", lambda e, v, logger=None: recorded.append((e, v)))

    dp._fill_days(
        None,
        None,
        "days",
        0,
        {"lundi": "1", "mardi": "2"},
        [],
        "input",
        "log",
        filling_context=ctx,
    )
    assert recorded == [(dummy, "1"), (dummy, "2")]
