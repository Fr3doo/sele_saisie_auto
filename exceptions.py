"""Custom exception classes for sele_saisie_auto."""

class DriverError(Exception):
    """Raised when the Selenium WebDriver cannot be started."""


class InvalidConfigError(Exception):
    """Raised when configuration values are missing or inconsistent."""

