import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.elements.element_id_builder import (  # noqa: E402
    build_day_input_id,
)


def test_default_pattern():
    assert build_day_input_id("POL_TIME", 2, 5) == "POL_TIME2$5"


def test_special_dailyrest_pattern():
    base = "UC_TIME_LIN_WRK_UC_DAILYREST"
    assert build_day_input_id(base, 1, 3) == f"{base}11$0"
