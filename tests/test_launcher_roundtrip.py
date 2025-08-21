import configparser
from pathlib import Path

from sele_saisie_auto.launcher import save_all
from sele_saisie_auto.read_or_write_file_config_ini_utils import read_config_ini


class DummyVar:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def get(self) -> str:
        return self.value


def test_save_all_roundtrip(tmp_path: Path, monkeypatch) -> None:
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
    schedule_vars = {"lundi": (DummyVar("remote"), DummyVar("08-12"))}
    cgi_vars = {
        "lundi": {
            "rest": DummyVar("OUI"),
            "work": DummyVar("NON"),
            "half": DummyVar("NON"),
            "lunch": DummyVar("OUI"),
        }
    }
    mission_vars = {"billing_action": DummyVar("FACTURER")}
    location_vars = {"lundi": (DummyVar("Site"), DummyVar("Remote"))}
    log_file = str(tmp_path / "log.html")

    save_all(
        config,
        raw_cfg,
        log_file,
        date_var,
        debug_var,
        schedule_vars,
        mission_vars,
        cgi_vars,
        location_vars,
    )

    reread = read_config_ini(log_file)
    assert isinstance(reread, configparser.ConfigParser)
    assert reread.get("settings", "date_cible") == "2024-07-01"
    assert reread.get("project_information", "billing_action") == "FACTURER"
    assert reread.get("work_schedule", "lundi").startswith("remote")
    assert reread.get("work_location_am", "lundi") == "Site"
    assert reread.get("additional_information_lunch_break_duration", "lundi") == "OUI"
