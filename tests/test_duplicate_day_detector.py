import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.logging_service import Logger  # noqa: E402
from sele_saisie_auto.selenium_utils import NoSuchElementException  # noqa: E402
from sele_saisie_auto.selenium_utils.duplicate_day_detector import (  # noqa: E402
    DuplicateDayDetector,
)


class DummyDesc:
    def __init__(self, text=""):
        self.text = text


class DummyField:
    def __init__(self, value=""):
        self.value = value

    def get_attribute(self, name):
        return self.value


class DummyDriver:
    def __init__(self, descs, values):
        self.descs = descs
        self.values = values

    def find_element(self, by, ident):
        if ident.startswith("POL_DESCR$"):
            idx = int(ident.split("$")[1])
            if idx in self.descs:
                return DummyDesc(self.descs[idx])
            raise NoSuchElementException("desc")
        if ident.startswith("POL_TIME"):
            prefix, row = ident.split("$")
            day = int(prefix[8:])
            idx = int(row)
            if (day, idx) in self.values:
                return DummyField(self.values[(day, idx)])
            raise NoSuchElementException("day")
        raise NoSuchElementException("unknown")

    def find_elements(self, by, value):
        if by == "css selector" and value == "[id^='POL_DESCR$']":
            return [DummyDesc(self.descs[idx]) for idx in sorted(self.descs)]
        return []


def test_detector_uses_builder(monkeypatch):
    calls = []

    def fake_build(base, day, row):
        calls.append((base, day, row))
        return f"{base}{day}${row}"

    monkeypatch.setattr(
        "sele_saisie_auto.selenium_utils.duplicate_day_detector.ElementIdBuilder.build_day_input_id",
        fake_build,
    )

    logger = Logger(None, writer=lambda *a, **k: None)
    driver = DummyDriver({0: "A"}, {(2, 0): "8"})
    detector = DuplicateDayDetector(logger=logger)
    detector.detect(driver)
    assert calls


def test_detector_logs_duplicate(monkeypatch):
    logs = []
    logger = Logger(None, writer=lambda msg, *a, **k: logs.append(msg))
    descs = {0: "A", 1: "B"}
    values = {(2, 0): "8", (2, 1): "7"}
    driver = DummyDriver(descs, values)
    detector = DuplicateDayDetector(logger=logger)
    detector.detect(driver)
    assert any("Doublon" in m for m in logs)


def test_detector_no_duplicate(monkeypatch):
    logs = []
    logger = Logger(None, writer=lambda msg, *a, **k: logs.append(msg))
    descs = {0: "A"}
    values = {(2, 0): "8", (3, 0): "4"}
    driver = DummyDriver(descs, values)
    detector = DuplicateDayDetector(logger=logger)
    detector.detect(driver)
    assert any("Aucun doublon" in m for m in logs)


def test_detector_handles_missing_rows(monkeypatch):
    logs = []
    logger = Logger(None, writer=lambda msg, *a, **k: logs.append(msg))
    descs = {0: "A"}
    values = {}
    driver = DummyDriver(descs, values)
    monkeypatch.setattr(
        driver,
        "find_elements",
        lambda by, value: [DummyDesc("A"), DummyDesc("B")],
    )
    detector = DuplicateDayDetector(logger=logger)
    detector.detect(driver)
    assert any("Fin de l'analyse" in m for m in logs)
