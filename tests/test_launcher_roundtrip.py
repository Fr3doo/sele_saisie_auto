import configparser
from pathlib import Path

from sele_saisie_auto.launcher import save_all
from sele_saisie_auto.read_or_write_file_config_ini_utils import read_config_ini


class DummyVar:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def get(self) -> str:
        return self.value


def _sample_schedule() -> dict[str, tuple[DummyVar, DummyVar, DummyVar]]:
    return {"lundi": (DummyVar("remote"), DummyVar("desc"), DummyVar("08-12"))}


def _sample_cgi() -> dict[str, dict[str, DummyVar]]:
    return {
        "lundi": {
            "rest": DummyVar("OUI"),
            "work": DummyVar("NON"),
            "half": DummyVar("NON"),
            "lunch": DummyVar("OUI"),
        }
    }


def _sample_mission() -> dict[str, DummyVar]:
    return {
        "project_code": DummyVar("P1"),
        "activity_code": DummyVar("A1"),
        "category_code": DummyVar("C1"),
        "sub_category_code": DummyVar("S1"),
        "billing_action": DummyVar("FACTURER"),
    }


def _sample_location() -> dict[str, tuple[DummyVar, DummyVar]]:
    return {"lundi": (DummyVar("Site"), DummyVar("Remote"))}


def _prepare(tmp_path: Path, monkeypatch) -> tuple[
    dict[str, dict[str, str]],
    configparser.ConfigParser,
    DummyVar,
    DummyVar,
    dict[str, tuple[DummyVar, DummyVar, DummyVar]],
    dict[str, dict[str, DummyVar]],
    dict[str, DummyVar],
    dict[str, tuple[DummyVar, DummyVar]],
    str,
]:
    config_path = tmp_path / "config.ini"
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.get_runtime_config_path",
        lambda log_file=None: str(config_path),
    )
    config_path.write_text("[settings]\n")
    config: dict[str, dict[str, str]] = {"settings": {}}
    raw_cfg = configparser.ConfigParser()
    date_var = DummyVar("2024-07-01")
    debug_var = DummyVar("WARNING")
    schedule_vars = _sample_schedule()
    cgi_vars = _sample_cgi()
    mission_vars = _sample_mission()
    location_vars = _sample_location()
    log_file = str(tmp_path / "log.html")
    return (
        config,
        raw_cfg,
        date_var,
        debug_var,
        schedule_vars,
        cgi_vars,
        mission_vars,
        location_vars,
        log_file,
    )


def _assert_roundtrip(log_file: str) -> None:
    reread = read_config_ini(log_file)
    assert isinstance(reread, configparser.ConfigParser)
    expected = [
        (("settings", "date_cible"), "2024-07-01"),
        (("project_information", "billing_action"), "FACTURER"),
        (("project_information", "project_code"), "P1"),
        (("work_description", "lundi"), "desc"),
        (("work_location_am", "lundi"), "Site"),
        (("additional_information_lunch_break_duration", "lundi"), "OUI"),
    ]
    for (section, key), value in expected:
        assert reread.get(section, key) == value
    assert reread.get("work_schedule", "lundi").startswith("remote")


def test_save_all_roundtrip(tmp_path: Path, monkeypatch) -> None:
    (
        config,
        raw_cfg,
        date_var,
        debug_var,
        schedule_vars,
        cgi_vars,
        mission_vars,
        location_vars,
        log_file,
    ) = _prepare(tmp_path, monkeypatch)
    save_all(
        config,
        raw_cfg,
        log_file,
        date_var,
        debug_var,
        schedule_vars,
        cgi_vars,
        mission_vars,
        location_vars,
    )
    _assert_roundtrip(log_file)
