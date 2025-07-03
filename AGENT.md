# 🤖 Agent Guide – Projet sele_saisie_auto

## 1. Dev Environment Tips
> ℹ️ Comment configurer et lancer l’environnement local
- Installer les dépendances : `poetry install --no-root`
- Pour cibler un agent : exécuter directement le fichier Python correspondant (ex. `python saisie_automatiser_psatime.py`)
- Les scripts utilisent `config.ini` pour les paramètres. Vérifier son contenu avant exécution.

## 2. Testing Instructions
> ⚠️ Les modifications doivent passer tous les tests et le lint
- CI YAML : `.github/workflows/ci.yml` (non configuré pour le moment)
- Lancer les tests : `pytest`
- Pour un seul test : `pytest -k "<pattern>"`
- Après refactorings : `flake8` (ou autre outil de lint à configurer).

## 3. Pull Request (PR) Instructions
- **Titre** : `[<nom_agent>] <Résumé concis>`
- **Description** :
  1. Contexte et objectif en français
  2. Étapes pour tester
  3. Impact éventuel sur les autres agents
  4. CodecovIA : ajouter à la fin du commentaire PR :
      - `@codecov-ai-reviewer review`
      - `@codecov-ai-reviewer test`
  5. Avant d’ouvrir la PR :
      - exécuter `poetry install` et `poetry.lock`
      - exécuter `poetry run pre-commit run --all-files`, `poetry run pytest` et `poetry run pytest --cov=sele_saisie_auto --cov-report=term-missing`. Les deux doivent réussir. Si erreur, corrige-les avant d’ouvrir la PR.
      - executer `poetry run ruff .` et `poetry run ruff check . --fix`. Les controles doivent réussir. Si erreur, corrige-les en acceptant les modifications de ruff avant d’ouvrir la PR.
      - executer `poetry run radon cc src/ -s` et `poetry run radon mi src/` et `poetry run radon html src/ -o radon-report`. Les controles doivent réussir. Si erreur, corrige-les avant d’ouvrir la PR.
      - executer `poetry run bandit -r src/` et `poetry run bandit -r src/ -lll -iii`. Les controles doivent réussir. Si erreur, corrige-les avant d’ouvrir la PR.
      - executer `poetry run safety auth`, pour démarrer le flux d'authentification ou l'état d'affichage.  Les controles doivent réussir. 
      - executer `poetry run safety scan`, pour effectuer une analyse de vulnérabilité dans le répertoire actuel. Les controles doivent réussir. Si erreur, corrige-les avant d’ouvrir la PR.
      - executer `poetry run safety system-scan`, pour effectuez une analyse sur l’ensemble de la machine de développement. Les controles doivent réussir. Si erreur, corrige-les avant d’ouvrir la PR.
      - executer `poetry run safety scan --apply-fixes`, pour effectuez une mise à jour des dépendances vulnérables. Les controles doivent réussir. Si erreur, corrige-les avant d’ouvrir la PR.

## 4. Codex/ChatGPT Usage Tips
> 🔧 Conseils pour guider l’IA dans ce repo
- Limiter la recherche aux modules Python concernés (`*.py`).
- Fournir des extraits de stack trace ou de logs pour le débogage.
- Demander à l’agent de dessiner un diagramme ASCII/Mermaid avant d’écrire le code.
- Scinder les grandes tâches en étapes : réécriture, tests, documentation.

## 5. Vue d’ensemble des agents

