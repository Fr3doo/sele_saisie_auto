import types
from configparser import ConfigParser
from pathlib import Path
from unittest.mock import Mock, call

import pytest

from sele_saisie_auto.automation.browser_session import BrowserSession
from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.memory_config import MemoryConfig
from sele_saisie_auto.shared_memory_service import SharedMemoryService


class DummyLogger:
    """Simple logger collecting messages."""

    def __init__(self):
        self.records = {"info": [], "debug": [], "warning": [], "error": []}

    def info(self, msg):
        self.records["info"].append(msg)

    def debug(self, msg):
        self.records["debug"].append(msg)

    def warning(self, msg):
        self.records["warning"].append(msg)

    def error(self, msg):
        self.records["error"].append(msg)


@pytest.fixture
def dummy_logger():
    """Return a fresh DummyLogger instance."""
    return DummyLogger()


@pytest.fixture
def sample_config():
    """Load the minimal example configuration."""
    cfg = ConfigParser()
    path = Path(__file__).resolve().parents[1] / "examples" / "config_minimal.ini"
    cfg.read(path, encoding="utf-8")
    cfg["settings"]["url"] = "http://test"
    return cfg


class FakeEncryptionService:
    """Lightweight encryption stub used in integration tests."""

    def __init__(self, log_file: str | None = None) -> None:
        self.log_file = log_file
        self.cle_aes = b"k" * 32
        self.removed: list[object] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def retrieve_credentials(self):
        from sele_saisie_auto.encryption_utils import Credentials

        return Credentials(
            aes_key=self.cle_aes,
            mem_key=object(),
            login=b"user",
            mem_login=object(),
            password=b"pass",
            mem_password=object(),
        )

    def dechiffrer_donnees(self, data, key):
        return data.decode() if isinstance(data, bytes) else data

    def supprimer_memoire_partagee_securisee(self, mem):
        self.removed.append(mem)

    # New helper mirroring production API
    def remove_shared_memory(self, mem):
        self.supprimer_memoire_partagee_securisee(mem)


@pytest.fixture
def service_factory():
    def _factory(
        mock_service: Mock, mem_cfg: MemoryConfig, expected_key: bytes
    ) -> EncryptionService:
        service = EncryptionService(
            shared_memory_service=mock_service, memory_config=mem_cfg
        )
        service.generer_cle_aes = Mock(return_value=expected_key)
        return service

    return _factory


def assert_call_sequence(mock: Mock, *expected: call) -> None:
    assert mock.call_args_list == list(expected)


def assert_call_prefix(mock: Mock, *expected: call) -> None:
    assert mock.mock_calls[: len(expected)] == list(expected)


def store_setup(mem_cfg: MemoryConfig, service_factory):
    expected_key = b"k" * mem_cfg.key_size
    mem_key = object()
    mem_login = object()
    mem_pwd = object()
    login_blob = b"login-data"
    pwd_blob = b"pwd-data"
    mock_service = Mock(spec=SharedMemoryService)
    mock_service.stocker_en_memoire_partagee.side_effect = [
        mem_key,
        mem_login,
        mem_pwd,
    ]
    service = service_factory(mock_service, mem_cfg, expected_key)
    return (
        service,
        mock_service,
        expected_key,
        mem_key,
        mem_login,
        mem_pwd,
        login_blob,
        pwd_blob,
    )


# ----------------------------
# Common test stubs
# ----------------------------


class DummyBrowserSession(BrowserSession):
    """Lightweight browser session stub."""

    def __init__(self):
        # Intentionally bypass BrowserSession.__init__ to avoid side effects
        self.log_file = "log.html"
        self.app_config = None
        self.open_calls = []
        self.driver = "drv"
        self.waiter = types.SimpleNamespace(wait_for_element=lambda *a, **k: True)
        self.clicked = []
        self.filled = []

    def wait_for_dom(self, driver, max_attempts: int = 3):
        self.wait_called = True

    def go_to_iframe(self, frame_id):
        self.iframe_called = frame_id
        return True

    def open(self, url, headless=False, no_sandbox=False):
        self.open_calls.append((url, headless, no_sandbox))
        return self.driver

    def go_to_default_content(self):
        self.default_called = True

    def click(self, element_id):
        self.clicked.append(element_id)
        return True

    def fill_input(self, element_id, value):
        self.filled.append((element_id, value))
        return True

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


