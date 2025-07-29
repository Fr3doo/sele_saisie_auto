import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.additional_info_locators import (  # noqa: E402
    ADDITIONAL_INFO_LOCATORS,
)
from sele_saisie_auto.elements.element_id_builder import ElementIdBuilder  # noqa: E402


def test_default_pattern():
    assert ElementIdBuilder.build_day_input_id("POL_TIME", 2, 5) == "POL_TIME2$5"


def test_uc_dailyrest_pattern():
    base = ADDITIONAL_INFO_LOCATORS["DAY_UC_DAILYREST"]
    assert ElementIdBuilder.build_day_input_id(base, 4, 2) == f"{base}4$2"


def test_special_dailyrest_pattern():
    base = ADDITIONAL_INFO_LOCATORS["DAY_UC_DAILYREST_SPECIAL"]
    assert ElementIdBuilder.build_day_input_id(base, 1, 3) == f"{base}11$0"


def test_uc_location_a_pattern():
    base = ADDITIONAL_INFO_LOCATORS["DAY_UC_LOCATION_A"]
    assert ElementIdBuilder.build_day_input_id(base, 7, 1) == f"{base}7$1"
