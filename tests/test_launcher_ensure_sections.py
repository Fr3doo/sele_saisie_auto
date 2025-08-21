import configparser

from sele_saisie_auto.launcher import ensure_sections


def test_ensure_sections_adds_missing() -> None:
    parser = configparser.ConfigParser()
    ensure_sections(parser, ["settings", "work_schedule"])
    assert parser.has_section("settings")
    assert parser.has_section("work_schedule")
