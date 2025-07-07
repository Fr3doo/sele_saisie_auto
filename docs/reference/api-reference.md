# Référence API

Cette section décrit brièvement les principales classes exposées par le projet.

## SolverCore

### __init__
```python
def __init__(self, driver, algorithm):
    """Initialise le solver principal avec un WebDriver et l'algorithme de
    résolution fourni."""
```

## SeleniumFiller (``PSATimeAutomation``)

Classe principale localisée dans ``saisie_automatiser_psatime.py``. Elle pilote
le navigateur Selenium pour remplir la feuille de temps.

```python
class PSATimeAutomation:
    def __init__(
        self,
        log_file: str,
        app_config: AppConfig,
        choix_user: bool = True,
        memory_config: MemoryConfig | None = None,
    ) -> None:
        """Prépare la configuration et les services nécessaires."""
```

- ``log_initialisation() -> None`` – initialise les logs et vérifie les
  paramètres essentiels.
- ``initialize_shared_memory() -> Credentials`` – récupère les identifiants
  chiffrés depuis la mémoire partagée.
- ``setup_browser(driver_manager: SeleniumDriverManager)`` – ouvre et configure
  le navigateur.
- `switch_to_iframe_main_target_win0(driver)` – bascule dans l’iframe principale.
- `navigate_from_home_to_date_entry_page(driver)` – ouvre la page de saisie de date.
- `submit_date_cible(driver)` – valide la date choisie.
- `navigate_from_work_schedule_to_additional_information_page(driver)` – accède aux informations supplémentaires.
- `submit_and_validate_additional_information(driver)` – remplit puis confirme les données complémentaires.
- `save_draft_and_validate(driver)` – sauvegarde la feuille et déclenche la validation.
- `cleanup_resources(driver_manager, mem_key, mem_login, mem_password)` – ferme le navigateur et libère la mémoire.
- ``run() -> None`` – lance toute la séquence d’automatisation. Désormais, cette méthode délègue à ``AutomationOrchestrator.run()`` pour la logique principale.

## AutomationOrchestrator

```python
class AutomationOrchestrator:
    def run(self, *, headless=False, no_sandbox=False) -> None:
        """Exécute l'automatisation complète."""
```
Classe centrale d'orchestration de l'automatisation. Sa méthode ``run()`` exécute désormais l'ensemble de la logique.

## TimeSheetHelper

Situé dans ``remplir_jours_feuille_de_temps.py``. Orchestration du remplissage
des jours et missions.

```python
class TimeSheetHelper:
    def __init__(self, log_file: str) -> None:
        """Enregistre le chemin du fichier de log."""
```

- ``initialize()`` – prépare les dépendances du module.
- ``fill_standard_days(driver, jours_remplis: list[str]) -> list[str]`` –
  renseigne les jours hors mission.
- ``fill_work_missions(driver, jours_remplis: list[str]) -> list[str]`` –
  gère les jours « En mission ».
- ``handle_additional_fields(driver)`` – complète les champs supplémentaires.
- ``run(driver)`` – exécute l’ensemble du processus.

## ExtraInfoHelper

Regroupe plusieurs fonctions d’aide pour remplir les informations
supplémentaires (``remplir_informations_supp_utils.py``).

- ``traiter_description(driver, config)`` – renseigne un champ selon la
  configuration fournie.

## ConfigManager

Gestionnaire de ``config.ini`` exposé par ``config_manager.py``.

```python
class ConfigManager:
    def load(self) -> AppConfig:
        """Charge la configuration depuis le disque."""
    def save(self) -> str:
        """Sauvegarde l’instance courante dans ``config.ini``."""
```

## EncryptionService

Service dédié au chiffrement (``encryption_utils.py``).

```python
class EncryptionService:
    def generer_cle_aes(self, taille_cle: int = 32) -> bytes:
        """Génère une clé AES aléatoire."""
    def chiffrer_donnees(self, donnees: str, cle: bytes, taille_bloc: int = 128) -> bytes:
        """Chiffre un texte en AES‑CBC."""
    def dechiffrer_donnees(self, donnees_chiffrees: bytes, cle: bytes, taille_bloc: int = 128) -> str:
        """Déchiffre un texte précédemment chiffré."""
```

## SeleniumDriverManager

Enveloppe simplifiée autour du WebDriver (``selenium_driver_manager.py``).

```python
class SeleniumDriverManager:
    def open(self, url: str, *, fullscreen=False, headless=False, no_sandbox=False) -> Optional[WebDriver]:
        """Lance le navigateur sur l’URL cible."""
    def close(self) -> None:
        """Ferme le navigateur si nécessaire."""
```

## Logger utils

Fonctions utilitaires pour écrire les journaux (``logger_utils.py``).

- ``initialize_logger(config, log_level_override=None)`` – applique le niveau de
  log.
- ``write_log(message, log_file, level="INFO", ...)`` – ajoute une entrée dans le
  fichier de log.
- ``close_logs(log_file)`` – ferme proprement le fichier.

## Shared utils

Quelques fonctions de support communes. ``shared_utils.py``
se charge de la gestion des logs tandis que ``utils/misc.py``
contient des utilitaires pour la console.

- ``setup_logs(log_dir="logs", log_format="html") -> str`` – prépare le
  répertoire de logs.
- ``get_log_file() -> str`` – retourne le chemin du log courant.
- ``program_break_time(memorization_time: int, affichage_text: str)`` – affiche
  un compte à rebours (``utils.misc``).
- ``clear_screen()`` – efface la console (``utils.misc``).

## GUIBuilder

Collection de fonctions Tkinter définies dans ``gui_builder.py``.

- ``create_tab(notebook, title, style="Modern.TFrame", padding=20)`` – ajoute un
  onglet.
- ``create_a_frame(parent, style="Modern.TFrame", ...)`` – crée un conteneur.
- ``create_labeled_frame(parent, text="", ...)`` – cadre avec titre.
- ``create_modern_label_with_grid(frame, text, row, col, ...)`` – label stylisé.
- ``create_modern_entry_with_grid(frame, var, row, col, ...)`` – champ de saisie
  classique.
- ``create_modern_entry_with_grid_for_password(frame, var, row, col, ...)`` –
  champ de mot de passe.
- ``create_combobox(frame, var, values, row, col, ...)`` – menu déroulant.
- ``create_button_with_style(frame, text, command, ...)`` – bouton stylisé.
- ``create_button_without_style(frame, text, command, ...)`` – bouton simple.


## Exemple minimal

```python
from config_manager import ConfigManager
from selenium_driver_manager import SeleniumDriverManager
from saisie_automatiser_psatime import PSATimeAutomation, TimeSheetHelper

cfg = ConfigManager().load()
filler = PSATimeAutomation("log.html", cfg)

with SeleniumDriverManager("log.html") as dm:
    driver = filler.setup_browser(dm)
    creds = filler.initialize_shared_memory()
    filler.login_handler.login(
        driver, creds, filler.context.encryption_service
    )
    TimeSheetHelper("log.html").run(driver)
```

