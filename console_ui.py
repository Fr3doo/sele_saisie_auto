"""Console utility helpers for user interactions."""

from __future__ import annotations


def ask_continue(prompt: str) -> None:
    """Prompt the user to continue using ``input``."""
    input(prompt)


def show_separator() -> None:
    """Display a separator line in the console."""
    print("*************************************************************")
