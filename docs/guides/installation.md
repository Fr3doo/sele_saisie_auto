# Guide d’installation

Ce guide explique comment installer et utiliser localement **sele_saisie_auto**.

## 1. Pré-requis

- Python 3.11 installé
- Poetry disponible dans le `PATH`

## 2. Installation pas-à-pas

1. Clonez le dépôt puis positionnez-vous dans le dossier :
   ```bash
   git clone <URL> sele_saisie_auto
   cd sele_saisie_auto
   ```
2. Installez les dépendances du projet :
   ```bash
   poetry install --no-root
   ```
3. Copiez le fichier `config.ini` si nécessaire et complétez vos identifiants.
4. Lancez enfin l'application via :
   ```bash
   poetry run psatime-launcher
   ```

Cette suite de commandes installe tous les modules définis dans `pyproject.toml`.
Pour générer un rapport de complexité au format HTML, ajoute également le plugin `radon-html` :
```bash
poetry add --group dev radon-html
```

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

