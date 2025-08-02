import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from unittest.mock import MagicMock  # noqa: E402

from sele_saisie_auto.app_config import AppConfig, AppConfigRaw  # noqa: E402
from sele_saisie_auto.encryption_utils import Credentials  # noqa: E402
from sele_saisie_auto.logging_service import Logger  # noqa: E402
from sele_saisie_auto.navigation import PageNavigator  # noqa: E402
from sele_saisie_auto.orchestration import AutomationOrchestrator  # noqa: E402
from sele_saisie_auto.saisie_context import SaisieContext  # noqa: E402
from tests.conftest import (  # noqa: E402
    DummyAddPage,
    DummyBrowserSession,
    DummyDateEntryPage,
    DummyHelper,
    DummyLoginHandler,
)


def test_run_calls_services(monkeypatch, sample_config):
    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    logger = Logger("log.html")
    session = DummyBrowserSession()
    login = DummyLoginHandler()
    date_page = DummyDateEntryPage()
    add_page = DummyAddPage()
    creds = Credentials(b"k" * 32, object(), b"user", object(), b"pwd", object())

    class DummyEncService:
        def __init__(self):
            self.calls = 0

        def retrieve_credentials(self):
            self.calls += 1
            return creds

    class DummySHMService:
        def __init__(self):
            self.removed = []

        def supprimer_memoire_partagee_securisee(self, mem):
            self.removed.append(mem)

    enc_service = DummyEncService()
    shm_service = DummySHMService()

    ctx = SaisieContext(app_cfg, enc_service, shm_service, {}, [])
    from sele_saisie_auto.orchestration import automation_orchestrator as orch_mod
    from sele_saisie_auto.resources import resource_manager as rm

    monkeypatch.setattr(
        orch_mod,
        "ResourceManager",
        lambda log_file, **kw: rm.ResourceManager(log_file, enc_service),
    )

    orch = AutomationOrchestrator(
        app_cfg,
        logger,
        session,
        login,
        date_page,
        add_page,
        ctx,
        timesheet_helper_cls=DummyHelper,
    )
    orch.page_navigator = PageNavigator(
        session,
        login,
        date_page,
        add_page,
        DummyHelper(None, logger),
    )
    orch.page_navigator = PageNavigator(
        session,
        login,
        date_page,
        add_page,
        DummyHelper(None, logger),
    )
    orch.page_navigator = PageNavigator(
        session,
        login,
        date_page,
        add_page,
        DummyHelper(None, logger),
    )

    orch.page_navigator = PageNavigator(
        session,
        login,
        date_page,
        add_page,
        DummyHelper(None, logger),
    )

    # Stub out heavy selenium helpers
    orch.wait_for_dom = lambda d: None
    orch.switch_to_iframe_main_target_win0 = lambda d: True
    orch.browser_session.go_to_default_content = lambda: None
    orch.browser_session.waiter = types.SimpleNamespace(
        wait_for_element=lambda *a, **k: True
    )
    orch.date_entry_page._click_action_button = lambda d: None
    orch.additional_info_page._handle_save_alerts = lambda d: None
    from sele_saisie_auto.orchestration import automation_orchestrator as orch_mod

    monkeypatch.setattr(orch_mod, "detecter_doublons_jours", lambda *a, **k: None)

    cleanup_args = {}

    def cleanup_spy(mkey, mlogin, mpwd):
        cleanup_args["vals"] = (mkey, mlogin, mpwd)

    monkeypatch.setattr(orch, "cleanup_resources", cleanup_spy)
    from sele_saisie_auto import console_ui

    monkeypatch.setattr(console_ui, "ask_continue", lambda *a, **k: None)

    orch.run()

    assert enc_service.calls == 1
    assert cleanup_args["vals"] == (
        creds.mem_key,
        creds.mem_login,
        creds.mem_password,
    )
    assert session.open_calls[0][0] == app_cfg.url
    assert login.calls
    assert DummyHelper.ran == session.driver
    assert "nav" in date_page.calls
    assert "nav_add" in add_page.calls


def test_wrappers(monkeypatch, sample_config):
    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    orch = AutomationOrchestrator(
        app_cfg,
        Logger("log.html"),
        DummyBrowserSession(),
        DummyLoginHandler(),
        DummyDateEntryPage(),
        DummyAddPage(),
        SaisieContext(app_cfg, None, None, {}, []),
        timesheet_helper_cls=DummyHelper,
    )

    monkeypatch.setattr(orch.browser_session, "wait_for_dom", lambda d: None)
    monkeypatch.setattr(orch, "switch_to_iframe_main_target_win0", lambda d: True)
    orch.navigate_from_home_to_date_entry_page("drv")
    orch.submit_date_cible("drv")
    orch.navigate_from_work_schedule_to_additional_information_page("drv")
    orch.submit_and_validate_additional_information("drv")
    orch.save_draft_and_validate("drv")


