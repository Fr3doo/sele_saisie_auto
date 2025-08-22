# tests\test_launcher_roundtrip.py
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
    """Chemin ConfigParser : vérifie l'écriture complète des informations de mission."""
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
    project_vars = {
        "project_code": DummyVar("P"),
        "activity_code": DummyVar("A"),
        "category_code": DummyVar("C"),
        "sub_category_code": DummyVar("S"),
        "billing_action": DummyVar("FACTURER"),
    }
    location_vars = {"lundi": (DummyVar("Site"), DummyVar("Remote"))}
    log_file = str(tmp_path / "log.html")

    save_all(
        config,
        raw_cfg,
        log_file,
        date_var,
        debug_var,
        schedule_vars,
        cgi_vars,
        project_vars,
        location_vars,
    )

    reread = read_config_ini(log_file)
    assert isinstance(reread, configparser.ConfigParser)
    assert reread.get("settings", "date_cible") == "2024-07-01"
    assert reread.get("project_information", "billing_action") == "FACTURER"
    assert reread.get("project_information", "project_code") == "P"
    assert reread.get("project_information", "activity_code") == "A"
    assert reread.get("project_information", "category_code") == "C"
    assert reread.get("project_information", "sub_category_code") == "S"
    assert reread.get("work_schedule", "lundi").startswith("remote")
    assert reread.get("work_location_am", "lundi") == "Site"
    assert reread.get("additional_information_lunch_break_duration", "lundi") == "OUI"


def test_save_all_roundtrip_dict_backend(tmp_path: Path, monkeypatch) -> None:
    """Chemin dict/_dict_to_configparser : valide l'autre branche de save_all."""
    config_path = tmp_path / "config.ini"
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.get_runtime_config_path",
        lambda log_file=None: str(config_path),
    )
    config_path.write_text("[settings]\n")

    # Variables
    date_var = DummyVar("2024-07-02")
    debug_var = DummyVar("INFO")
    schedule_vars = {"mardi": (DummyVar("site"), DummyVar("09-17"))}
    cgi_vars = {
        "mardi": {
            "rest": DummyVar("NON"),
            "work": DummyVar("OUI"),
            "half": DummyVar("NON"),
            "lunch": DummyVar("30"),
        }
    }
    project_vars = {
        "project_code": DummyVar("PX"),
        "activity_code": DummyVar("AX"),
        "category_code": DummyVar("CX"),
        "sub_category_code": DummyVar("SX"),
        "billing_action": DummyVar("NE_PAS_FACTURER"),
    }
    location_vars = {"mardi": (DummyVar("Remote"), DummyVar("Site"))}
    log_file = str(tmp_path / "log2.html")

    # raw_cfg en dict -> déclenche la branche _dict_to_configparser
    save_all(
        {"settings": {}},
        {},
        log_file,
        date_var,
        debug_var,
        schedule_vars,
        cgi_vars,
        project_vars,
        location_vars,
    )

    reread = read_config_ini(log_file)
    assert isinstance(reread, configparser.ConfigParser)
    assert reread.get("settings", "date_cible") == "2024-07-02"
    assert reread.get("project_information", "billing_action") == "NE_PAS_FACTURER"
    assert reread.get("project_information", "project_code") == "PX"
    assert reread.get("project_information", "activity_code") == "AX"
    assert reread.get("project_information", "category_code") == "CX"
    assert reread.get("project_information", "sub_category_code") == "SX"
    assert reread.get("work_schedule", "mardi").startswith("site")
    assert reread.get("work_location_am", "mardi") == "Remote"
    assert reread.get("additional_information_lunch_break_duration", "mardi") == "30"