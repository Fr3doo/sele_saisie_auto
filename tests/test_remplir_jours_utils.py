import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.remplir_jours_feuille_de_temps import (  # noqa: E402
    afficher_message_insertion,
    ajouter_jour_a_jours_remplis,
    est_en_mission,
    est_en_mission_presente,
)
from sele_saisie_auto.shared_utils import clear_screen  # noqa: E402


def test_utilities(monkeypatch):
    assert est_en_mission("En mission") is True
    assert est_en_mission("Autre") is False

    jours = {"lun": ("En mission", "8")}
    assert est_en_mission_presente(jours) is True

    jours_remplis = []
    assert ajouter_jour_a_jours_remplis("lun", jours_remplis) == ["lun"]
    assert ajouter_jour_a_jours_remplis("lun", jours_remplis) == ["lun"]

    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.write_log",
        lambda msg, file, level: logs.append(msg),
    )
    afficher_message_insertion("lun", "8", 0, "test")
    assert logs

    called = {}
    monkeypatch.setattr(
        "sele_saisie_auto.shared_utils.subprocess.run",
        lambda cmd, *a, **k: called.setdefault("cmd", cmd),
    )
    clear_screen()
    assert called["cmd"] in {"cls", "clear"}
