import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.app_config import AppConfig  # noqa: E402
from sele_saisie_auto.config_manager import ConfigManager  # noqa: E402


def test_load_and_save(tmp_path, monkeypatch):
    config_file = tmp_path / "config.ini"
    config_file.write_text("[section]\nkey=value\n", encoding="utf-8")

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
    with pytest.raises(RuntimeError):
        _ = manager.config


def test_save_without_load(tmp_path):
    manager = ConfigManager(log_file=str(tmp_path / "log.html"))
    with pytest.raises(RuntimeError):
        manager.save()


def test_config_property_after_load(tmp_path, monkeypatch):
    config_file = tmp_path / "config.ini"
    config_file.write_text("[section]\nkey=value\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.messagebox.showinfo",
        lambda *a, **k: None,
    )

    manager = ConfigManager(log_file=str(tmp_path / "log.html"))
    config = manager.load()
    assert manager.config == config.raw


def test_load_missing_config(tmp_path, monkeypatch):
    """Vérifie qu'une erreur explicite est levée si ``config.ini`` manque."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.messagebox.showinfo",
        lambda *a, **k: None,
    )
    manager = ConfigManager(log_file=str(tmp_path / "log.html"))
    with pytest.raises(FileNotFoundError):
        manager.load()
