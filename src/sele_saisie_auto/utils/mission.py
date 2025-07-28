"""Mission related helper functions."""

from __future__ import annotations


def est_en_mission(description: str) -> bool:
    """Return True if the description indicates a mission day."""
    return description == "En mission"