class DummySession:
    """Minimal session stub used by PageNavigator tests."""

    def __init__(self):
        self.calls = []

    def click(self, element_id):
        self.calls.append(f"click:{element_id}")
        return True

    def fill_input(self, element_id, value):
        self.calls.append(f"fill:{element_id}:{value}")
        return True

    def go_to_default_content(self):
        self.calls.append("default")


class DummyLoginHandler:
    def __init__(self):
        self.calls = []

    def connect_to_psatime(self, driver, key, login, pwd):
        self.calls.append((driver, key, login, pwd))


class DummyDateEntryPage:
    def __init__(self):
        self.calls = []

    def navigate_from_home_to_date_entry_page(self, driver):
        self.calls.append("nav")
        return True

    def process_date(self, driver, date):
        self.calls.append(("date", date))

    def click_action_button(self, driver):
        self.calls.append("click")

    def submit_date_cible(self, driver):
        self.calls.append("submit")


class DummyAdditionalInfoPage:
    def __init__(self):
        self.calls = []

    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        self.calls.append("nav_add")

    def submit_and_validate_additional_information(self, driver):
        self.calls.append("submit_add")

    def save_draft_and_validate(self, driver):
        self.calls.append("save")

    def log_information_details(self):
        self.calls.append("log_info")


class DummyTimeSheetHelper:
    ran = None

    def __init__(
        self, *args, additional_info_page=None, browser_session=None, **kwargs
    ):
        self.calls = []
        self.additional_info_page = additional_info_page
        self.browser_session = browser_session

    def run(self, driver):
        self.__class__.ran = driver
        self.calls.append(driver)
        if self.additional_info_page is not None:
            self.additional_info_page.navigate_from_work_schedule_to_additional_information_page(
                driver
            )
            self.additional_info_page.submit_and_validate_additional_information(driver)
        if self.browser_session is not None:
            self.browser_session.go_to_default_content()


class LoggedDummyLoginHandler(DummyLoginHandler):
    def __init__(self, log):
        super().__init__()
        self.log = log

    def connect_to_psatime(self, driver, key, login, pwd):
        super().connect_to_psatime(driver, key, login, pwd)
        self.log.append("login")


class LoggedDummyDateEntryPage(DummyDateEntryPage):
    def __init__(self, log):
        super().__init__()
        self.log = log

    def navigate_from_home_to_date_entry_page(self, driver):
        result = super().navigate_from_home_to_date_entry_page(driver)
        self.log.append("navigate")
        return result

    def process_date(self, driver, date):
        super().process_date(driver, date)
        self.log.append("process")


class LoggedDummyAdditionalInfoPage(DummyAdditionalInfoPage):
    def __init__(self, log):
        super().__init__()
        self.log = log

    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        super().navigate_from_work_schedule_to_additional_information_page(driver)
        self.log.append("nav_add")

    def submit_and_validate_additional_information(self, driver):
        super().submit_and_validate_additional_information(driver)
        self.log.append("submit_add")

    def save_draft_and_validate(self, driver):
        super().save_draft_and_validate(driver)
        self.log.append("save")

    def log_information_details(self):
        super().log_information_details()
        self.log.append("log_info")


class LoggedDummyTimeSheetHelper(DummyTimeSheetHelper):
    def __init__(self, log, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = log

    def run(self, driver):
        self.log.append("fill")
        super().run(driver)


class LoggedDummySession(DummySession):
    def __init__(self, log):
        super().__init__()
        self.log = log

    def go_to_default_content(self):
        super().go_to_default_content()
        self.log.append("default")

    def click(self, element_id):
        super().click(element_id)
        self.log.append(f"click:{element_id}")
        return True

    def fill_input(self, element_id, value):
        super().fill_input(element_id, value)
        self.log.append(f"fill:{element_id}:{value}")
        return True


# Backward compatibility aliases
DummyDatePage = DummyDateEntryPage
DummyInfoPage = DummyAdditionalInfoPage
DummyAddPage = DummyAdditionalInfoPage
DummyHelper = DummyTimeSheetHelper
LoggedDummyHelper = LoggedDummyTimeSheetHelper
LoggedDummyInfoPage = LoggedDummyAdditionalInfoPage
