"""Module contenant les constantes partagées."""

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

# Dictionnaire de jours initialisé vide pour la configuration
JOURS_SEMAINE__DICT = {
    "lundi": "",
    "mardi": "",
    "mercredi": "",
    "jeudi": "",
    "vendredi": "",
    "samedi": "",
    "dimanche": "",
}

# Liste ordonnee des jours de la semaine
JOURS_SEMAINE__LIST = [
    "dimanche",
    "lundi",
    "mardi",
    "mercredi",
    "jeudi",
    "vendredi",
    "samedi",
]

# Liste des IDs associés aux informations du projet
LISTES_ID_INFORMATIONS_MISSION = [
    "PROJECT_CODE$0",
    "ACTIVITY_CODE$0",
    "CATEGORY_CODE$0",
    "SUB_CATEGORY_CODE$0",
    "BILLING_ACTION$0",
]

# Correspondance entre l'ID d'un champ et la clé de configuration associée
ID_TO_KEY_MAPPING = {
    "PROJECT_CODE$0": "project_code",
    "ACTIVITY_CODE$0": "activity_code",
    "CATEGORY_CODE$0": "category_code",
    "SUB_CATEGORY_CODE$0": "sub_category_code",
    "BILLING_ACTION$0": "billing_action",
}
