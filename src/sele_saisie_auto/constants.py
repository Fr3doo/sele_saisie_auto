"""Module contenant les constantes partagées."""

from sele_saisie_auto.enums import MissionField

# Mapping numerique -> nom du jour
JOURS_SEMAINE = {
    1: "dimanche",
    2: "lundi",
    3: "mardi",
    4: "mercredi",
    5: "jeudi",
    6: "vendredi",
    7: "samedi",
}

# Liste des IDs associés aux informations du projet
LISTES_ID_INFORMATIONS_MISSION = [field.value for field in MissionField]

# Correspondance entre l'ID d'un champ et la clé de configuration associée
ID_TO_KEY_MAPPING = {field.value: field.config_key for field in MissionField}
