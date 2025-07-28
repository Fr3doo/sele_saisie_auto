from enum import Enum, auto
from typing import Any, Dict, List

# --------------------------------------------------------------------------- #
# Mapping brut id_logique ➜ id_HTML
# --------------------------------------------------------------------------- #
LOCATOR_MAP: Dict[str, str] = {
    "ROW_DESCR100": "DESCR100$",
    "DAY_UC_DAILYREST": "UC_DAILYREST",
    "ROW_DESCR200": "UC_TIME_LIN_WRK_DESCR200$",
    "DAY_UC_DAILYREST_SPECIAL": "UC_TIME_LIN_WRK_UC_DAILYREST",
    "ROW_DESCR": "DESCR$",
    "DAY_UC_LOCATION_A": "UC_LOCATION_A",
}


class AdditionalInfoLocators(str, Enum):
    """Locator prefixes for additional information lines and fields."""

    @staticmethod
    def _generate_next_value_(
        name: str,
        start: int,
        count: int,
        last_values: List[Any],
    ) -> str:
        return LOCATOR_MAP[name]

    ROW_DESCR100 = auto()
    DAY_UC_DAILYREST = auto()
    ROW_DESCR200 = auto()
    DAY_UC_DAILYREST_SPECIAL = auto()
    ROW_DESCR = auto()
    DAY_UC_LOCATION_A = auto()
