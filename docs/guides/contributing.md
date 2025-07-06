# Contribution

Merci de contribuer à ce projet ! 🙌
Voici les étapes et conventions à respecter avant de proposer une Pull Request (PR).

Pour la description des différents agents, consultez [AGENT.md](../../AGENT.md).

---

## 🔧 Configuration de l’environnement

Vérifie d’abord que Poetry est disponible :

```bash
poetry --version
```

Si la commande est introuvable, lance `scripts/install_poetry_windows.ps1` ou
consulte le [guide d’installation](installation.md).

Installe les dépendances et les hooks Git :

```bash
poetry install
pre-commit install
```

Ces commandes installent les dépendances de développement et configurent les
hooks `pre-commit`.
Pour installer sans l'environnement isol de Poetry, utilisez :
```bash
poetry install --no-root
```

Pour lancer l'automatisation en ligne de commande :
```bash
poetry run psatime-auto
```
Pour démarrer l'interface graphique :
```bash
poetry run psatime-launcher
```
L'ancienne commande reste possible :
```bash
python saisie_automatiser_psatime.py
```
Les scripts lisent leurs paramètres dans `config.ini`. Vérifiez son contenu avant exécution.


---

## 🧪 Avant de proposer une Pull Request

1. **Vérifie la qualité du code :**

   ```bash
   poetry run pre-commit run --all-files
   ```

2. **Lance les tests :**

   ```bash
   poetry run pytest
   ```

   > Voir [cli-tests.md](cli-tests.md) pour plus de détails.

3. **Respecte les hooks :**

   Le script `pre-commit` s'exécute automatiquement :

   ```bash
   pre-commit run
   ```

   à chaque commit.
   Si le hook échoue, corrige les erreurs signalées avant de recommitter.

4. **Style de code :**
Le formatage et l’analyse statique sont appliqués via des hooks pre-commit :
```bash
poetry run black src tests
poetry run isort src tests
poetry run mypy src
```
Exécutez poetry run pre-commit run --all-files avant de valider pour vérifier automatiquement ces règles.

5. **Exécution des tests :**
Lancez l’ensemble de la suite de tests avec :
```bash
poetry run pytest
```
Utilisez cette commande avant d’ouvrir une pull request pour vous assurer que tout fonctionne correctement.


---

### 📦 Pull Request : instructions de fusion
- **Titre** : `[<nom_agent>] <Résumé concis>`
- **Description** :
  1. Contexte et objectif, écrit en français
  2. Étapes pour tester, écrit en français
  3. Impact éventuel sur les autres agents, écrit en français
  4. CodecovIA : ajouter à la fin du commentaire PR :
      - `@codecov-ai-reviewer review`
      - `@codecov-ai-reviewer test`
  5. Avant d’ouvrir la PR :
      - exécuter `poetry install` et `poetry.lock`
      - exécuter `poetry run pre-commit run --all-files`, `poetry run pytest` et `poetry run pytest --cov=sele_saisie_auto --cov-report=term-missing`. Les deux doivent réussir. Si erreur, corrige-les avant d’ouvrir la PR.
      - executer `poetry run ruff check >/tmp/ruff.log` et `poetry run ruff check . --fix`. Les controles doivent réussir. Si erreur, corrige-les en acceptant les modifications de ruff avant d’ouvrir la PR.
      - exécuter `poetry run radon cc src/ -s` et `poetry run radon mi src/`. Pour produire un rapport HTML, installe d’abord le plugin [`radon-html`](https://pypi.org/project/radon-html/) via `poetry add --group dev radon-html` puis lance `poetry run radon html src/ -o radon-report`. Les contrôles doivent réussir. Si erreur, corrige-les avant d’ouvrir la PR.
      - executer `poetry run bandit -r src/` et `poetry run bandit -r src/ -lll -iii`. Les controles doivent réussir. Si erreur, corrige-les avant d’ouvrir la PR.

  6. Création de branche
     
  Utilise **une branche par fonctionnalité ou correctif**, selon la convention suivante :

  | Type de branche | Préfixe recommandé     | Exemple                                  |
  |-----------------|------------------------|------------------------------------------|
  | Fonctionnalité  | `feature/` ou `feat/`  | `feature/inscription-utilisateur`        |
  | Nouvelles règles métier  | `feature/` ou `feat/`  | `feature/gestion-rg-metier-x`        |
  | Correctif       | `bugfix/` ou `fix/`    | `bugfix/correction-affichage-date`       |
  | Refactorisation | `refactor/`            | `refactor/simplification-formulaires`    |
  | Documentation   | `docs/`                | `docs/ajout-guide-installation`          |
  | Hotfix          | `hotfix/`              | `hotfix/patch-urgent-en-prod`            |
  | Environnement   | `release/`             | `release/staging` ou `release/1.2.0`     |

---

## 💡 Stack technique

Ce projet repose exclusivement sur **Python, Tkinter et Selenium** et les outils suivants :

- [Poetry](https://python-poetry.org/) pour la gestion des dépendances
- [pytest](https://docs.pytest.org/) pour les tests
- [pre-commit](https://pre-commit.com/) pour les hooks de qualité

### ⚠️ Conventions à respecter

- Ne pas ajouter d’autres bibliothèques UI (Material, Antd, etc.).
- Respecter le style de code existant.
- Utiliser les composants réutilisables lorsqu’ils existent.

---

Merci pour ta contribution ! 🚀
