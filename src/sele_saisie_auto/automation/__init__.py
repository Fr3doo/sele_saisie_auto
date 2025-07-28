"""Subpackage regroupant les automatisations Selenium futures."""

from .additional_info_page import AdditionalInfoPage
from .browser_session import BrowserSession, create_session
from .date_entry_page import DateEntryPage
from .login_handler import LoginHandler

__all__ = [
    "BrowserSession",
    "create_session",
    "LoginHandler",
    "DateEntryPage",
    "AdditionalInfoPage",
]
