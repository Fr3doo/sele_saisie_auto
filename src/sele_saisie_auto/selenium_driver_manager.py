"""Backward compatibility wrapper for ``SeleniumDriverManager``."""  # pragma: no cover

from __future__ import annotations

from sele_saisie_auto.automation.browser_session import (
    SeleniumDriverManager,  # pragma: no cover
)

# This thin wrapper exists for backward compatibility only.  # pragma: no cover

__all__ = ["SeleniumDriverManager"]  # pragma: no cover
