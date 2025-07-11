import types
from configparser import ConfigParser

import pytest


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
    """Provide a sample ConfigParser similar to real config."""
    cfg = ConfigParser()
    cfg["credentials"] = {"login": "enc_login", "mdp": "enc_pwd"}
    cfg["settings"] = {
        "url": "http://test",
        "date_cible": "01/07/2024",
        "liste_items_planning": '"desc1", "desc2"',
    }
    cfg["work_schedule"] = {"lundi": "En mission,8"}
    cfg["project_information"] = {"billing_action": "Facturable"}
    cfg["additional_information_rest_period_respected"] = {"lundi": "Oui"}
    cfg["additional_information_work_time_range"] = {"lundi": "8-16"}
    cfg["additional_information_half_day_worked"] = {"lundi": "Non"}
    cfg["additional_information_lunch_break_duration"] = {"lundi": "1"}
    cfg["work_location_am"] = {"lundi": "CGI"}
    cfg["work_location_pm"] = {"lundi": "CGI"}
    cfg["cgi_options_billing_action"] = {"Facturable": "B"}
    return cfg


# ----------------------------
# Common test stubs
# ----------------------------


class DummyBrowserSession:
    """Lightweight browser session stub."""

    def __init__(self):
        self.open_calls = []
        self.driver = "drv"
        self.waiter = types.SimpleNamespace(wait_for_element=lambda *a, **k: True)

    def wait_for_dom(self, driver):
        self.wait_called = True

    def go_to_iframe(self, frame_id):
        self.iframe_called = frame_id
        return True

    def open(self, url, headless=False, no_sandbox=False):
        self.open_calls.append((url, headless, no_sandbox))
        return self.driver

    def go_to_default_content(self):
        self.default_called = True

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

    def _click_action_button(self, driver, create_new):
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


class DummyTimeSheetHelper:
    ran = None

    def __init__(self, *args, **kwargs):
        self.calls = []

    def run(self, driver):
        self.__class__.ran = driver
        self.calls.append(driver)


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


class LoggedDummyTimeSheetHelper(DummyTimeSheetHelper):
    def __init__(self, log, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = log

    def run(self, driver):
        super().run(driver)
        self.log.append("fill")


class LoggedDummySession(DummySession):
    def __init__(self, log):
        super().__init__()
        self.log = log

    def go_to_default_content(self):
        super().go_to_default_content()
        self.log.append("default")


# Backward compatibility aliases
DummyDatePage = DummyDateEntryPage
DummyInfoPage = DummyAdditionalInfoPage
DummyAddPage = DummyAdditionalInfoPage
DummyHelper = DummyTimeSheetHelper
LoggedDummyHelper = LoggedDummyTimeSheetHelper
LoggedDummyInfoPage = LoggedDummyAdditionalInfoPage
