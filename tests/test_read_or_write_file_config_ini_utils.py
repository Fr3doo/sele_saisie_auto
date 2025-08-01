import builtins
import configparser
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402
from sele_saisie_auto.read_or_write_file_config_ini_utils import (  # noqa: E402
    get_runtime_config_path,
    get_runtime_resource_path,
    read_config_ini,
    write_config_ini,
)


# helper to silence logging
def noop(*args, **kwargs):
    return None


def test_get_runtime_config_path_meipass_copy(tmp_path, monkeypatch):
    embedded = tmp_path / "embedded"
    embedded.mkdir()
    (embedded / "config.ini").write_text("data", encoding="utf-8")
    current = tmp_path / "current"
    current.mkdir()
    monkeypatch.chdir(current)
    monkeypatch.setattr(sys, "_MEIPASS", str(embedded), raising=False)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )
    path = get_runtime_config_path()
    assert Path(path).exists()
    assert Path(path).read_text(encoding="utf-8") == "data"
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)


def test_get_runtime_config_path_no_meipass(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("_MEIPASS", raising=False)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )
    path = get_runtime_config_path()
    assert path == str(tmp_path / "config.ini")


def test_get_runtime_resource_path_copy(tmp_path, monkeypatch):
    embedded = tmp_path / "embedded"
    embedded.mkdir()
    (embedded / "file.png").write_text("img", encoding="utf-8")
    current = tmp_path / "current"
    current.mkdir()
    monkeypatch.chdir(current)
    monkeypatch.setattr(sys, "_MEIPASS", str(embedded), raising=False)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )
    path = get_runtime_resource_path("file.png")
    assert Path(path).exists()
    assert Path(path).read_text(encoding="utf-8") == "img"
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)


def test_get_runtime_resource_path_not_found(tmp_path, monkeypatch):
    embedded = tmp_path / "embedded"
    embedded.mkdir()
    current = tmp_path / "current"
    current.mkdir()
    monkeypatch.chdir(current)
    monkeypatch.setattr(sys, "_MEIPASS", str(embedded), raising=False)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )
    with pytest.raises(FileNotFoundError):
        get_runtime_resource_path("missing.png")
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)


def test_get_runtime_resource_path_permission_error(tmp_path, monkeypatch):
    embedded = tmp_path / "embedded"
    embedded.mkdir()
    (embedded / "file.png").write_text("img", encoding="utf-8")
    current = tmp_path / "current"
    current.mkdir()
    monkeypatch.chdir(current)
    monkeypatch.setattr(sys, "_MEIPASS", str(embedded), raising=False)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.shutil.copy",
        lambda *a, **k: (_ for _ in ()).throw(PermissionError("no")),
    )
    with pytest.raises(PermissionError):
        get_runtime_resource_path("file.png")
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)


def test_get_runtime_config_path_meipass_exists(tmp_path, monkeypatch):
    embedded = tmp_path / "embedded"
    embedded.mkdir()
    (embedded / "config.ini").write_text("new", encoding="utf-8")
    current = tmp_path / "current"
    current.mkdir()
    cfg = current / "config.ini"
    cfg.write_text("orig", encoding="utf-8")
    monkeypatch.chdir(current)
    monkeypatch.setattr(sys, "_MEIPASS", str(embedded), raising=False)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )
    path = get_runtime_config_path()
    assert Path(path).read_text(encoding="utf-8") == "orig"
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)


def test_get_runtime_resource_path_exists(tmp_path, monkeypatch):
    embedded = tmp_path / "embedded"
    embedded.mkdir()
    (embedded / "img.png").write_text("embedded", encoding="utf-8")
    current = tmp_path / "current"
    current.mkdir()
    res = current / "img.png"
    res.write_text("local", encoding="utf-8")
    monkeypatch.chdir(current)
    monkeypatch.setattr(sys, "_MEIPASS", str(embedded), raising=False)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )
    path = get_runtime_resource_path("img.png")
    assert Path(path).read_text(encoding="utf-8") == "local"
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)


def test_get_runtime_resource_path_no_meipass(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("_MEIPASS", raising=False)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )
    path = get_runtime_resource_path("any.png")
    assert path == str(tmp_path / "any.png")


