import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from sele_saisie_auto.constants import (  # noqa: E402
    ID_TO_KEY_MAPPING,
    LISTES_ID_INFORMATIONS_MISSION,
)
from sele_saisie_auto.enums import MissionField  # noqa: E402


def test_project_information_constants():
    expected_ids = [field.value for field in MissionField]
    assert LISTES_ID_INFORMATIONS_MISSION == expected_ids

    expected_mapping = {field.value: field.config_key for field in MissionField}
    assert ID_TO_KEY_MAPPING == expected_mapping
