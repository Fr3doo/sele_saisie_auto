from sele_saisie_auto import logger_utils
from sele_saisie_auto.logging_service import Logger


def test_logger_calls_writer(monkeypatch):
    calls = []

    monkeypatch.setattr(logger_utils, "close_logs", lambda *a, **k: None)

    def writer(msg, log_file, level="INFO", log_format="html", auto_close=False):
        calls.append((level, msg, auto_close))

    with Logger("log.html", writer=writer) as logger:
        logger.info("hello")
        logger.debug("dbg")
        logger.warning("warn")
        logger.error("oops")
        logger.critical("boom")

    assert calls == [
        ("INFO", "hello", False),
        ("DEBUG", "dbg", False),
        ("WARNING", "warn", False),
        ("ERROR", "oops", False),
        ("CRITICAL", "boom", False),
    ]
