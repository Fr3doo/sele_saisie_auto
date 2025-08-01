import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import pytest  # noqa: E402

from sele_saisie_auto.encryption_utils import Credentials  # noqa: E402
from sele_saisie_auto.navigation.page_navigator import PageNavigator  # noqa: E402
from tests.conftest import (  # noqa: E402
    LoggedDummyAdditionalInfoPage as StubAdditionalInfoPage,
)
from tests.conftest import LoggedDummyDateEntryPage as StubDateEntryPage  # noqa: E402
from tests.conftest import LoggedDummyLoginHandler as StubLoginHandler  # noqa: E402
from tests.conftest import LoggedDummySession as StubBrowserSession  # noqa: E402
from tests.conftest import (  # noqa: E402
    LoggedDummyTimeSheetHelper as StubTimeSheetHelper,
)


def make_navigator():
    log = []
    session = StubBrowserSession(log)
    info_page = StubAdditionalInfoPage(log)
    navigator = PageNavigator(
        session,
        StubLoginHandler(log),
        StubDateEntryPage(log),
        info_page,
        StubTimeSheetHelper(
            log, additional_info_page=info_page, browser_session=session
        ),
    )
    return log, navigator


def test_run_without_prepare_raises():
    log, nav = make_navigator()
    with pytest.raises(RuntimeError):
        nav.run("drv")
    assert not log


def test_run_without_driver_raises():
    log, nav = make_navigator()
    creds = Credentials(b"k", None, b"u", None, b"p", None)
    nav.prepare(creds, "2024")
    with pytest.raises(RuntimeError, match="driver missing"):
        nav.run(None)  # type: ignore[arg-type]
    assert not log


def test_run_calls_dependencies_in_order():
    log, nav = make_navigator()
    creds = Credentials(b"k", None, b"u", None, b"p", None)
    nav.prepare(creds, "2024")
    nav.run("drv")
    assert log == [
        "login",
        "navigate",
        "process",
        "fill",
        "nav_add",
        "submit_add",
        "default",
        "save",
    ]
