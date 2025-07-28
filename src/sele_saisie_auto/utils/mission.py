"""Mission related helper functions."""

from __future__ import annotations

from datetime import datetime, timedelta


def est_en_mission(description: str) -> bool:
    """Return True if the description indicates a mission day."""
    return description == "En mission"


def get_next_saturday_if_not_saturday(date_str: str) -> str:
    """Return the next Saturday if the provided date is not already a Saturday."""
    initial_date = datetime.strptime(date_str, "%d/%m/%Y")
    initial_weekday = initial_date.weekday()
    if initial_weekday != 5:
        days_to_next_saturday = (5 - initial_weekday) % 7
        next_saturday_date = initial_date + timedelta(days=days_to_next_saturday)
        return next_saturday_date.strftime("%d/%m/%Y")
    return date_str


__all__ = ["est_en_mission", "get_next_saturday_if_not_saturday"]
