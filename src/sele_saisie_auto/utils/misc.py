"""Miscellaneous helper functions."""

from __future__ import annotations

import os
import subprocess  # nosec B404
import time


def program_break_time(memorization_time: int, affichage_text: str) -> None:
    """Display a short countdown in the console."""
    print(f"{affichage_text} {memorization_time} secondes ", end="", flush=True)
    for _ in range(memorization_time):
        time.sleep(1)
        print(".", end="", flush=True)


def clear_screen() -> None:
    """Clear console output."""
    cmd = "cls" if os.name == "nt" else "clear"
    subprocess.run(
        cmd,
        shell=True,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )  # nosec B603 B607 B602
