"""Tests for URL accessibility checks."""

from __future__ import annotations

import pytest
import requests
import responses

from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.selenium_utils.navigation import verifier_accessibilite_url

URL = "https://example.com"


@pytest.mark.parametrize(
    "setup, expected",
    [
        (lambda rsps: rsps.add(responses.GET, URL, status=200), True),
        (lambda rsps: rsps.add(responses.GET, URL, status=403), False),
        (
            lambda rsps: (
                rsps.add(responses.GET, URL, body=requests.exceptions.SSLError("ssl")),
                rsps.add(responses.GET, URL, status=200),
            ),
            True,
        ),
        (
            lambda rsps: rsps.add(
                responses.GET, URL, body=requests.exceptions.Timeout()
            ),
            False,
        ),
    ],
)
def test_verifier_accessibilite_url_responses(setup, expected):
    logger = Logger(None, writer=lambda *a, **k: None)
    with responses.RequestsMock() as rsps:
        setup(rsps)
        assert verifier_accessibilite_url(URL, logger=logger) is expected
