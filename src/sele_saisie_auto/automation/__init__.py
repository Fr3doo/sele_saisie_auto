"""Subpackage regroupant les automatisations Selenium futures."""

from .browser_session import BrowserSession
from .login_handler import LoginHandler

__all__ = [
    "BrowserSession",
    "LoginHandler",
]
