"""Utility functions for error logging and propagation."""

from sele_saisie_auto.logger_utils import write_log


def log_error(message: str, log_file: str, level: str = "ERROR") -> None:
    """Log an error message using ``logger_utils.write_log``.

    Parameters
    ----------
    message: str
        Text to log.
    log_file: str
        Path to the log file.
    level: str, default "ERROR"
        Logging level.
    """
    write_log(message, log_file, level)


def log_and_raise(exc: Exception, log_file: str, message: str | None = None) -> None:
    """Log the exception then re-raise it.

    Parameters
    ----------
    exc:
        Exception instance to propagate.
    log_file:
        Path to the log file.
    message:
        Optional custom message. If not provided, ``str(exc)`` is used.
    """
    log_msg = f"{message}: {exc}" if message else str(exc)
    log_error(log_msg, log_file)
    raise exc
