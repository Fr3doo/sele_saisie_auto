class Logger:
    """Simple logging wrapper around ``write_log``."""

    def __init__(self, log_file: str | None, log_format: str = "html", writer=None):
        from sele_saisie_auto.logger_utils import write_log as default_write_log

        self.log_file = log_file
        self.log_format = log_format
        self.writer = writer or default_write_log

    def _log(self, level: str, message: str, *, auto_close: bool = False) -> None:
        self.writer(
            message,
            self.log_file,
            level=level,
            log_format=self.log_format,
            auto_close=auto_close,
        )

    def info(self, message: str) -> None:
        self._log("INFO", message)

    def debug(self, message: str) -> None:
        self._log("DEBUG", message)

    def warning(self, message: str) -> None:
        self._log("WARNING", message)

    def error(self, message: str) -> None:
        self._log("ERROR", message)

    def critical(self, message: str) -> None:
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
