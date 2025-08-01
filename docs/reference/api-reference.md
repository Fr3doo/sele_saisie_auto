# Référence API

Cette section décrit brièvement les principales classes exposées par le projet.


## SeleniumFiller (``PSATimeAutomation``)

Classe principale localisée dans ``saisie_automatiser_psatime.py``. Elle pilote
le navigateur Selenium pour remplir la feuille de temps.

```python
class PSATimeAutomation:
    def __init__(
        self,
        log_file: str,
        app_config: AppConfig,
        memory_config: MemoryConfig | None = None,
    ) -> None:
        """Prépare la configuration et les services nécessaires."""
    def __enter__(self) -> PSATimeAutomation:
        """Ouvre le ``ResourceManager`` interne."""

    def __exit__(self, exc_type, exc, tb) -> None:
        """Ferme toutes les ressources via le ``ResourceManager``."""
```

- ``run() -> None`` – lance toute la séquence d’automatisation. Cette méthode délègue maintenant à ``AutomationOrchestrator.run()``.

Les fonctions de navigation détaillées ont été retirées de cette classe. Pour piloter manuellement le processus, instanciez ``AutomationOrchestrator`` puis appelez
``PageNavigator.prepare(credentials, date_cible)`` pour injecter le contexte,
puis ``PageNavigator.run(driver)``.

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

## ServiceConfigurator

Configure la création des services principaux (``service_configurator.py``).

```python
class ServiceConfigurator:
    def create_encryption_service(self, log_file: str) -> EncryptionService:
        """Retourne un service de chiffrement."""
    def create_waiter(self) -> Waiter:
        """Prépare un ``Waiter`` standard."""
    def create_browser_session(self, log_file: str) -> BrowserSession:
        """Instancie la session navigateur."""
    def build_services(self, log_file: str) -> Services:
        """Renvoie tous les services prêts à l'emploi."""
```

Fonction utilitaire :

- ``build_services(app_config, log_file) -> Services`` – crée directement l'ensemble.

## ResourceManager

Gestionnaire de contexte centralisant configuration, chiffrement et navigateur
(``resource_manager.py``).

```python
class ResourceManager:
    def __enter__(self) -> ResourceManager:
        """Charge la configuration et prépare les services."""
    def __exit__(self, exc_type, exc, tb) -> None:
        """Ferme proprement les ressources."""
    def close(self) -> None:
        """Alias explicite de ``__exit__``."""
    def get_credentials(self) -> Credentials:
        """Retourne les identifiants chiffrés."""
    def get_driver(self, *, headless=False, no_sandbox=False):
        """Ouvre le navigateur si nécessaire."""
```

## Resource access helpers

Fonctions utilitaires pour récupérer les identifiants ou ouvrir le navigateur en
s'appuyant directement sur ``EncryptionService`` et ``BrowserSession``.

```python
from sele_saisie_auto.resources.accessors import get_credentials, get_driver

creds = get_credentials(encryption_service)
driver = get_driver(
    browser_session,
    "https://example.com",
    headless=True,
    no_sandbox=True,
)
```

## PageNavigator

Orchestre la navigation entre les différentes pages PSA Time
(``page_navigator.py``).

```python
class PageNavigator:
    def prepare(self, credentials: Credentials, date_cible: str) -> None:
        """Stocke les informations nécessaires pour ``run()``."""
    def run(self, driver) -> None:
        """Enchaîne connexion, saisie et validation."""
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
from configuration import ServiceConfigurator
from saisie_automatiser_psatime import PSATimeAutomation
from orchestration import AutomationOrchestrator

cfg = ConfigManager().load()
service_configurator = ServiceConfigurator(cfg)
services = service_configurator.build_services("log.html")

auto = PSATimeAutomation("log.html", cfg, services=services)
orchestrator = AutomationOrchestrator.from_components(
    auto.resource_manager,
    auto.page_navigator,
    service_configurator,
    auto.context,
    auto.logger,
)
orchestrator.run()

# Pour un contrôle manuel
with auto.resource_manager as rm:
    creds = rm.initialize_shared_memory(auto.logger)
    driver = rm.get_driver()
    auto.page_navigator.prepare(creds, cfg.date_cible)
    auto.page_navigator.run(driver)
```

