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
