"""Example plugin demonstrating hook registration."""

from __future__ import annotations

from sele_saisie_auto import shared_utils
from sele_saisie_auto.logger_utils import write_log
from sele_saisie_auto.plugins import hook


@hook("before_submit")
def notify_before_submit(driver) -> None:
    """Simple hook printing a message before submission."""
    write_log(
        "Plugin before_submit called",
        shared_utils.get_log_file(),
        "DEBUG",
    )
