from enum import Enum


class AdditionalInfoLocators(str, Enum):
    """Locator prefixes for additional information lines and fields."""

    ROW_DESCR100 = "DESCR100$"
    DAY_UC_DAILYREST = "UC_DAILYREST"
    ROW_DESCR200 = "UC_TIME_LIN_WRK_DESCR200$"
    DAY_UC_DAILYREST_SPECIAL = "UC_TIME_LIN_WRK_UC_DAILYREST"
    ROW_DESCR = "DESCR$"
    DAY_UC_LOCATION_A = "UC_LOCATION_A"
