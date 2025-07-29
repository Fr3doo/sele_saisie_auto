"""Definitions of HTML id prefixes used for the additional info modal."""

from typing import Dict

# --------------------------------------------------------------------------- #
# Mapping brut id_logique ➜ id_HTML
# --------------------------------------------------------------------------- #
ADDITIONAL_INFO_LOCATORS: Dict[str, str] = {
    "ROW_DESCR100": "DESCR100$",
    "DAY_UC_DAILYREST": "UC_DAILYREST",
    "ROW_DESCR200": "UC_TIME_LIN_WRK_DESCR200$",
    "DAY_UC_DAILYREST_SPECIAL": "UC_TIME_LIN_WRK_UC_DAILYREST",
    "ROW_DESCR": "DESCR$",
    "DAY_UC_LOCATION_A": "UC_LOCATION_A",
}


# For backward compatibility ------------------------------------------------- #
LOCATOR_MAP = ADDITIONAL_INFO_LOCATORS
