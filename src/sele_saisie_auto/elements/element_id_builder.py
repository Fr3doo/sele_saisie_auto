from __future__ import annotations

"""Utilities for building Selenium element identifiers."""


def build_day_input_id(base_id: str, day_index: int, row_index: int) -> str:
    """Return the identifier for a day input field.

    This helper handles specific patterns used in PSA Time where some day inputs
    follow a different naming scheme. When ``base_id`` contains the substring
    ``"UC_TIME_LIN_WRK_UC_DAILYREST"`` the index must be offset by ``10`` and
    the row index is always ``0``.
    """
    if "UC_TIME_LIN_WRK_UC_DAILYREST" in base_id:
        return f"{base_id}{10 + day_index}$0"
    return f"{base_id}{day_index}${row_index}"
