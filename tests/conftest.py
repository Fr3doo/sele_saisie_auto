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
