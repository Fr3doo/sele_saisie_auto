"""Utility helpers around :mod:`sele_saisie_auto.plugins`."""

from __future__ import annotations

from typing import Any

from sele_saisie_auto import plugins

__all__ = ["call_hook"]


def call_hook(name: str, *args: Any, **kwargs: Any) -> None:
    """Invoke hooks registered under ``name`` with the provided arguments."""

    plugins.call(name, *args, **kwargs)