def test_run_order(monkeypatch, sample_config):
    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    logger = Logger("log.html")
    session = DummyBrowserSession()
    login = DummyLoginHandler()
    date_page = DummyDateEntryPage()
    add_page = DummyAddPage()
    creds = Credentials(b"k" * 32, object(), b"user", object(), b"pwd", object())

    class DummyEncService:
        def retrieve_credentials(self):
            return creds

    class DummySHMService:
        def supprimer_memoire_partagee_securisee(self, mem):
            pass

    ctx = SaisieContext(app_cfg, DummyEncService(), DummySHMService(), {}, [])
    from sele_saisie_auto.orchestration import automation_orchestrator as orch_mod
    from sele_saisie_auto.resources import resource_manager as rm

    monkeypatch.setattr(
        orch_mod,
        "ResourceManager",
        lambda log_file, **kw: rm.ResourceManager(log_file, DummyEncService()),
    )
    orch = AutomationOrchestrator(
        app_cfg,
        logger,
        session,
        login,
        date_page,
        add_page,
        ctx,
        timesheet_helper_cls=DummyHelper,
    )
    orch.page_navigator = PageNavigator(
        session,
        login,
        date_page,
        add_page,
        DummyHelper(None, logger),
    )

    calls = []
    monkeypatch.setattr(
        orch.page_navigator, "prepare", lambda *a, **k: calls.append("prepare")
    )
    monkeypatch.setattr(orch.page_navigator, "run", lambda *a, **k: calls.append("run"))
    monkeypatch.setattr(orch, "initialize_shared_memory", lambda: creds)
    monkeypatch.setattr(orch, "wait_for_dom", lambda *a, **k: None)
    monkeypatch.setattr(orch, "switch_to_iframe_main_target_win0", lambda *a, **k: None)
    monkeypatch.setattr(orch, "cleanup_resources", lambda *a, **k: None)
    from sele_saisie_auto import console_ui

    monkeypatch.setattr(console_ui, "ask_continue", lambda *a, **k: None)
    orch.browser_session.go_to_default_content = lambda: None
    orch.run()

    assert calls == ["prepare", "run"]


def test_run_uses_passed_cleanup_function(monkeypatch, sample_config):
    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    logger = Logger("log.html")
    session = DummyBrowserSession()
    login = DummyLoginHandler()
    date_page = DummyDateEntryPage()
    add_page = DummyAddPage()
    creds = Credentials(b"k" * 32, object(), b"user", object(), b"pwd", object())

    class DummyEncService:
        def __init__(self):
            self.calls = 0

        def retrieve_credentials(self):
            self.calls += 1
            return creds

    class DummySHMService:
        def __init__(self):
            self.removed = []

        def supprimer_memoire_partagee_securisee(self, mem):
            self.removed.append(mem)

    enc_service = DummyEncService()
    shm_service = DummySHMService()

    ctx = SaisieContext(app_cfg, enc_service, shm_service, {}, [])
    from sele_saisie_auto.orchestration import automation_orchestrator as orch_mod
    from sele_saisie_auto.resources import resource_manager as rm

    monkeypatch.setattr(
        orch_mod,
        "ResourceManager",
        lambda log_file, **kw: rm.ResourceManager(log_file, enc_service),
    )

    cleanup_args = {}

    def cleanup_func(mkey, mlogin, mpwd):
        cleanup_args["vals"] = (mkey, mlogin, mpwd)

    orch = AutomationOrchestrator(
        app_cfg,
        logger,
        session,
        login,
        date_page,
        add_page,
        ctx,
        timesheet_helper_cls=DummyHelper,
        cleanup_resources=cleanup_func,
    )

    orch.page_navigator = PageNavigator(
        session,
        login,
        date_page,
        add_page,
        DummyHelper(None, logger),
    )

    orch.wait_for_dom = lambda d: None
    orch.switch_to_iframe_main_target_win0 = lambda d: True
    orch.browser_session.go_to_default_content = lambda: None
    orch.browser_session.waiter = types.SimpleNamespace(
        wait_for_element=lambda *a, **k: True
    )
    orch.date_entry_page._click_action_button = lambda d: None
    orch.additional_info_page._handle_save_alerts = lambda d: None
    from sele_saisie_auto.orchestration import automation_orchestrator as orch_mod

    monkeypatch.setattr(orch_mod, "detecter_doublons_jours", lambda *a, **k: None)
    from sele_saisie_auto import console_ui

    monkeypatch.setattr(console_ui, "ask_continue", lambda *a, **k: None)

    orch.run()

    assert cleanup_args["vals"] == (
        creds.mem_key,
        creds.mem_login,
        creds.mem_password,
    )


def test_run_sequence_with_mocks(sample_config):
    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    logger = Logger("log.html")
    creds = Credentials(b"k" * 32, object(), b"u", object(), b"p", object())

    order = []

    rm = MagicMock()
    rm.__enter__.side_effect = lambda: (order.append("enter"), rm)[1]
    rm.__exit__.side_effect = lambda exc_type, exc, tb: order.append("exit")
    rm.initialize_shared_memory.side_effect = lambda *a, **k: (
        order.append("init"),
        creds,
    )[1]
    rm.get_driver.side_effect = lambda *a, **k: (order.append("driver"), "drv")[1]

    pn = MagicMock()
    pn.browser_session = DummyBrowserSession()
    pn.prepare.side_effect = lambda *a, **k: order.append("prepare")
    pn.run.side_effect = lambda *a, **k: order.append("run")

    ctx = SaisieContext(app_cfg, None, None, {}, [])
    svc = types.SimpleNamespace(app_config=app_cfg)
    orch = AutomationOrchestrator.from_components(
        rm,
        pn,
        svc,
        ctx,
        logger,
        timesheet_helper_cls=lambda *a, **k: object(),
    )

    orch.cleanup_resources = lambda *a, **k: order.append("cleanup")

    orch.run()

    assert order == [
        "enter",
        "init",
        "driver",
        "prepare",
        "run",
        "cleanup",
        "exit",
    ]
