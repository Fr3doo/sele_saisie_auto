# pragma: no cover
"""Messages communs utilisés à travers plusieurs modules."""

# Messages de log ou d'erreur
TENTATIVE_INSERTION = "tentative d'insertion n°"
ECHEC_INSERTION = "Échec de l'insertion"
REFERENCE_OBSOLETE = "Référence obsolète"
IMPOSSIBLE_DE_TROUVER = "Impossible de trouver"
INTROUVABLE = "introuvable"
WEBDRIVER = "WebDriver"
ERREUR_INATTENDUE = "Erreur inattendue"
AUCUNE_VALEUR = "Aucune valeur"
REMPLISSAGE = "Remplissage"

# Gabarit commun pour la confirmation d'une valeur
CONFIRMED_VALUE = "⚠️ Valeur '{valeur}' confirmée pour le jour '{jour}'"


# Messages divers
CHECK_FILLED_DAYS = "🔍 Vérification des jours déjà remplis..."
DAY_CHECK = "👉 Vérification du jour : {jour} (ID: {id})"
DAY_ALREADY_FILLED = "✅ Jour '{jour}' déjà rempli."
DAY_EMPTY = "❌ Jour '{jour}' vide."
ELEMENT_NOT_FOUND_ID = "❌ Élément non trouvé pour l'ID : {id}"
DAY_ALREADY_FILLED_NO_CHANGE = "🔄 Jour '{jour}' déjà rempli, aucun changement."
DESCRIPTION_PROCESS_START = (
    "🔍 Début du traitement pour la description : '{description}'"
)
DESCRIPTION_NOT_FOUND = (
    "❌ Description '{description}' non trouvée avec l'id_value '{id_value}'."
)
DESCRIPTION_FOUND = "✅ Description '{description}' trouvée à l'index {index}."
FILL_EMPTY_DAYS = "✍️ Remplissage des jours vides pour '{description}'."
ADDITIONAL_INFO_DONE = "Validation des informations supplémentaires terminée."
SAVE_ALERT_WARNING = "⚠️ Alerte rencontrée lors de la sauvegarde."
TIME_SHEET_EXISTS_ERROR = (
    "ERREUR : Vous avez déjà créé une feuille de temps pour cette période. (10502,125)"
)
MODIFY_DATE_MESSAGE = (
    "--> Modifier la date du PSATime dans le fichier ini. Le programme va s'arreter."
)
DATE_VALIDATED = "Date validée avec succès."
ASK_CREDENTIALS = "Veuillez entrer vos identifiants"
MISSING_AES_KEY = "Clé AES manquante"
CONFIGURATION_SAVED = "Configuration enregistrée"
DOM_STABLE = "Le DOM est stable."
DOM_NOT_STABLE = "Le DOM n'est pas complètement stable après le délai."
LOCATOR_VALUE_REQUIRED = (
    "Erreur : Le paramètre 'locator_value' doit être spécifié pour localiser l'élément."
)
WAIT_STABILISATION = "Veuillez patienter. Court délai pour stabilisation du DOM"
NO_DATE_CHANGE = "Aucune modification de la date nécessaire."
