import types

from sele_saisie_auto import saisie_automatiser_psatime as sap
from sele_saisie_auto.app_config import AppConfig, AppConfigRaw


def test_log_configuration_details(monkeypatch, sample_config):
    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    records = []
    monkeypatch.setattr(
        sap,
        "write_log",
        lambda msg, log_file, level="INFO", log_format="html", auto_close=False: records.append(
            (level, msg)
        ),
    )

    dummy = types.SimpleNamespace(
        context=types.SimpleNamespace(config=app_cfg),
        log_file="log.html",
    )

    sap.PSATimeAutomation.log_configuration_details(dummy)

    expected_messages = [
        "📌 Chargement des configurations...",
        f"👉 Login : {app_cfg.encrypted_login} - pas visible, normal",
        f"👉 Password : {app_cfg.encrypted_mdp} - pas visible, normal",
        f"👉 URL : {app_cfg.url}",
        f"👉 Date cible : {app_cfg.date_cible}",
        "👉 Planning de travail de la semaine:",
        "🔹 'lundi': ('En mission', '8')",
        "👉 Infos_supp_cgi_periode_repos_respectee:",
        "🔹 'lundi': 'Oui'",
        "👉 Infos_supp_cgi_horaire_travail_effectif:",
        "🔹 'lundi': '8-16'",
        "👉 Planning de travail de la semaine:",
        "🔹 'lundi': 'Non'",
        "👉 Infos_supp_cgi_duree_pause_dejeuner:",
        "🔹 'lundi': '1'",
        "👉 Lieu de travail Matin:",
        "🔹 'lundi': 'CGI'",
        "👉 Lieu de travail Apres-midi:",
        "🔹 'lundi': 'CGI'",
    ]

    assert records == [("DEBUG", msg) for msg in expected_messages]
