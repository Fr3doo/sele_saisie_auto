import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from sele_saisie_auto.constants import ID_TO_KEY_MAPPING, LISTES_ID_INFORMATIONS_MISSION  # noqa: E402


def test_project_information_constants():
    expected_ids = [
        "PROJECT_CODE$0",
        "ACTIVITY_CODE$0",
        "CATEGORY_CODE$0",
        "SUB_CATEGORY_CODE$0",
        "BILLING_ACTION$0",
    ]
    assert LISTES_ID_INFORMATIONS_MISSION == expected_ids

    expected_mapping = {
        "PROJECT_CODE$0": "project_code",
        "ACTIVITY_CODE$0": "activity_code",
        "CATEGORY_CODE$0": "category_code",
        "SUB_CATEGORY_CODE$0": "sub_category_code",
        "BILLING_ACTION$0": "billing_action",
    }
    assert ID_TO_KEY_MAPPING == expected_mapping