| Agent                   | Rôle principal                                | Fichier                                   | Entrées               | Sorties                      |
|-------------------------|-----------------------------------------------|-------------------------------------------|-----------------------|------------------------------|
| `SeleniumFiller`        | Remplit la feuille de temps via Selenium      | `saisie_automatiser_psatime.py`           | Config, navigateur    | Feuille de temps complétée   |
| `TimeSheetHelper`       | Remplit les jours dans la grille              | `remplir_jours_feuille_de_temps.py`       | Driver, config        | Statut d’insertion           |
| `ExtraInfoHelper`       | Gère les informations supplémentaires         | `remplir_informations_supp_utils.py`      | Driver, config        | Champs complétés             |
| `ConfigManager`         | Lecture et préparation de `config.ini`        | `config_manager.py`  | Aucune                | Objet `ConfigParser`         |
| `EncryptionService`     | Chiffre/déchiffre les données sensibles       | `encryption_utils.py`                     | Chaîne ou bytes       | Bytes ou chaîne             |
| `Logger`                | Gestion et rotation des logs                  | `logger_utils.py`                         | Messages à enregistrer| Fichier HTML/TXT de logs     |
| `SeleniumDriverManager` | Initialise et ferme le WebDriver             | `selenium_driver_manager.py`             | URL, options          | Instance WebDriver |
| `SeleniumUtils`         | Fonctions utilitaires pour Selenium           | `selenium_utils/`             | WebDriver, ID, valeurs| Éléments manipulés          |
## 6. Détails par agent

### `SeleniumFiller`
- **Rôle** : Automatiser la saisie des temps dans PSA Time.
- **Entrées** : configuration, identifiants chiffrés, WebDriver.
- **Sorties** : feuille de temps validée ou messages d’erreur.
- **Dépendances** : `SeleniumUtils`, `TimeSheetHelper`, `ExtraInfoHelper`, `Logger`, `EncryptionService`.
- **Tests** : (non définis pour l’instant).

### `TimeSheetHelper`
- **Rôle** : Remplir les jours et missions.
- **Entrées** : driver Selenium, configuration des jours.
- **Sorties** : liste des jours remplis.
- **Dépendances** : `SeleniumUtils`, `Logger`, `ConfigManager`.
- **Tests** : TODO ajouter `tests/test_timesheet_helper.py`.

### `ExtraInfoHelper`
- **Rôle** : Insérer les informations supplémentaires demandées par CGI.
- **Entrées** : driver Selenium, configuration spécifique.
- **Sorties** : confirmation du remplissage.
- **Dépendances** : `SeleniumUtils`, `Logger`.
- **Tests** : TODO ajouter `tests/test_extra_info_helper.py`.

### `ConfigManager`
- **Rôle** : Charger `config.ini` à l’exécution, fournir les chemins pour PyInstaller.
- **Entrées** : chemin du fichier, options du système.
- **Sorties** : objet `ConfigParser` utilisé par les autres agents.
- **Dépendances** : `Logger`.
- **Tests** : TODO ajouter `tests/test_config_manager.py`.

### `EncryptionService`
- **Rôle** : Gérer la clé AES et la mémoire partagée.
- **Entrées** : données à chiffrer/déchiffrer.
- **Sorties** : données chiffrées ou déchiffrées.
- **Dépendances** : `Logger`.
- **Tests** : TODO ajouter `tests/test_encryption_service.py`.

### `SeleniumDriverManager`
- **Rôle** : Centraliser l'ouverture et la fermeture du WebDriver.
- **Entrées** : URL cible et options navigateur.
- **Sorties** : instance Selenium prête à l'emploi.
- **Dépendances** : `SeleniumUtils`, `Logger`.

## 7. Schéma d’interaction

```mermaid
graph TD
  subgraph UI
    A[Utilisateur] --> B(SeleniumFiller)
  end
  B --> C(TimeSheetHelper)
  B --> D(ExtraInfoHelper)
  B --> E(ConfigManager)
  B --> F(EncryptionService)
  C --> G(SeleniumUtils)
  D --> G
  E --> H(Logger)
  F --> H
```

## 8. Ajouter un nouvel agent

1. Isoler une responsabilité unique.
2. Créer un fichier Python dans `./` ou un sous-répertoire avec la classe ou fonction principale.
3. Documenter son rôle dans ce fichier et ici.
4. Ajouter des tests dans `tests/`.
5. Mettre à jour `AGENT.md`.

## 9. Meilleures pratiques

* Un agent = une responsabilité (Single Responsibility).
* Fonctions courtes pour faciliter les tests.
* Dépendances injectées.
* Logs détaillés pour faciliter le débogage.

