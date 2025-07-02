import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

from config_manager import ConfigManager  # noqa: E402


def test_load_and_save(tmp_path, monkeypatch):
    config_file = tmp_path / "config.ini"
    config_file.write_text("[section]\nkey=value\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "read_or_write_file_config_ini_utils.messagebox.showinfo",
        lambda *a, **k: None,
    )

    manager = ConfigManager(log_file=str(tmp_path / "log.html"))
    config = manager.load()
    assert config.get("section", "key") == "value"

    config.set("section", "key", "new")
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
        "read_or_write_file_config_ini_utils.messagebox.showinfo",
        lambda *a, **k: None,
    )

    manager = ConfigManager(log_file=str(tmp_path / "log.html"))
    config = manager.load()
    assert manager.config == config
