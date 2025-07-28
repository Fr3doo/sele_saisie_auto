"""Miscellaneous helper functions."""

from __future__ import annotations

import os
import subprocess  # nosec B404
import time

from sele_saisie_auto import shared_utils
from sele_saisie_auto.logger_utils import write_log


def program_break_time(
    memorization_time: int, affichage_text: str, *, log_file: str | None = None
) -> None:
    """Display a short countdown using logging instead of ``print``."""

    log_file = log_file or shared_utils.get_log_file()
    write_log(
        f"{affichage_text} {memorization_time} secondes",
        log_file,
        "DEBUG",
    )
    time.sleep(memorization_time)


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
