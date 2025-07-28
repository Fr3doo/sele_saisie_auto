from sele_saisie_auto.selenium_utils import Waiter
from sele_saisie_auto.selenium_utils.waiter_factory import create_waiter


def test_create_waiter_returns_configured_waiter():
    waiter = create_waiter(5)

    assert isinstance(waiter, Waiter)
    assert waiter.wrapper.default_timeout == 5
    assert waiter.wrapper.long_timeout == 10
