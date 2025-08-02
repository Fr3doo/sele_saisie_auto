import sys
import types
from multiprocessing import shared_memory
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from sele_saisie_auto import __version__, cli  # noqa: E402
from sele_saisie_auto.memory_config import MemoryConfig  # noqa: E402


def test_help_displays_new_options(capsys):
    with pytest.raises(SystemExit):
        cli.parse_args(["--help"])
    out = capsys.readouterr().out
    assert "--version" in out
    assert "Automate PSA Time" in out
    assert "--headless" in out
    assert "--no-sandbox" in out
    assert "--cleanup-mem" in out


def test_version_option(capsys):
    with pytest.raises(SystemExit):
        cli.parse_args(["--version"])
    out = capsys.readouterr().out.strip()
    assert out.endswith(__version__)


def test_parse_flags():
    args = cli.parse_args(["--headless", "--no-sandbox"])
    assert args.headless is True
    assert args.no_sandbox is True

    args = cli.parse_args(["--cleanup-mem"])
    assert args.cleanup_mem is True


def test_main_creates_services_and_passes_flags(monkeypatch):
    dummy_args = types.SimpleNamespace(
        log_level=None,
        headless=True,
        no_sandbox=True,
        cleanup_mem=False,
    )
    monkeypatch.setattr(cli, "parse_args", lambda argv: dummy_args)
    monkeypatch.setattr(cli, "get_log_file", lambda: "log.html")

    cfg = types.SimpleNamespace(raw={}, encrypted_login="x", encrypted_mdp="y")
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
            return types.SimpleNamespace(encryption_service=types.SimpleNamespace())

    monkeypatch.setattr(
        cli,
        "service_configurator_factory",
        lambda cfg, **kw: DummyConfigurator(cfg),
    )

    auto_data = {}

    class DummyAutomation:
        def __init__(self, lf, conf, logger=None, services=None):
            auto_data["init_auto"] = (lf, conf, logger, services)
            self.resource_manager = object()
            self.page_navigator = object()
            self.context = types.SimpleNamespace()
            self.logger = logger

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
        cli.LoggingConfigurator,
        "setup",
        lambda log_file, debug_mode, config=None: None,
    )

    cli.main([])

    assert service_calls == {"cfg": cfg, "log_file": "log.html"}
    assert "from_components" in auto_data
    assert auto_data["run"] == (True, True)
    assert auto_data["enter"] and auto_data["exit"]


def test_main_cleanup_flag(monkeypatch):
    dummy_args = types.SimpleNamespace(
        log_level=None,
        headless=False,
        no_sandbox=False,
        cleanup_mem=True,
    )
    monkeypatch.setattr(cli, "parse_args", lambda argv: dummy_args)
    called = {}
    import sele_saisie_auto.launcher as launcher

    monkeypatch.setattr(
        launcher,
        "cleanup_memory_segments",
        lambda: called.setdefault("clean", True),
    )

    cli.main([])

    assert called["clean"] is True


def test_cleanup_mem_flag_removes_segments_and_skips_automation(monkeypatch):
    dummy_args = types.SimpleNamespace(
        log_level=None,
        headless=False,
        no_sandbox=False,
        cleanup_mem=True,
    )
    monkeypatch.setattr(cli, "parse_args", lambda argv: dummy_args)
    import sele_saisie_auto.launcher as launcher

    mem_cfg = MemoryConfig.with_uuid()
    leftovers = []
    for name in (
        mem_cfg.cle_name,
        mem_cfg.data_name,
        mem_cfg.login_name,
        mem_cfg.password_name,
    ):
        seg = shared_memory.SharedMemory(create=True, size=1, name=name)
        seg.buf[:1] = b"x"
        seg.close()
        leftovers.append(name)

    orig_cleanup = launcher.cleanup_memory_segments
    monkeypatch.setattr(
        launcher,
        "cleanup_memory_segments",
        lambda: orig_cleanup(mem_cfg),
    )
    called: dict[str, bool] = {}
    monkeypatch.setattr(
        cli,
        "PSATimeAutomation",
        lambda *a, **k: called.setdefault("automation", True),
    )

    cli.main([])

    assert "automation" not in called
    for name in leftovers:
        with pytest.raises(FileNotFoundError):
            shared_memory.SharedMemory(name=name)


def test_prompts_and_encrypts_when_credentials_missing(monkeypatch):
    dummy_args = types.SimpleNamespace(
        log_level=None,
        headless=False,
        no_sandbox=False,
        cleanup_mem=False,
    )
    monkeypatch.setattr(cli, "parse_args", lambda argv: dummy_args)
    monkeypatch.setattr(cli, "get_log_file", lambda: "log.html")

    cfg = types.SimpleNamespace(raw={}, encrypted_login=None, encrypted_mdp=None)
    monkeypatch.setattr(
        cli,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: cfg),
    )

    monkeypatch.setattr("builtins.input", lambda prompt="": "user")
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt="": "pass")

    class DummyEnc:
        def __init__(self):
            self.cle_aes = None

        def __enter__(self):
            self.cle_aes = b"k" * 32
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def chiffrer_donnees(self, donnees, cle, taille_bloc=128):
            return f"enc:{donnees}".encode()

        def store_credentials(self, login_data, password_data):
            self.login = login_data
            self.pwd = password_data

        def retrieve_credentials(self):
            from sele_saisie_auto.encryption_utils import Credentials

            return Credentials(
                aes_key=self.cle_aes or b"",
                mem_key=object(),
                login=self.login,
                mem_login=object(),
                password=self.pwd,
                mem_password=object(),
            )

        def dechiffrer_donnees(self, data, cle, taille_bloc=128):
            return data.decode().split("enc:", 1)[1]

    class DummyConfigurator:
        def __init__(self, conf):
            self.cfg = conf

        def build_services(self, log_file):
            enc = DummyEnc()
            return types.SimpleNamespace(encryption_service=enc)

    monkeypatch.setattr(
        cli,
        "service_configurator_factory",
        lambda conf, **kw: DummyConfigurator(conf),
    )

    results: dict[str, object] = {}

    class DummyAutomation:
        def __init__(self, lf, conf, logger=None, services=None):
            enc = services.encryption_service
            creds = enc.retrieve_credentials()
            results["login"] = enc.dechiffrer_donnees(creds.login, creds.aes_key)
            results["password"] = enc.dechiffrer_donnees(creds.password, creds.aes_key)
            results["enc_login"] = creds.login
            results["enc_pwd"] = creds.password
            results["enc"] = enc
            self.resource_manager = object()
            self.page_navigator = object()
            self.context = types.SimpleNamespace()
            self.logger = logger

    class DummyOrchestrator:
        @classmethod
        def from_components(cls, *a, **k):
            return cls()

        def run(self, headless=False, no_sandbox=False):
            pass

    monkeypatch.setattr(cli, "PSATimeAutomation", DummyAutomation)
    monkeypatch.setattr(cli, "AutomationOrchestrator", DummyOrchestrator)

    cli.main([])

    results["enc"].__exit__(None, None, None)
    assert results["login"] == "user"
    assert results["password"] == "pass"
    assert results["enc_login"] != b"user"
    assert results["enc_pwd"] != b"pass"
