"""Strategy helpers to fill Selenium elements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from selenium.webdriver.support.ui import Select

from sele_saisie_auto.logging_service import Logger


class ElementFillingStrategy(ABC):
    """Interface for strategies inserting ``value`` into ``element``."""

    @abstractmethod
    def fill(self, element: Any, value: str, logger: Logger | None = None) -> None:
        """Fill ``element`` with ``value``."""
        raise NotImplementedError


class SelectFillingStrategy(ElementFillingStrategy):
    """Strategy for ``<select>`` elements."""

    def fill(self, element: Any, value: str, logger: Logger | None = None) -> None:
        selector = Select(element)
        selector.select_by_visible_text(value)
        if logger:
            logger.debug(f"Option '{value}' sélectionnée.")


class InputFillingStrategy(ElementFillingStrategy):
    """Strategy for text input fields."""

    def fill(self, element: Any, value: str, logger: Logger | None = None) -> None:
        element.clear()
        element.send_keys(value)
        if logger:
            logger.debug(f"Valeur '{value}' insérée dans le champ.")


class ElementFillingContext:
    """Execute a filling strategy on elements."""

    def __init__(self, strategy: ElementFillingStrategy | None = None) -> None:
        self.strategy = strategy or InputFillingStrategy()

    def set_strategy(self, strategy: ElementFillingStrategy) -> None:
        """Change the underlying strategy."""
        self.strategy = strategy

    def fill(self, element: Any, value: str, logger: Logger | None = None) -> None:
        """Fill ``element`` using the configured strategy."""
        if not self.strategy:
            raise RuntimeError("No filling strategy configured")
        self.strategy.fill(element, value, logger)
