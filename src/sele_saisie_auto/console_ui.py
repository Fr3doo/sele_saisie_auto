"""Console utility helpers for user interactions."""

from __future__ import annotations

from sele_saisie_auto import shared_utils
from sele_saisie_auto.logger_utils import show_log_separator


def ask_continue(prompt: str) -> None:
    """Prompt the user to continue using ``input``."""
    input(prompt)


def show_separator() -> None:
    """Log a separator line."""
    show_log_separator(shared_utils.get_log_file(), "DEBUG")
