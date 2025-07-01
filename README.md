# sele_saisie_auto

[![Licence](https://img.shields.io/badge/license-Unlicense-lightgrey.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](#)
[![CI](https://img.shields.io/badge/CI-GitHub_Actions-inactive.svg)](#)
[![Coverage](https://img.shields.io/badge/coverage-0%25-red.svg)](#)

## 🚀 Objectif du projet
Automatiser la saisie de la feuille de temps PSA Time via Selenium et une interface Tkinter.

## 🧰 Stack technologique
- Python 3.11
- Selenium 4.25
- Cryptography 43.0
- Dev: pytest, flake8, mypy, black, isort, ruff, radon, bandit, safety

## ⚡ Démarrage rapide
```bash
poetry install --no-root
poetry run python main.py
```

## 🔧 Installation
### Pré-requis système
- Python 3.11 et [Poetry](https://python-poetry.org/)

### Depuis les sources
```bash
pip install -r requirements.txt
```

### Mode développement
```bash
poetry install
```

### Environnement virtuel
Poetry gère automatiquement l'environnement virtuel du projet.

## ▶️ Lancement
Après installation :
```bash
poetry run python main.py
```

## 📦 Utilisation
Une interface graphique Tkinter permet de renseigner vos identifiants chiffrés et déclenche l'automatisation Selenium.

## ⚙️ Utilisation avancée
- Configuration dans `config.ini`
- Logs générés dans le dossier `logs/`

## 🔌 Injection de dépendances
Certaines fonctions acceptent les modules Selenium ou Logger en paramètres pour faciliter les tests. Voir [AGENT.md](AGENT.md) pour plus de détails.

## 📈 Collecte de métriques
TODO: intégrer un système de métriques (ex. Prometheus).

## ❗ Gestion des erreurs
Les exceptions sont journalisées via `logger_utils.py`. Reportez-vous à la documentation interne pour enrichir le mécanisme.

## 📝 Formats d'entrée
Les paramètres sont lus depuis `config.ini` (login, mot de passe chiffré, planning, etc.).

## 🧠 Architecture
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
Voir [AGENT.md](AGENT.md) pour la description complète des agents.

## 📁 Structure du projet
```
.
├── main.py
├── saisie_automatiser_psatime.py
├── encryption_utils.py
├── remplir_jours_feuille_de_temps.py
├── config.ini
├── tests/
└── ...
```

## 🖥️ Compatibilité Windows
L'utilisation de PyInstaller permet de générer un exécutable Windows (voir instructions dans `main.py`).

## 🛠️ Fichiers de configuration
- `config.ini` : paramètres de connexion et de planning
- `pytest.ini` : options de tests
- `.coveragerc` : configuration de couverture
- `.pre-commit-config.yaml` : hooks de lint et formatage

## 🧪 Tests
```bash
poetry run pre-commit run --all-files
poetry run pytest
```
Rapports de couverture disponibles dans `htmlcov/` via `pytest --cov-report html`.

## 🔍 Qualité du code
- Formatage : `black`
- Tri des imports : `isort`
- Lint : `flake8` et `ruff`
- Analyse de complexité : `radon`
- Analyse de sécurité : `bandit` et `safety`
- Typage statique : `mypy`

## 🤝 Contribuer
Les guidelines de contribution se trouvent dans [AGENT.md](AGENT.md). Ouvrez une issue avant toute grosse modification.

## 📚 Documentation liée
- [AGENT.md](AGENT.md) — rôles des différents agents
- [AGENT.md](AGENT.md) — guide de structuration des agents
- [TESTING.md](TESTING.md) — stratégie de tests et conseils

## 🚀 Publication d'une release
TODO: définir la procédure de publication (Git tag, packaging, PyPI).

## 🛡️ Licence
Aucune licence spécifiée pour l'instant.
