"""Example plugin demonstrating hook registration."""
from __future__ import annotations

from plugins import hook


@hook("before_submit")
def notify_before_submit(driver) -> None:
    """Simple hook printing a message before submission."""
    print("Plugin before_submit called")
