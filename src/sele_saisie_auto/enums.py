from __future__ import annotations

from enum import Enum


class LogLevel(str, Enum):
    """Available log levels for the application."""

    INFO = "INFO"
    DEBUG = "DEBUG"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    OFF = "OFF"


class AlertType(str, Enum):
    """Types of alerts that can be handled."""

    SAVE_ALERTS = "save_alerts"
    DATE_ALERT = "date_alert"


class MissionField(str, Enum):
    """Fields related to project information for a mission."""

    PROJECT_CODE = ("PROJECT_CODE$0", "project_code")
    ACTIVITY_CODE = ("ACTIVITY_CODE$0", "activity_code")
    CATEGORY_CODE = ("CATEGORY_CODE$0", "category_code")
    SUB_CATEGORY_CODE = ("SUB_CATEGORY_CODE$0", "sub_category_code")
    BILLING_ACTION = ("BILLING_ACTION$0", "billing_action")

    config_key: str

    def __new__(cls, field_id: str, config_key: str) -> "MissionField":
        obj = str.__new__(cls, field_id)
        obj._value_ = field_id
        obj.config_key = config_key
        return obj


class AlertMessage(str, Enum):
    """Message codes used when handling alerts."""

    TIME_SHEET_EXISTS_ERROR = "TIME_SHEET_EXISTS_ERROR"
    MODIFY_DATE_MESSAGE = "MODIFY_DATE_MESSAGE"
    SAVE_ALERT_WARNING = "SAVE_ALERT_WARNING"
    DATE_VALIDATED = "DATE_VALIDATED"
