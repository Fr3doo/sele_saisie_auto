from sele_saisie_auto.launcher import _dict_to_configparser


def test_dict_to_configparser_creates_sections_and_entries() -> None:
    data = {
        "section1": {"key1": "value1"},
        "section2": {"key2": "value2"},
    }
    parser = _dict_to_configparser(data)
    assert set(parser.sections()) == {"section1", "section2"}
    assert parser.get("section1", "key1") == "value1"
    assert parser.get("section2", "key2") == "value2"
