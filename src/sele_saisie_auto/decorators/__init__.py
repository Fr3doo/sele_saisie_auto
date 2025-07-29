"""Decorators utilities for error handling, etc."""

from .error_handler import handle_errors
from .error_handling import handle_selenium_errors

__all__ = ["handle_selenium_errors", "handle_errors"]
