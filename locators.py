from enum import Enum


class Locators(str, Enum):
    """Central Selenium locators used across modules."""

    USERNAME = "userid"
    PASSWORD = "pwd"
    MAIN_FRAME = "main_target_win0"
    NAV_TO_DATE_ENTRY = "PTNUI_LAND_REC14$0_row_0"
    SIDE_MENU_BUTTON = "PT_SIDE$PIMG"
    DATE_INPUT = "EX_TIME_ADD_VW_PERIOD_END_DT"
    ADD_BUTTON = "PTS_CFG_CL_WRK_PTS_ADD_BTN"
    ADDITIONAL_INFO_LINK = "UC_EX_WRK_UC_TI_FRA_LINK"
    MODAL_FRAME = "ptModFrame_0"
    SAVE_ICON = "#ICSave"
    SAVE_DRAFT_BUTTON = "EX_ICLIENT_WRK_SAVE_PB"
    CONFIRM_OK = "#ICOK"
    OK_BUTTON = "EX_ICLIENT_WRK_OK_PB"
    COPY_TIME_BUTTON = "EX_TIME_HDR_WRK_COPY_TIME_RPT"
    ALERT_CONTENT_0 = "ptModContent_0"
    ALERT_CONTENT_1 = "ptModContent_1"
    ALERT_CONTENT_2 = "ptModContent_2"
    ALERT_CONTENT_3 = "ptModContent_3"
