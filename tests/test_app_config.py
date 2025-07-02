import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

from app_config import AppConfig, load_config  # noqa: E402


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
        "read_or_write_file_config_ini_utils.write_log", lambda *a, **k: None
    )

    app_cfg = load_config(str(tmp_path / "log.html"))
    assert isinstance(app_cfg, AppConfig)
    assert app_cfg.url == "http://t"
    assert app_cfg.date_cible == "01/07/2024"
    assert app_cfg.liste_items_planning == ["a", "b"]
    assert app_cfg.raw.get("credentials", "login") == "enc"
    assert app_cfg.cgi_options_billing_action["facturable"] == "B"
