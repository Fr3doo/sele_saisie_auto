"""Petit système de hooks pour l'automatisation PSA Time."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

_HOOKS: dict[str, list[Callable[..., Any]]] = defaultdict(list)


def register(name: str, func: Callable[..., Any]) -> None:
    """Enregistre ``func`` pour le hook ``name``."""
    _HOOKS[name].append(func)


def unregister(name: str, func: Callable[..., Any]) -> None:
    """Supprime ``func`` du hook ``name`` s'il est présent."""
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
    """Décorateur pour enregistrer une fonction sur un hook."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        register(name, func)
        return func

    return decorator


def call(name: str, *args: Any, **kwargs: Any) -> list[Any]:
    """Appelle toutes les fonctions enregistrées et renvoie leurs résultats."""
    results: list[Any] = []
    for func in list(_HOOKS.get(name, [])):
        results.append(func(*args, **kwargs))
    return results


def clear() -> None:
    """Vide l'ensemble du registre (utile pour les tests)."""
    _HOOKS.clear()


__all__ = ["register", "unregister", "hook", "call", "clear"]
