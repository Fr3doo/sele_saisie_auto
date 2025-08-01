"""Backward compatibility wrapper for ``SeleniumDriverManager``."""

from __future__ import annotations

from sele_saisie_auto.automation.browser_session import SeleniumDriverManager

# This thin wrapper exists for backward compatibility only.

__all__ = ["SeleniumDriverManager"]
