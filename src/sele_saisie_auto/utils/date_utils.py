"""Utilities for date-related calculations."""

from __future__ import annotations

from datetime import datetime, timedelta


def get_next_saturday_if_not_saturday(date_str: str) -> str:
    """Return the next Saturday if the provided date is not already a Saturday."""
    initial_date = datetime.strptime(date_str, "%d/%m/%Y")
    initial_weekday = initial_date.weekday()
    if initial_weekday != 5:
        days_to_next_saturday = (5 - initial_weekday) % 7
        next_saturday_date = initial_date + timedelta(days=days_to_next_saturday)
        return next_saturday_date.strftime("%d/%m/%Y")
    return date_str


__all__ = ["get_next_saturday_if_not_saturday"]
