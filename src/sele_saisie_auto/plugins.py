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


def unregister(name: str, func: Callable[..., Any]) -> None:
    """Remove ``func`` from the list of callbacks for ``name`` if present."""
    callbacks = _HOOKS.get(name)
    if not callbacks:
        return
    try:
        callbacks.remove(func)
        if not callbacks:
            _HOOKS.pop(name, None)
    except ValueError:
        pass


def hook(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator registering a function for a hook."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Ajoute ``func`` au registre des hooks."""
        register(name, func)
        return func

    return decorator


def call(name: str, *args: Any, **kwargs: Any) -> list[Any]:
    """Invoke all functions registered for *name* and collect their results."""
    results: list[Any] = []
    for func in list(_HOOKS.get(name, [])):
        results.append(func(*args, **kwargs))
    return results


def clear() -> None:
    """Remove all registered hooks (useful for testing)."""
    _HOOKS.clear()


__all__ = ["register", "unregister", "hook", "call", "clear"]
