import configparser
import importlib
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto import logger_utils  # noqa: E402
from sele_saisie_auto.enums import LogLevel  # noqa: E402
from sele_saisie_auto.exceptions import InvalidConfigError  # noqa: E402


def test_initialize_logger_override(tmp_path):
    mod = importlib.reload(logger_utils)
    cfg = configparser.ConfigParser()
    cfg["settings"] = {"debug_mode": "INFO"}
    mod.initialize_logger(cfg, log_level_override=LogLevel.DEBUG)
    assert mod.LOG_LEVEL_FILTER == LogLevel.DEBUG


def test_is_log_level_allowed():
    assert logger_utils.is_log_level_allowed(LogLevel.ERROR, LogLevel.INFO) is True
    assert logger_utils.is_log_level_allowed(LogLevel.INFO, LogLevel.ERROR) is False


def test_format_message():
    assert logger_utils.format_message("BROWSER_OPEN", {}) == "Ouverture du navigateur"


def test_format_message_unknown():
    with pytest.raises(KeyError):
        logger_utils.format_message("BOGUS", {})


def test_write_and_close_html_log(tmp_path):
    log_file = tmp_path / "log.html"
    logger_utils.write_log("msg", str(log_file), level=LogLevel.INFO, log_format="html")
    logger_utils.close_logs(str(log_file))
    content = log_file.read_text(encoding="utf-8")
    assert "msg" in content


def test_write_log_text(tmp_path):
    log_file = tmp_path / "log.txt"
    logger_utils.write_log(
        "txt", str(log_file), level=LogLevel.INFO, log_format="txt", auto_close=True
    )
    assert "txt" in log_file.read_text(encoding="utf-8")


def test_initialize_logger_config_value(tmp_path):
    mod = importlib.reload(logger_utils)
    cfg = configparser.ConfigParser()
    cfg["settings"] = {"debug_mode": "WARNING"}
    mod.initialize_logger(cfg)
    assert mod.LOG_LEVEL_FILTER == LogLevel.WARNING


def test_initialize_logger_invalid_string(tmp_path):
    mod = importlib.reload(logger_utils)
    cfg = configparser.ConfigParser()
    cfg["settings"] = {"debug_mode": "INFO"}
    mod.initialize_logger(cfg, log_level_override="BOGUS")
    assert mod.LOG_LEVEL_FILTER == LogLevel.INFO


def test_initialize_logger_invalid_config(tmp_path):
    mod = importlib.reload(logger_utils)
    cfg = configparser.ConfigParser()
    cfg["settings"] = {"debug_mode": "BAD"}
    mod.initialize_logger(cfg, log_file=str(tmp_path / "log.html"))
    assert mod.LOG_LEVEL_FILTER == LogLevel.INFO


def test_initialize_logger_override_and_config_invalid(tmp_path):
    mod = importlib.reload(logger_utils)
    cfg = configparser.ConfigParser()
    cfg["settings"] = {"debug_mode": "BAD"}
    log_file = tmp_path / "log.html"
    mod.initialize_logger(cfg, log_level_override="BOGUS", log_file=str(log_file))
    assert mod.LOG_LEVEL_FILTER == LogLevel.INFO
    assert "Invalid log level" in log_file.read_text(encoding="utf-8")


def test_initialize_html_log_file_cleanup(tmp_path):
    log_file = tmp_path / "log.html"
    log_file.write_text("</table></body></html>", encoding="utf-8")
    logger_utils.initialize_html_log_file(str(log_file))
    assert "</table></body></html>" not in log_file.read_text(encoding="utf-8")


def test_initialize_html_log_file_no_cleanup(tmp_path):
    log_file = tmp_path / "log.html"
    log_file.write_text("<table>", encoding="utf-8")
    logger_utils.initialize_html_log_file(str(log_file))
    assert log_file.read_text(encoding="utf-8") == "<table>"


def test_write_log_invalid_level(tmp_path):
    log_file = tmp_path / "log.html"
    logger_utils.write_log("x", str(log_file), level="BOGUS", log_format="html")
    assert not log_file.exists()


def test_write_log_filtered(monkeypatch, tmp_path):
    log_file = tmp_path / "log.html"
    logger_utils.LOG_LEVEL_FILTER = LogLevel.INFO
    logger_utils.write_log(
        "msg", str(log_file), level=LogLevel.ERROR, log_format="html"
    )
    assert not log_file.exists()
    logger_utils.LOG_LEVEL_FILTER = logger_utils.DEFAULT_LOG_LEVEL
    logger_utils.write_log(
        "msg", str(log_file), level=LogLevel.ERROR, log_format="html"
    )


