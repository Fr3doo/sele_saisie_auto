import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

from remplir_jours_feuille_de_temps import (
    est_en_mission,
    est_en_mission_presente,
    ajouter_jour_a_jours_remplis,
    afficher_message_insertion,
    clear_screen,
)


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
        "remplir_jours_feuille_de_temps.write_log",
        lambda msg, file, level: logs.append(msg),
    )
    afficher_message_insertion("lun", "8", 0, "test")
    assert logs

    called = {}
    monkeypatch.setattr("os.system", lambda cmd: called.setdefault("cmd", cmd))
    clear_screen()
    assert called["cmd"] in {"cls", "clear"}
