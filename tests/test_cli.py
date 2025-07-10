import sys
import types
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from sele_saisie_auto import __version__, cli  # noqa: E402


def test_help_displays_new_options(capsys):
    with pytest.raises(SystemExit):
        cli.parse_args(["--help"])
    out = capsys.readouterr().out
    assert "--version" in out
    assert "Automate PSA Time" in out
    assert "--headless" in out
    assert "--no-sandbox" in out


def test_version_option(capsys):
    with pytest.raises(SystemExit):
        cli.parse_args(["--version"])
    out = capsys.readouterr().out.strip()
    assert out.endswith(__version__)


def test_parse_flags():
    args = cli.parse_args(["--headless", "--no-sandbox"])
    assert args.headless is True
    assert args.no_sandbox is True


def test_main_creates_services_and_passes_flags(monkeypatch):
    dummy_args = types.SimpleNamespace(log_level=None, headless=True, no_sandbox=True)
    monkeypatch.setattr(cli, "parse_args", lambda argv: dummy_args)
    monkeypatch.setattr(cli, "get_log_file", lambda: "log.html")

    cfg = types.SimpleNamespace(raw={})
    monkeypatch.setattr(
        cli,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: cfg),
    )

    service_calls = {}

    class DummyConfigurator:
        def __init__(self, conf):
            service_calls["cfg"] = conf

        def build_services(self, log_file):
            service_calls["log_file"] = log_file
            return "services"

    monkeypatch.setattr(cli, "ServiceConfigurator", DummyConfigurator)

    auto_data = {}

    class DummyAutomation:
        def __init__(self, lf, conf, logger=None, services=None):
            auto_data["init_auto"] = (lf, conf, logger, services)
            self.resource_manager = object()
            self.page_navigator = object()
            self.context = types.SimpleNamespace()
            self.logger = logger
            self.choix_user = True

    class DummyOrchestrator:
        def __init__(self, *args, **kwargs):
            auto_data["init"] = args

        @classmethod
        def from_components(cls, *a, **k):
            auto_data["from_components"] = a
            return cls(*a, **k)

        def run(self, headless=False, no_sandbox=False):
            auto_data["run"] = (headless, no_sandbox)

    monkeypatch.setattr(cli, "PSATimeAutomation", DummyAutomation)
    monkeypatch.setattr(cli, "AutomationOrchestrator", DummyOrchestrator)

    class DummyLogger:
        def __enter__(self):
            auto_data["enter"] = True
            return "logger"

        def __exit__(self, exc_type, exc, tb):
            auto_data["exit"] = True

    monkeypatch.setattr(cli, "get_logger", lambda lf: DummyLogger())
    monkeypatch.setattr(
        cli, "initialize_logger", lambda cfg_raw, log_level_override=None: None
    )

    cli.main([])

    assert service_calls == {"cfg": cfg, "log_file": "log.html"}
    assert "from_components" in auto_data
    assert auto_data["run"] == (True, True)
    assert auto_data["enter"] and auto_data["exit"]
