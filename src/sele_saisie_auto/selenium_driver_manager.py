from __future__ import annotations

"""Backward compatibility wrapper for ``SeleniumDriverManager``."""

from sele_saisie_auto.automation.browser_session import SeleniumDriverManager

# This thin wrapper exists for backward compatibility only.
# pragma: no cover - trivial alias

__all__ = ["SeleniumDriverManager"]
