# Guide d’installation

Ce guide explique comment installer et utiliser localement **sele_saisie_auto**.

## 1. Pré-requis

- Python 3.11 installé
- Poetry disponible dans le `PATH`

## 2. Installation

Lancez :

```bash
poetry install --no-root
```

Cette commande installe les dépendances définies dans `pyproject.toml`.

## 3. Sans Poetry : création d’un environnement virtuel

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Lancement de la CLI

Depuis la racine du projet :

```bash
poetry run sele-saisie-auto --help
poetry run sele-saisie-auto run config.ini
```

## 5. Exécution des tests

```bash
poetry run pre-commit run --all-files
poetry run pytest
```

La couverture doit rester supérieure à 95 %.

---

## Dépannage

- **Version de Selenium** : si l’outil signale une incompatibilité, vérifiez la
  version indiquée dans `pyproject.toml` puis exécutez `poetry update selenium`.
- **Permissions insuffisantes** : si un script refuse de s’exécuter, appliquez
  `chmod +x` sur le fichier ou ajustez les droits du dossier.