def test_read_config_ini_success(tmp_path, monkeypatch):
    cfg = tmp_path / "config.ini"
    cfg.write_text("[s]\na=b\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )
    config = read_config_ini()
    assert config.get("s", "a") == "b"


def test_read_config_ini_percent_in_log_style(tmp_path, monkeypatch):
    cfg = tmp_path / "config.ini"
    cfg.write_text(
        """[log_style]
column_widths = timestamp:50%, level:25%, message:25%
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )
    config = read_config_ini()
    assert (
        config.get("log_style", "column_widths")
        == "timestamp:50%, level:25%, message:25%"
    )


def test_read_config_ini_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )
    with pytest.raises(FileNotFoundError):
        read_config_ini()


def test_read_config_ini_unicode_error(tmp_path, monkeypatch):
    cfg = tmp_path / "config.ini"
    cfg.write_text("[s]\na=b\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )

    def bad_open(*a, **k):
        raise UnicodeDecodeError("utf-8", b"", 0, 1, "boom")

    monkeypatch.setattr(builtins, "open", bad_open)
    with pytest.raises(TypeError):
        read_config_ini()


def test_read_config_ini_generic_error(tmp_path, monkeypatch):
    cfg = tmp_path / "config.ini"
    cfg.write_text("[s]\na=b\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )

    def bad_open(*a, **k):
        raise ValueError("bad")

    monkeypatch.setattr(builtins, "open", bad_open)
    with pytest.raises(RuntimeError):
        read_config_ini()


def test_read_config_ini_config_error(tmp_path, monkeypatch):
    cfg = tmp_path / "config.ini"
    cfg.write_text("[s]\na=b\n[s]\nc=d\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log",
        noop,
    )
    messages: list[str] = []

    def capture(msg: str, lf: str | None = None) -> None:
        messages.append(msg)

    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info",
        capture,
    )

    with pytest.raises(configparser.Error):
        read_config_ini()
    assert any("s" in m for m in messages)


def test_write_config_ini_success(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.ini"
    cfg_path.write_text("[s]\na=b\n", encoding="utf-8")
    cp = configparser.ConfigParser()
    cp["s"] = {"a": "c"}
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.messagebox.showinfo", noop
    )
    write_config_ini(cp)
    assert "a = c" in cfg_path.read_text(encoding="utf-8")


def test_write_config_ini_not_found(tmp_path, monkeypatch):
    cp = configparser.ConfigParser()
    cp["s"] = {"a": "c"}
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )
    with pytest.raises(FileNotFoundError):
        write_config_ini(cp)


def test_write_config_ini_unicode_error(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.ini"
    cfg_path.write_text("[s]\na=b\n", encoding="utf-8")
    cp = configparser.ConfigParser()
    cp["s"] = {"a": "c"}
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.messagebox.showinfo", noop
    )

    def bad_open(*a, **k):
        raise UnicodeDecodeError("utf-8", b"", 0, 1, "boom")

    monkeypatch.setattr(builtins, "open", bad_open)
    with pytest.raises(TypeError):
        write_config_ini(cp)


def test_write_config_ini_generic_error(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.ini"
    cfg_path.write_text("[s]\na=b\n", encoding="utf-8")
    cp = configparser.ConfigParser()
    cp["s"] = {"a": "c"}
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info", noop
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.messagebox.showinfo", noop
    )

    def bad_open(*a, **k):
        raise ValueError("bad")

    monkeypatch.setattr(builtins, "open", bad_open)
    with pytest.raises(RuntimeError):
        write_config_ini(cp)


def test_read_config_ini_uses_cache(tmp_path, monkeypatch):
    cfg = tmp_path / "config.ini"
    cfg.write_text("[s]\na=b\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.write_log",
        noop,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.read_or_write_file_config_ini_utils.log_info",
        noop,
    )
    opened: list[str] = []
    real_open = builtins.open

    def counting_open(*args, **kwargs):
        opened.append(args[0])
        return real_open(*args, **kwargs)

    monkeypatch.setattr(builtins, "open", counting_open)
    # ensure cache cleared
    from sele_saisie_auto import read_or_write_file_config_ini_utils as mod

    mod.clear_cache()
    first = read_config_ini()
    second = read_config_ini()
    assert first is second
    assert len(opened) == 1
