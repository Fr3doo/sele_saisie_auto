"""Minimal plugin registry for PSA Time automation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

# Map of hook name to registered callables
_HOOKS: dict[str, list[Callable[..., Any]]] = defaultdict(list)


def register(name: str, func: Callable[..., Any]) -> None:
    """Register *func* to be called for the hook *name*."""
    _HOOKS[name].append(func)


def hook(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator registering a function for a hook."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Ajoute ``func`` au registre des hooks."""
        register(name, func)
        return func

    return decorator


def call(name: str, *args: Any, **kwargs: Any) -> None:
    """Invoke all functions registered for *name*."""
    for func in list(_HOOKS.get(name, [])):
        func(*args, **kwargs)


def clear() -> None:
    """Remove all registered hooks (useful for testing)."""
    _HOOKS.clear()


__all__ = ["register", "hook", "call", "clear"]
