# src\sele_saisie_auto\interfaces\protocols.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto.app_config import AppConfig

if TYPE_CHECKING:
    from sele_saisie_auto.remplir_jours_feuille_de_temps import (
        TimesheetHelperProtocol as TimeSheetHelperProtocol,
    )
else:

    class TimeSheetHelperProtocol(Protocol):
        def run(self, driver: WebDriver) -> None: ...


@runtime_checkable
class LoggerProtocol(Protocol):
    log_file: str | None

    def info(self, message: str) -> None: ...
    def debug(self, message: str) -> None: ...
    def warning(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...
    def critical(self, message: str) -> None: ...

    def __enter__(self) -> LoggerProtocol: ...

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any
    ) -> None: ...


@runtime_checkable
class WaiterProtocol(Protocol):
    def wait_for_dom_ready(
        self, driver: WebDriver, timeout: int | None = None
    ) -> None: ...

    def wait_until_dom_is_stable(
        self, driver: WebDriver, timeout: int | None = None
    ) -> bool: ...

    def wait_for_element(self, driver: WebDriver, *args: Any, **kwargs: Any) -> Any: ...

    def find_clickable(self, driver: WebDriver, *args: Any, **kwargs: Any) -> Any: ...

    def find_visible(self, driver: WebDriver, *args: Any, **kwargs: Any) -> Any: ...

    def find_present(self, driver: WebDriver, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class BrowserSessionProtocol(Protocol):
    waiter: WaiterProtocol
    app_config: AppConfig | None

    def open(
        self,
        url: str,
        *,
        fullscreen: bool = False,
        headless: bool = False,
        no_sandbox: bool = False,
    ) -> Any: ...
    def close(self) -> None: ...
    def wait_for_dom(self, driver: WebDriver, max_attempts: int = 3) -> None: ...
    def go_to_iframe(self, id_or_name: str) -> bool: ...
    def go_to_default_content(self) -> None: ...
    def click(self, element_id: str) -> bool: ...
    def fill_input(self, element_id: str, value: str) -> bool: ...


@runtime_checkable
class LoginHandlerProtocol(Protocol):
    def connect_to_psatime(
        self,
        driver: WebDriver,
        aes_key: bytes,
        encrypted_login: bytes,
        encrypted_password: bytes,
    ) -> None: ...


@runtime_checkable
class DateEntryPageProtocol(Protocol):
    def navigate_from_home_to_date_entry_page(self, driver: WebDriver) -> bool: ...
    def process_date(self, driver: WebDriver, date_cible: str) -> bool | None: ...
    def submit_date_cible(self, driver: WebDriver) -> bool: ...
<<<<<<< HEAD
    def click_action_button(self, driver: WebDriver) -> None: ...
=======
    def click_creation_mode(self, driver: WebDriver) -> None: ...
>>>>>>> 2d569f5138f633b435a1f9fc6a5b3eb72dad2c33


@runtime_checkable
class AdditionalInfoPageProtocol(Protocol):
    def navigate_from_work_schedule_to_additional_information_page(
        self, driver: WebDriver
    ) -> bool: ...
    def submit_and_validate_additional_information(self, driver: WebDriver) -> bool: ...
    def save_draft_and_validate(self, driver: WebDriver) -> bool: ...
    def log_information_details(self) -> None: ...


__all__ = [
    "LoggerProtocol",
    "WaiterProtocol",
    "BrowserSessionProtocol",
    "LoginHandlerProtocol",
    "DateEntryPageProtocol",
    "AdditionalInfoPageProtocol",
    "TimeSheetHelperProtocol",
]
