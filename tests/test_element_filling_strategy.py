import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.strategies.element_filling_strategy import (
    ElementFillingContext,
    InputFillingStrategy,
    SelectFillingStrategy,
)


def test_input_filling_strategy(monkeypatch):
    calls = {}

    class Field:
        def clear(self):
            calls["clear"] = True

        def send_keys(self, value):
            calls["value"] = value

    InputFillingStrategy().fill(Field(), "42")
    assert calls == {"clear": True, "value": "42"}


def test_select_filling_strategy(monkeypatch):
    selected = {}

    class DummySelect:
        def __init__(self, element):
            pass

        def select_by_visible_text(self, text):
            selected["text"] = text

    monkeypatch.setattr(
        "sele_saisie_auto.strategies.element_filling_strategy.Select",
        DummySelect,
    )

    SelectFillingStrategy().fill(object(), "option")
    assert selected["text"] == "option"


def test_element_filling_context(monkeypatch):
    called = {}

    class DummyStrategy:
        def fill(self, element, value, logger=None):
            called["e"] = element
            called["v"] = value

    ctx = ElementFillingContext(DummyStrategy())
    ctx.fill("el", "val")
    assert called == {"e": "el", "v": "val"}

    new_called = {}

    class OtherStrategy:
        def fill(self, element, value, logger=None):
            new_called["e"] = element

    ctx.set_strategy(OtherStrategy())
    ctx.fill("el2", "v2")
    assert new_called["e"] == "el2"