def test_write_log_debug_html_autoclose(monkeypatch, tmp_path):
    log_file = tmp_path / "log.html"
    logger_utils.LOG_LEVEL_FILTER = LogLevel.INFO
    logger_utils.write_log(
        "hello", str(log_file), level=LogLevel.INFO, log_format="html", auto_close=True
    )
    content = log_file.read_text(encoding="utf-8")
    assert content.endswith("</table></body></html>")
    logger_utils.LOG_LEVEL_FILTER = logger_utils.DEFAULT_LOG_LEVEL


def test_write_log_text_debug(monkeypatch, tmp_path):
    log_file = tmp_path / "log.txt"
    logger_utils.LOG_LEVEL_FILTER = LogLevel.INFO
    logger_utils.write_log("hi", str(log_file), level=LogLevel.INFO, log_format="txt")
    assert "hi" in log_file.read_text(encoding="utf-8")
    logger_utils.LOG_LEVEL_FILTER = logger_utils.DEFAULT_LOG_LEVEL


def test_write_log_oserror(monkeypatch, tmp_path):
    log_file = tmp_path / "log.html"

    def bad_open(*a, **k):
        raise OSError("boom")

    monkeypatch.setattr(logger_utils, "initialize_html_log_file", lambda *a, **k: None)
    monkeypatch.setattr("builtins.open", bad_open)
    with pytest.raises(OSError):
        logger_utils.write_log(
            "msg", str(log_file), level=LogLevel.INFO, log_format="html"
        )


def test_close_logs_no_file(tmp_path):
    logger_utils.close_logs(str(tmp_path / "no.html"))


def test_close_logs_error(monkeypatch, tmp_path):
    log_file = tmp_path / "log.html"
    log_file.write_text("<table>", encoding="utf-8")

    def bad_open(*a, **k):
        raise OSError("fail")

    monkeypatch.setattr("builtins.open", bad_open)
    with pytest.raises(OSError):
        logger_utils.close_logs(str(log_file))


def test_write_log_generic_exception(monkeypatch, tmp_path):
    log_file = tmp_path / "log.html"
    monkeypatch.setattr(logger_utils, "initialize_html_log_file", lambda *a, **k: None)

    def raise_value(*a, **k):
        raise ValueError("oops")

    monkeypatch.setattr("builtins.open", raise_value)
    with pytest.raises(RuntimeError):
        logger_utils.write_log(
            "msg", str(log_file), level=LogLevel.INFO, log_format="html"
        )


def test_close_logs_already_closed(tmp_path):
    log_file = tmp_path / "log.html"
    log_file.write_text("</table></body></html>", encoding="utf-8")
    logger_utils.close_logs(str(log_file))
    content = log_file.read_text(encoding="utf-8")
    assert content.endswith("</table></body></html>")


def test_close_logs_no_double_closure(tmp_path):
    first = tmp_path / "first.html"
    first.write_text("<table>", encoding="utf-8")
    second = tmp_path / "second.html"
    second.write_text("</table></body></html>", encoding="utf-8")
    logger_utils.close_logs(str(first))
    logger_utils.close_logs(str(second))
    assert first.read_text(encoding="utf-8").count("</table></body></html>") == 1
    assert second.read_text(encoding="utf-8").count("</table></body></html>") == 1


def test_close_logs_generic_error(monkeypatch, tmp_path):
    log_file = tmp_path / "log.html"
    log_file.write_text("<table>", encoding="utf-8")

    def raise_value(*a, **k):
        raise ValueError("bad")

    monkeypatch.setattr("builtins.open", raise_value)
    with pytest.raises(RuntimeError):
        logger_utils.close_logs(str(log_file))


def test_get_html_style_from_config(tmp_path, monkeypatch):
    cfg = tmp_path / "config.ini"
    cfg.write_text(
        """[log_style]
column_widths = timestamp:30%, level:20%, message:50%
row_height = 30px
font_size = 16px
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    style = logger_utils.get_html_style()
    assert "30%" in style
    assert "height: 30px" in style
    assert "font-size: 16px" in style


def test_get_html_style_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    style = logger_utils.get_html_style()
    assert "width: 10%" in style


def test_parse_column_widths():
    widths = logger_utils._parse_column_widths("timestamp:11%, level:22%, message:33%")
    assert widths["level"] == "22%"


def test_validate_log_style_unknown_key(tmp_path, monkeypatch):
    cfg = tmp_path / "config.ini"
    cfg.write_text(
        """[log_style]
bogus = 1
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    with pytest.raises(InvalidConfigError):
        logger_utils.get_html_style()


def test_validate_log_style_bad_width(tmp_path, monkeypatch):
    cfg = tmp_path / "config.ini"
    cfg.write_text(
        """[log_style]
column_widths = timestamp10%
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    with pytest.raises(InvalidConfigError):
        logger_utils.get_html_style()


def test_validate_log_style_missing_value():
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string("[log_style]\ncolumn_widths=timestamp:10%,level")
    with pytest.raises(InvalidConfigError):
        logger_utils.validate_log_style(parser)
