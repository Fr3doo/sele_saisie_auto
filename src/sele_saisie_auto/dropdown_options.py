# pragma: no cover
# dropdown_options.py

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkLocationOption:
    """Option du menu déroulant pour le lieu de travail."""

    label: str


@dataclass(frozen=True)
class CGIOption:
    """Option générique Oui/Non/N\xa0A pour les informations CGI."""

    label: str


@dataclass(frozen=True)
class CGILunchOption:
    """Option pour la durée de la pause déjeuner."""

    label: str


@dataclass(frozen=True)
class BillingActionOption:
    """Option du menu « billing action »."""

    label: str
    code: str


@dataclass(frozen=True)
class WorkScheduleOption:
    """Option du planning de travail."""

    label: str


DEFAULTS_FILE = (
    Path(__file__).resolve().parents[2] / "examples" / "dropdown_defaults.json"
)


def _load_defaults() -> dict:
    try:
        with DEFAULTS_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        return {}


_DEFAULTS = _load_defaults()


# Options pour l'onglet "Lieu de travail"
_work_location_labels = _DEFAULTS.get(
    "work_location_options",
    [
        "",
        "CGI",
        "Demande CGI TLT",
        "Exceptionel TLT",
        "N/A",
        "Ponctuel TLT",
        "Regulier TLT",
        "Site client",
        "Vélo Site CGI",
        "Vélo Site client",
    ],
)
work_location_options: list[WorkLocationOption] = [
    WorkLocationOption(label) for label in _work_location_labels
]

# Options pour l'onglet "Informations CGI"
_cgi_labels = _DEFAULTS.get("cgi_options", ["", "N/A", "Oui", "Non"])
cgi_options: list[CGIOption] = [CGIOption(label) for label in _cgi_labels]

# Options pour l'onglet "Informations CGI- ligne pause dejeuner"
_cgi_dej_labels = _DEFAULTS.get("cgi_options_dejeuner", ["", "1"])
cgi_options_dejeuner: list[CGILunchOption] = [
    CGILunchOption(label) for label in _cgi_dej_labels
]

# Options pour le menu deroulant "billing"
_billing_map = _DEFAULTS.get(
    "cgi_options_billing_action",
    {"Facturable": "B", "Facture int.": "I", "Non facturable": "U"},
)
cgi_options_billing_action: list[BillingActionOption] = [
    BillingActionOption(label=k, code=v) for k, v in _billing_map.items()
]

# Options pour l'onglet "Planning de travail"
_work_schedule_labels = _DEFAULTS.get(
    "work_schedule_options",
    [
        "",
        "En mission",
        "Formation IA",
        "Conseiller Prud’Homal",
        "Vacances (Congés payés)",
        "Temps compensatoire",
        "Maladie",
        "Congé pour examen / etudes",
        "Congé déménagement",
        "Congé pour décès famille",
        "Accident de travail",
        "Congé pour juré/témoin",
        "Congé militaire",
        "Congé mariage/PACS",
        "Congé de paternité",
        "Congé naissance enfant",
        "Congé solidarité familiale",
        "Congé administratif",
        "Retour progressif au travail",
        "Absc non autoriséee non payée",
        "Congé sans solde",
        "Congé examen prénatal",
        "Congé mariage/PACS enfant",
        "Congé de parentalité payé",
        "Congé de parentalité non payé",
        "Travaux passagers",
        "Avant-vente",
        "Général et administration",
        "Compl temps partiel / activite",
        "Formation",
        "Formation Animation",
        "Jour férié",
        "RTT Q1",
        "RTT non payée (Q2)",
        "Enfant malade Alsace-Moseille",
        "Bénéficiaire don de congé",
        "Abs. autorisée non rémunérée",
        "CPF/VAE/Bilan compé. Payé",
        "CPF/VAE/Bilan compé. non payé",
        "Maladie professionnelle",
        "Accident de trajet",
        "Grossesse patho. pré-natale",
        "Grossesse patho. post-natale",
        "Elu d'état",
        "Congé recherche d'emploi",
        "Heures déplacements récup",
        "Dispense Spe Rem",
        "Repos Hebdo/Quotidien",
        "Congé d'accompagnement",
        "Enfant – Annonce patho/handi",
        "Soin handicap",
        "Formation syndicale (CFESES)",
        "RQTH - Dossier",
        "PDPMA",
        "Jours CET",
        "Mandataire sécurité sociale",
        "CET Retraite",
        "Congé deuil parental",
        "Prés. parent requis enf<12 ans",
        "Congé enfant hospitalisé",
        "Mécénat de compétences",
        "Interr spontanée de grossesse",
        "Conseiller du salarié",
        "Congé Formation conseiller CPH",
        "Défenseur syndical",
        "Formation Défenseur syndical",
        "Congé enfant malade non payé",
        "Assesseur judiciaire SS",
    ],
)
work_schedule_options: list[WorkScheduleOption] = [
    WorkScheduleOption(label) for label in _work_schedule_labels
]
