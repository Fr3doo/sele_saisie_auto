# tests\test_constants.py

# Import des bibliothèques nécessaires
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from sele_saisie_auto.constants import (  # noqa: E402
    ID_TO_KEY_MAPPING,
    LISTES_ID_INFORMATIONS_MISSION,
)
from sele_saisie_auto.enums import MissionField  # noqa: E402


def test_project_information_constants() -> None:

    # On s'attend désormais à des enums (pas des str)
    expected_enums = list(MissionField)
    assert LISTES_ID_INFORMATIONS_MISSION == expected_enums
    # Par sécurité, vérifie bien le type
    assert all(isinstance(f, MissionField) for f in LISTES_ID_INFORMATIONS_MISSION)

    # Le mapping est maintenant typé: dict[MissionField, str]
    expected_mapping = {field: field.config_key for field in MissionField}
    assert ID_TO_KEY_MAPPING == expected_mapping
    # Vérifie également que toutes les clés sont bien des enums
    assert all(isinstance(k, MissionField) for k in ID_TO_KEY_MAPPING.keys())
