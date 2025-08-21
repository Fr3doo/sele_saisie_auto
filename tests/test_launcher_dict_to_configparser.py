# tests/test_launcher_dict_to_configparser.py
import configparser
from typing import Any, cast

import pytest

from sele_saisie_auto.launcher import _dict_to_configparser


def test_dict_to_configparser_creates_sections_and_entries() -> None:
    data = {
        "section1": {"key1": "value1"},
        "section2": {"key2": "value2"},
    }
    parser: configparser.ConfigParser = _dict_to_configparser(data)
    assert set(parser.sections()) == {"section1", "section2"}
    assert parser.get("section1", "key1") == "value1"
    assert parser.get("section2", "key2") == "value2"


def test_dict_to_configparser_empty() -> None:
    parser: configparser.ConfigParser = _dict_to_configparser({})
    assert parser.sections() == []


def test_dict_to_configparser_empty_section() -> None:
    parser: configparser.ConfigParser = _dict_to_configparser({"section1": {}})
    assert parser.has_section("section1")
    assert not parser.has_option("section1", "key1")
    with pytest.raises(configparser.NoOptionError):
        parser.get("section1", "key1")


def test_dict_to_configparser_rejects_non_string_value() -> None:
    # configparser exige des chaînes pour les valeurs ; un int déclenche TypeError
    # on construit sciemment un mapping invalide
    bad_data: dict[str, dict[str, Any]] = {"section1": {"key1": 123}}
    with pytest.raises(TypeError):
        _dict_to_configparser(cast(dict[str, dict[str, str]], bad_data))