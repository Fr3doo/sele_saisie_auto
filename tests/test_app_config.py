import configparser
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import pytest  # noqa: E402

from sele_saisie_auto.app_config import AppConfig, load_config  # noqa: E402
from sele_saisie_auto.dropdown_options import BillingActionOption  # noqa: E402


def test_load_config_parses(tmp_path, monkeypatch):
    cfg = tmp_path / "config.ini"
    cfg.write_text(
        """[credentials]
login=enc
mdp=enc
[settings]
url=http://t
date_cible=01/07/2024
liste_items_planning="a", "b"
[cgi_options_billing_action]
Facturable = B
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log",
        lambda *a, **k: None,
    )

    app_cfg = load_config(str(tmp_path / "log.html"))
    assert isinstance(app_cfg, AppConfig)
    assert app_cfg.url == "http://t"
    assert app_cfg.date_cible == "01/07/2024"
    assert app_cfg.liste_items_planning == ["a", "b"]
    assert app_cfg.raw.get("credentials", "login") == "enc"
    billing = {o.label.lower(): o.code for o in app_cfg.cgi_options_billing_action}
    assert billing["facturable"] == "B"


def test_env_vars_override(tmp_path, monkeypatch):
    cfg = tmp_path / "config.ini"
    cfg.write_text(
        """[credentials]
login=file_login
mdp=file_mdp
[settings]
url=http://file
date_cible=01/07/2024
debug_mode=INFO
liste_items_planning="x"
[cgi_options_billing_action]
Facturable = B
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log",
        lambda *a, **k: None,
    )
    monkeypatch.setenv("PSATIME_URL", "http://env")
    monkeypatch.setenv("PSATIME_DATE_CIBLE", "02/07/2024")
    monkeypatch.setenv("PSATIME_LOGIN", "env_login")
    monkeypatch.setenv("PSATIME_MDP", "env_mdp")
    monkeypatch.setenv("PSATIME_DEBUG_MODE", "DEBUG")
    monkeypatch.setenv("PSATIME_LISTE_ITEMS_PLANNING", '"env1", "env2"')

    app_cfg = load_config(str(tmp_path / "log.html"))
    assert app_cfg.url == "http://env"
    assert app_cfg.date_cible == "02/07/2024"
    assert app_cfg.debug_mode == "DEBUG"
    assert app_cfg.liste_items_planning == ["env1", "env2"]
    assert app_cfg.raw.get("credentials", "login") == "env_login"


def test_load_config_fails_on_empty_url(tmp_path, monkeypatch):
    cfg = tmp_path / "config.ini"
    cfg.write_text(
        """[credentials]
login=enc
mdp=enc
[settings]
url=
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log",
        lambda *a, **k: None,
    )
    with pytest.raises(ValueError):
        load_config(str(tmp_path / "log.html"))


def test_load_config_fails_on_missing_credentials(tmp_path, monkeypatch):
    cfg = tmp_path / "config.ini"
    cfg.write_text(
        """[credentials]
login=
mdp=
[settings]
url=http://t
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log",
        lambda *a, **k: None,
    )
    with pytest.raises(ValueError):
        load_config(str(tmp_path / "log.html"))


def test__charger_settings_basic():
    parser = configparser.ConfigParser()
    parser.read_dict(
        {
            "settings": {
                "url": "http://x",
                "date_cible": "01/01/2024",
                "debug_mode": "DEBUG",
                "liste_items_planning": '"a", "b"',
                "default_timeout": "5",
                "long_timeout": "9",
            }
        }
    )

    parsed = AppConfig._charger_settings(parser)
    assert parsed["url"] == "http://x"
    assert parsed["date_cible"] == "01/01/2024"
    assert parsed["debug_mode"] == "DEBUG"
    assert parsed["liste_items_planning"] == ["a", "b"]
    assert parsed["default_timeout"] == 5
    assert parsed["long_timeout"] == 9


def test__charger_work_schedule_basic():
    parser = configparser.ConfigParser()
    parser.read_dict({"work_schedule": {"monday": "A,B", "tuesday": "C,D"}})
    parsed = AppConfig._charger_work_schedule(parser)
    assert parsed["work_schedule"]["monday"] == ("A", "B")
    assert parsed["work_schedule"]["tuesday"] == ("C", "D")


def test__charger_project_information_basic():
    parser = configparser.ConfigParser()
    parser.read_dict({"project_information": {"project": "X"}})
    parsed = AppConfig._charger_project_information(parser)
    assert parsed["project_information"] == {"project": "X"}


def test__charger_additional_information_basic():
    parser = configparser.ConfigParser()
    parser.read_dict(
        {
            "additional_information_rest_period_respected": {"mon": "Oui"},
            "additional_information_work_time_range": {"mon": "Oui"},
        }
    )
    parsed = AppConfig._charger_additional_information(parser)
    assert parsed["additional_information"]["periode_repos_respectee"]["mon"] == "Oui"
    assert parsed["additional_information"]["horaire_travail_effectif"]["mon"] == "Oui"


def test__charger_work_locations_basic():
    parser = configparser.ConfigParser()
    parser.read_dict(
        {
            "work_location_am": {"mon": "Site"},
            "work_location_pm": {"mon": "Domicile"},
        }
    )
    parsed = AppConfig._charger_work_locations(parser)
    assert parsed["work_location_am"] == {"mon": "Site"}
    assert parsed["work_location_pm"] == {"mon": "Domicile"}


def test__charger_dropdown_options_basic():
    parser = configparser.ConfigParser()
    parser.read_dict(
        {
            "work_location_options": {"values": '"X", "Y"'},
            "cgi_options": {"values": '"O"'},
            "cgi_options_dejeuner": {"values": '"1"'},
            "cgi_options_billing_action": {"Alpha": "A"},
            "work_schedule_options": {"values": '"S1"'},
        }
    )
    parsed = AppConfig._charger_dropdown_options(parser)
    assert [o.label for o in parsed["work_location_options"]] == ["X", "Y"]
    assert [o.label for o in parsed["cgi_options"]] == ["O"]
    assert [o.label for o in parsed["cgi_options_dejeuner"]] == ["1"]
    assert parsed["cgi_options_billing_action"] == [
        BillingActionOption(label="alpha", code="A")
    ]
    assert [o.label for o in parsed["work_schedule_options"]] == ["S1"]
