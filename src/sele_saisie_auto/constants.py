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

# ---------------------------------------------------------------------------
# Règle d’usage (cadrage)
# - Itération métier : toujours sur list(MissionField)
# - Interaction DOM (Selenium) : toujours via field.value
# - Récupération config : toujours via field.config_key
# ---------------------------------------------------------------------------

# VUES TYPIÉES (référence)
# -----------------------
# Liste des champs mission sous forme d'enums (pas de str)
LISTES_ID_INFORMATIONS_MISSION: list[MissionField] = list(MissionField)

# Correspondance champ -> clé de configuration
ID_TO_KEY_MAPPING: dict[MissionField, str] = {
    field: field.config_key for field in MissionField
}

# ---------------------------------------------------------------------------
# (Optionnel) VUES COMPATIBILITÉ pour code legacy qui manipule encore des str.
# À retirer une fois la migration finalisée.
# ---------------------------------------------------------------------------
# DEPRECATED: utilisez LISTES_ID_INFORMATIONS_MISSION (Enum) à la place.
LISTES_ID_INFORMATIONS_MISSION_STR: list[str] = [field.value for field in MissionField]
# DEPRECATED: utilisez ID_TO_KEY_MAPPING (dict[MissionField, str]) à la place.
ID_TO_KEY_MAPPING_STR: dict[str, str] = {
    field.value: field.config_key for field in MissionField
}
