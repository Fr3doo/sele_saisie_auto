# pragma: no cover
# dropdown_options.py

from dataclasses import dataclass


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


# Options pour l'onglet "Lieu de travail"
work_location_options: list[WorkLocationOption] = [
    WorkLocationOption(""),
    WorkLocationOption("CGI"),
    WorkLocationOption("Demande CGI TLT"),
    WorkLocationOption("Exceptionel TLT"),
    WorkLocationOption("N/A"),
    WorkLocationOption("Ponctuel TLT"),
    WorkLocationOption("Regulier TLT"),
    WorkLocationOption("Site client"),
    WorkLocationOption("Vélo Site CGI"),
    WorkLocationOption("Vélo Site client"),
]

# Options pour l'onglet "Informations CGI"
cgi_options: list[CGIOption] = [
    CGIOption(""),
    CGIOption("N/A"),
    CGIOption("Oui"),
    CGIOption("Non"),
]

# Options pour l'onglet "Informations CGI- ligne pause dejeuner"
cgi_options_dejeuner: list[CGILunchOption] = [
    CGILunchOption(""),
    CGILunchOption("1"),
]

# Options pour le menu deroulant "billing"
cgi_options_billing_action: list[BillingActionOption] = [
    BillingActionOption("Facturable", "B"),
    BillingActionOption("Facture int.", "I"),
    BillingActionOption("Non facturable", "U"),
]

# Options pour l'onglet "Planning de travail"
work_schedule_options: list[WorkScheduleOption] = [
    WorkScheduleOption(""),
    WorkScheduleOption("En mission"),
    WorkScheduleOption("Formation IA"),
    WorkScheduleOption("Conseiller Prud’Homal"),
    WorkScheduleOption("Vacances (Congés payés)"),
    WorkScheduleOption("Temps compensatoire"),
    WorkScheduleOption("Maladie"),
    WorkScheduleOption("Congé pour examen / etudes"),
    WorkScheduleOption("Congé déménagement"),
    WorkScheduleOption("Congé pour décès famille"),
    WorkScheduleOption("Accident de travail"),
    WorkScheduleOption("Congé pour juré/témoin"),
    WorkScheduleOption("Congé militaire"),
    WorkScheduleOption("Congé mariage/PACS"),
    WorkScheduleOption("Congé de paternité"),
    WorkScheduleOption("Congé naissance enfant"),
    WorkScheduleOption("Congé solidarité familiale"),
    WorkScheduleOption("Congé administratif"),
    WorkScheduleOption("Retour progressif au travail"),
    WorkScheduleOption("Absc non autoriséee non payée"),
    WorkScheduleOption("Congé sans solde"),
    WorkScheduleOption("Congé examen prénatal"),
    WorkScheduleOption("Congé mariage/PACS enfant"),
    WorkScheduleOption("Congé de parentalité payé"),
    WorkScheduleOption("Congé de parentalité non payé"),
    WorkScheduleOption("Travaux passagers"),
    WorkScheduleOption("Avant-vente"),
    WorkScheduleOption("Général et administration"),
    WorkScheduleOption("Compl temps partiel / activite"),
    WorkScheduleOption("Formation"),
    WorkScheduleOption("Formation Animation"),
    WorkScheduleOption("Jour férié"),
    WorkScheduleOption("RTT Q1"),
    WorkScheduleOption("RTT non payée (Q2)"),
    WorkScheduleOption("Enfant malade Alsace-Moseille"),
    WorkScheduleOption("Bénéficiaire don de congé"),
    WorkScheduleOption("Abs. autorisée non rémunérée"),
    WorkScheduleOption("CPF/VAE/Bilan compé. Payé"),
    WorkScheduleOption("CPF/VAE/Bilan compé. non payé"),
    WorkScheduleOption("Maladie professionnelle"),
    WorkScheduleOption("Accident de trajet"),
    WorkScheduleOption("Grossesse patho. pré-natale"),
    WorkScheduleOption("Grossesse patho. post-natale"),
    WorkScheduleOption("Elu d'état"),
    WorkScheduleOption("Congé recherche d'emploi"),
    WorkScheduleOption("Heures déplacements récup"),
    WorkScheduleOption("Dispense Spe Rem"),
    WorkScheduleOption("Repos Hebdo/Quotidien"),
    WorkScheduleOption("Congé d'accompagnement"),
    WorkScheduleOption("Enfant – Annonce patho/handi"),
    WorkScheduleOption("Soin handicap"),
    WorkScheduleOption("Formation syndicale (CFESES)"),
    WorkScheduleOption("RQTH - Dossier"),
    WorkScheduleOption("PDPMA"),
    WorkScheduleOption("Jours CET"),
    WorkScheduleOption("Mandataire sécurité sociale"),
    WorkScheduleOption("CET Retraite"),
    WorkScheduleOption("Congé deuil parental"),
    WorkScheduleOption("Prés. parent requis enf<12 ans"),
    WorkScheduleOption("Congé enfant hospitalisé"),
    WorkScheduleOption("Mécénat de compétences"),
    WorkScheduleOption("Interr spontanée de grossesse"),
    WorkScheduleOption("Conseiller du salarié"),
    WorkScheduleOption("Congé Formation conseiller CPH"),
    WorkScheduleOption("Défenseur syndical"),
    WorkScheduleOption("Formation Défenseur syndical"),
    WorkScheduleOption("Congé enfant malade non payé"),
    WorkScheduleOption("Assesseur judiciaire SS"),
]
