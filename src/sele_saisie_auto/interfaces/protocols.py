# pragma: no cover
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from sele_saisie_auto.app_config import AppConfig


@runtime_checkable
class LoggerProtocol(Protocol):
    log_file: str | None

    def info(self, message: str) -> None: ...
    def debug(self, message: str) -> None: ...
    def warning(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...
    def critical(self, message: str) -> None: ...

    def __enter__(self) -> "LoggerProtocol": ...

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any
    ) -> None: ...


@runtime_checkable
class WaiterProtocol(Protocol):
    def wait_for_dom_ready(self, driver, timeout: int | None = None) -> None: ...
    def wait_until_dom_is_stable(self, driver, timeout: int | None = None) -> bool: ...
    def wait_for_element(self, driver, *args, **kwargs): ...
    def find_clickable(self, driver, *args, **kwargs): ...
    def find_visible(self, driver, *args, **kwargs): ...
    def find_present(self, driver, *args, **kwargs): ...


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
    ): ...
    def close(self) -> None: ...
    def wait_for_dom(self, driver) -> None: ...
    def go_to_iframe(self, id_or_name: str) -> bool: ...
    def go_to_default_content(self) -> None: ...


@runtime_checkable
class LoginHandlerProtocol(Protocol):
    def connect_to_psatime(
        self, driver, aes_key: bytes, encrypted_login: bytes, encrypted_password: bytes
    ) -> None: ...


@runtime_checkable
class DateEntryPageProtocol(Protocol):
    def navigate_from_home_to_date_entry_page(self, driver) -> bool: ...
    def process_date(self, driver, date_cible) -> bool | None: ...
    def submit_date_cible(self, driver): ...


@runtime_checkable
class AdditionalInfoPageProtocol(Protocol):
    def navigate_from_work_schedule_to_additional_information_page(self, driver): ...
    def submit_and_validate_additional_information(self, driver): ...
    def save_draft_and_validate(self, driver): ...


@runtime_checkable
class TimeSheetHelperProtocol(Protocol):
    def run(self, driver) -> None: ...


__all__ = [
    "LoggerProtocol",
    "WaiterProtocol",
    "BrowserSessionProtocol",
    "LoginHandlerProtocol",
    "DateEntryPageProtocol",
    "AdditionalInfoPageProtocol",
    "TimeSheetHelperProtocol",
]
