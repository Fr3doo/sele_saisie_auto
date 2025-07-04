import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.app_config import AppConfig, load_config  # noqa: E402


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
    assert app_cfg.cgi_options_billing_action["facturable"] == "B"


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
