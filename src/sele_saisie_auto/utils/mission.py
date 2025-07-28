"""Mission related helper functions."""

from __future__ import annotations

from .date_utils import get_next_saturday_if_not_saturday


def est_en_mission(description: str) -> bool:
    """Return True if the description indicates a mission day."""
    return description == "En mission"


__all__ = ["est_en_mission", "get_next_saturday_if_not_saturday"]
