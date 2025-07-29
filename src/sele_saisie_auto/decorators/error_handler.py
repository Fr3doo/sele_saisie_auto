"""Generic error handling decorator."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from sele_saisie_auto.error_handler import log_error
from sele_saisie_auto.shared_utils import get_log_file


def handle_errors(
    log_file_attr: str = "log_file",
    default_return: Any | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Return a decorator that logs unexpected exceptions and returns ``default_return``."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log_file = kwargs.get("log_file")
            if log_file is None and args:
                inst = args[0]
                # Try attribute on instance directly
                if hasattr(inst, log_file_attr):
                    log_file = getattr(inst, log_file_attr)
                # Fallback to instance.logger.log_file
                elif hasattr(inst, "logger") and hasattr(inst.logger, "log_file"):
                    log_file = getattr(inst.logger, "log_file")
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                lf = log_file or get_log_file()
                log_error(str(exc), lf)
                return default_return

        return wrapper

    return decorator


__all__ = ["handle_errors"]