## 10. TODOs & Améliorations
* [ ] Lier `AGENT.md` depuis le `README.md`.
* [ ] Créer un workflow GitHub Actions pour les tests (`ci.yml`).
* [ ] Ajouter des tests unitaires pour chaque agent.
* [ ] Automatiser la génération du diagramme Mermaid.
* [x] Documenter la procédure d’export en binaire via PyInstaller (voir `README.md`).

## 11. Interfaces détaillées des agents

### `EncryptionService` (`encryption_utils.py`)
Service chargé du chiffrement et de la mémoire partagée.

- `generer_cle_aes(taille_cle: int = 32) -> bytes` : génère une clé AES aléatoire.
- `chiffrer_donnees(donnees: str, cle: bytes, taille_bloc: int = 128) -> bytes` : chiffre un texte en AES‑CBC.
- `dechiffrer_donnees(donnees_chiffrees: bytes, cle: bytes, taille_bloc: int = 128) -> str` : déchiffre le résultat précédent.
- `stocker_en_memoire_partagee(nom: str, donnees: bytes) -> SharedMemory` : écrit des octets dans un segment partagé.
- `recuperer_de_memoire_partagee(nom: str, taille: int) -> tuple[SharedMemory, bytes]` : lit un segment existant.
- `supprimer_memoire_partagee_securisee(memoire: SharedMemory) -> None` : efface et supprime le segment.

### `ConfigManager` (`config_manager.py`)
Gestion centralisée du fichier `config.ini`.

- `load() -> ConfigParser` : charge la configuration depuis le disque.
- `save() -> str` : sauvegarde l'instance courante.
- `config` : propriété retournant l'objet `ConfigParser` actif.

### `GUIBuilder` (`gui_builder.py`)
Collection de fonctions pour créer les widgets Tkinter de l'application.

Principales fonctions :
- `create_tab(notebook, title, style="Modern.TFrame", padding=20) -> ttk.Frame`
- `create_a_frame(parent, style="Modern.TFrame", ...) -> ttk.Frame`
- `create_labeled_frame(parent, text="", ...) -> ttk.LabelFrame`
 - `create_modern_label_with_grid(frame, text, row, col, ...) -> ttk.Label`
 - `create_modern_entry_with_grid(frame, var, row, col, ...) -> ttk.Entry`
 - `create_modern_entry_with_grid_for_password(frame, var, row, col, ...) -> ttk.Entry`
- `create_combobox(frame, var, values, row, col, ...) -> ttk.Combobox`
- `create_button_with_style(frame, text, command, ...) -> ttk.Button`
- `create_button_without_style(frame, text, command, ...) -> tk.Button`

### `SeleniumDriverManager` (`selenium_driver_manager.py`)
Enveloppe simplifiée autour du WebDriver Selenium.

- `open(url: str, fullscreen=False, headless=False, no_sandbox=False) -> Optional[WebDriver]` : instancie le navigateur et prépare la page.
- `close() -> None` : ferme le navigateur si ouvert.

### `Logger Utils` (`logger_utils.py`)
Fonctions pour gérer les journaux applicatifs.

- `initialize_logger(config, log_level_override=None)` : applique le niveau de log défini.
- `write_log(message, log_file, level="INFO", log_format="html", auto_close=False, max_size_mb=5)` : écrit un message dans le fichier.
- `close_logs(log_file, log_format="html")` : ferme proprement le fichier de log.

### `Shared Utils` (`shared_utils.py`)
Fonctions de support communes.

- `setup_logs(log_dir="logs", log_format="html") -> str` : prépare le répertoire des logs et retourne le chemin du fichier.
- `get_log_file() -> str` : retourne le fichier de log courant, en l'initialisant si nécessaire.
- `program_break_time(memorization_time: int, affichage_text: str)` : affiche un compte à rebours dans la console.

## 12. Protocoles de messages
*(si des APIs ou sockets sont ajoutés)*

## 13. Surveillance & Performances

## 14. Gestion des erreurs
*(uniformiser les exceptions et messages)*

## 15. Points d’extension
*(plugins, hooks, etc.)*

## 16. Considérations de déploiement & sécurité
- Scalabilité (multiprocessing si besoin)
- Validation des entrées utilisateurs
- Limites de ressources Selenium

## 17. Documentation
*(compléter avec des guides pas à pas)*
