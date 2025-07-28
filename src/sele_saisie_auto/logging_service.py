# pragma: no cover
from __future__ import annotations

from configparser import ConfigParser
from typing import Callable, Literal, Protocol

LogFormat = Literal["html", "txt"]


# Signature minimale acceptée pour la fonction d'écriture
class _Writer(Protocol):
    def __call__(
        self,
        message: str,
        log_file: str,
        *,
        level: str,
        log_format: LogFormat,
        auto_close: bool = False,
    ) -> None: ...


class Logger:
    """Simple logging wrapper around ``write_log``."""

    def __init__(
        self,
        log_file: str | None = None,
        log_format: LogFormat = "html",
        writer: _Writer | None = None,
    ) -> None:
        """Initialise le logger.

        Args:
            log_file: Chemin du fichier log.
            log_format: Format du fichier log (``html`` par défaut).
            writer: Fonction d'écriture, ``write_log`` si ``None``.
        """
        from sele_saisie_auto.logger_utils import write_log as default_write_log

        self.log_file: str = log_file if log_file else ""
        """Chemin du fichier de log."""
        self.log_format: LogFormat = log_format
        self.writer: _Writer = writer or default_write_log

    def _log(self, level: str, message: str, *, auto_close: bool = False) -> None:
        """Écrit un message au niveau spécifié."""
        self.writer(
            message,
            self.log_file,
            level=level,
            log_format=self.log_format,
            auto_close=auto_close,
        )

    def info(self, message: str) -> None:
        """Journalise au niveau ``INFO``."""
        self._log("INFO", message)

    def debug(self, message: str) -> None:
        """Journalise au niveau ``DEBUG``."""
        self._log("DEBUG", message)

    def warning(self, message: str) -> None:
        """Journalise au niveau ``WARNING``."""
        self._log("WARNING", message)

    def error(self, message: str) -> None:
        """Journalise au niveau ``ERROR``."""
        self._log("ERROR", message)

    def critical(self, message: str) -> None:
        """Journalise au niveau ``CRITICAL``."""
        self._log("CRITICAL", message)

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------

    def __enter__(self) -> "Logger":
        """Prepare the log file when used as a context manager."""
        from sele_saisie_auto.logger_utils import initialize_html_log_file

        if self.log_file:
            initialize_html_log_file(self.log_file)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> None:
        """Ensure the log file is closed properly."""
        from sele_saisie_auto.logger_utils import close_logs

        if self.log_file:
            close_logs(self.log_file, log_format=self.log_format)


_LOGGERS: dict[str, Logger] = {}

from sele_saisie_auto.shared_utils import get_log_file  # noqa: E402


def get_logger(log_file: str | None) -> Logger:
    """Return a :class:`Logger` instance for ``log_file``.

    The same instance is returned for identical ``log_file`` values so
    that modules share a single logger per file.
    """

    lf: str = log_file or get_log_file()
    if lf not in _LOGGERS:
        _LOGGERS[lf] = Logger(lf)
    return _LOGGERS[lf]


class LoggingConfigurator:
    """Utility to configure global logging for the application."""

    @staticmethod
    def setup(log_file: str, debug_mode: str | None, config: ConfigParser) -> None:
        """Configure logging for Selenium helpers and the logger utils."""

        from sele_saisie_auto.logger_utils import initialize_logger
        from sele_saisie_auto.selenium_utils import (
            set_log_file as set_log_file_selenium,
        )

        set_log_file_selenium(log_file)

        if isinstance(config, ConfigParser):
            initialize_logger(config, log_level_override=debug_mode)
