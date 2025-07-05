# Ce script doit être lancé en mode administrateur.

# Télécharge et installe Poetry à l'aide de la commande officielle
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Vérifie que Poetry est bien installé
poetry --version
