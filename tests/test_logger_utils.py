import configparser
import importlib
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

import logger_utils  # noqa: E402


def test_initialize_logger_override(tmp_path):
    mod = importlib.reload(logger_utils)
    cfg = configparser.ConfigParser()
    cfg["settings"] = {"debug_mode": "INFO"}
    mod.initialize_logger(cfg, log_level_override="DEBUG")
    assert mod.LOG_LEVEL_FILTER == "DEBUG"


def test_is_log_level_allowed():
    assert logger_utils.is_log_level_allowed("ERROR", "INFO") is True
    assert logger_utils.is_log_level_allowed("INFO", "ERROR") is False


def test_should_rotate_and_rotate_log_file(tmp_path):
    log_file = tmp_path / "log.html"
    log_file.write_text("x" * (6 * 1024 * 1024), encoding="utf-8")
    assert logger_utils.should_rotate(str(log_file), max_size_mb=5)
    logger_utils.rotate_log_file(str(log_file))
    rotated = list(tmp_path.glob("log.html.*.bak"))
    assert rotated


def test_write_and_close_html_log(tmp_path):
    log_file = tmp_path / "log.html"
    logger_utils.write_log("msg", str(log_file), level="INFO", log_format="html")
    logger_utils.close_logs(str(log_file))
    content = log_file.read_text(encoding="utf-8")
    assert "msg" in content


def test_write_log_text(tmp_path):
    log_file = tmp_path / "log.txt"
    logger_utils.write_log(
        "txt", str(log_file), level="INFO", log_format="txt", auto_close=True
    )
    assert "txt" in log_file.read_text(encoding="utf-8")
