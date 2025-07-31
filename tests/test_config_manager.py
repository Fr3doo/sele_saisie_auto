import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.app_config import AppConfig  # noqa: E402
from sele_saisie_auto.config_manager import ConfigManager  # noqa: E402


def test_load_and_save(tmp_path, monkeypatch):
    config_file = tmp_path / "config.ini"
    config_file.write_text(
        """[settings]
url=http://t
[section]
key=value
""",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.messagebox.showinfo",
        lambda *a, **k: None,
    )

    manager = ConfigManager(log_file=str(tmp_path / "log.html"))
    config = manager.load()
    assert isinstance(config, AppConfig)
    assert config.raw.get("section", "key") == "value"

    config.raw.set("section", "key", "new")
    manager.save()

    content = config_file.read_text(encoding="utf-8")
    assert "key = new" in content


def test_config_property_without_load(tmp_path):
    manager = ConfigManager(log_file=str(tmp_path / "log.html"))
    assert not manager.is_loaded
    with pytest.raises(RuntimeError):
        _ = manager.config


def test_save_without_load(tmp_path):
    manager = ConfigManager(log_file=str(tmp_path / "log.html"))
    with pytest.raises(RuntimeError):
        manager.save()


def test_config_property_after_load(tmp_path, monkeypatch):
    config_file = tmp_path / "config.ini"
    config_file.write_text(
        """[settings]
url=http://t
[section]
key=value
""",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.messagebox.showinfo",
        lambda *a, **k: None,
    )

    manager = ConfigManager(log_file=str(tmp_path / "log.html"))
    assert not manager.is_loaded
    config = manager.load()
    assert manager.is_loaded
    assert manager.config == config.raw


def test_load_missing_config(tmp_path, monkeypatch):
    """Crée un fichier par défaut si ``config.ini`` est absent."""
    monkeypatch.chdir(tmp_path)
    logs: list[str] = []
    monkeypatch.setattr(
        "sele_saisie_auto.config_manager.log_info",
        lambda msg, lf=None: logs.append(msg),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log",
        lambda *a, **k: None,
    )

    manager = ConfigManager(log_file=str(tmp_path / "log.html"))
    cfg = manager.load()
    assert (tmp_path / "config.ini").exists()
    assert isinstance(cfg, AppConfig)
    assert any("introuvable" in m.lower() for m in logs)


def test_is_loaded_property(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.ini"
    cfg_file.write_text(
        """[settings]
url=http://t
[section]
key=value
""",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.messagebox.showinfo",
        lambda *a, **k: None,
    )

    manager = ConfigManager(log_file=str(tmp_path / "log.html"))
    assert not manager.is_loaded
    manager.load()
    assert manager.is_loaded


def test_load_minimal_config(tmp_path, monkeypatch):
    """ConfigManager charge un ``config.ini`` minimal."""
    cfg_file = tmp_path / "config.ini"
    cfg_file.write_text(
        """[settings]
url=http://t
""",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.messagebox.showinfo",
        lambda *a, **k: None,
    )

    manager = ConfigManager(log_file=str(tmp_path / "log.html"))
    cfg = manager.load()
    assert isinstance(cfg, AppConfig)
    assert cfg.url == "http://t"


def test_env_vars_override_config(tmp_path, monkeypatch):
    """Les variables d'environnement remplacent ``config.ini``."""
    cfg_file = tmp_path / "config.ini"
    cfg_file.write_text(
        """[settings]
url=http://file
date_cible=01/01/2024
debug_mode=INFO
liste_items_planning="a"
""",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.messagebox.showinfo",
        lambda *a, **k: None,
    )
    monkeypatch.setenv("PSATIME_URL", "http://env")
    monkeypatch.setenv("PSATIME_DATE_CIBLE", "02/02/2024")
    monkeypatch.setenv("PSATIME_DEBUG_MODE", "DEBUG")
    monkeypatch.setenv("PSATIME_LISTE_ITEMS_PLANNING", '"b", "c"')

    manager = ConfigManager(log_file=str(tmp_path / "log.html"))
    cfg = manager.load()
    assert cfg.url == "http://env"
    assert cfg.date_cible == "02/02/2024"
    assert cfg.debug_mode == "DEBUG"
    assert cfg.liste_items_planning == ["b", "c"]
