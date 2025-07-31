# Commandes pour les outils de qualité de code Python

Cette page récapitule les commandes utiles pour sept outils courants de formatage, de linting et d'analyse de code. Chaque tableau sépare les commandes fréquemment utilisées des options avancées. Les liens vers PyPI permettent d'accéder rapidement à la documentation de chaque outil.

**Note :** Pour ce projet, qui fonctionne avec **Poetry**, ajouter le préfixe :  
`poetry run` avant chaque commande.

**Exemple :** Vérification lors d'un PR Brouillon  
```bash
poetry run mypy --strict --no-incremental src\sele_saisie_auto\navigation\page_navigator.py
````

## Commandes rapides à faire pour Vérification lors d'un PR Brouillon
```bash
poetry run mypy --strict --no-incremental src\

poetry run isort --check-only .
poetry run isort --check-only . > reports/isort/isort_check.txt

poetry run black --check . > reports/black/black_check.txt
poetry run black --diff . > reports/black/black_diff.txt

poetry run ruff check . > reports/ruff/ruff_check.txt
poetry run ruff check . --output-format=json > reports/ruff/ruff_check.json

poetry run flake8 .
poetry run flake8 --output-file=reports/flake8/flake8_report.txt .
poetry run flake8 . --max-complexity=10

poetry run pylint src\
```


## Black - Formatage de code

**PyPI :** [https://pypi.org/project/black/](https://pypi.org/project/black/)

### Commandes courantes

| Commande                                          | Description                                         | Chemin de sortie                |
| ------------------------------------------------- | --------------------------------------------------- | ------------------------------- |
| `black .`                                         | Formate tout le code du répertoire courant          | N/A                             |
| `black --check . > reports/black/black_check.txt` | Vérifie la mise en forme sans modifier les fichiers | `reports/black/black_check.txt` |
| `black --diff . > reports/black/black_diff.txt`   | Affiche le diff des modifications éventuelles       | `reports/black/black_diff.txt`  |

### Commandes avancées

| Commande                          | Description                             | Chemin de sortie                                 |     |
| --------------------------------- | --------------------------------------- | ------------------------------------------------ | --- |
| \`black --exclude "migrations     | venv" .\`                               | Exclut les dossiers correspondant au motif regex | N/A |
| `black --line-length 100 .`       | Utilise 100 caractères par ligne        | N/A                                              |     |
| `black --config pyproject.toml .` | Lit les options depuis `pyproject.toml` | N/A                                              |     |

## isort - Tri des imports

**PyPI :** [https://pypi.org/project/isort/](https://pypi.org/project/isort/)

### Commandes courantes

| Commande                                               | Description                              | Chemin de sortie                |
| ------------------------------------------------------ | ---------------------------------------- | ------------------------------- |
| `isort .`                                              | Trie et formate les imports en place     | N/A                             |
| `isort --check-only . > reports/isort/isort_check.txt` | Vérifie le tri des imports sans modifier | `reports/isort/isort_check.txt` |
| `isort --diff . > reports/isort/isort_diff.txt`        | Montre le diff des corrections possibles | `reports/isort/isort_diff.txt`  |

### Commandes avancées

| Commande                  | Description                                      | Chemin de sortie |
| ------------------------- | ------------------------------------------------ | ---------------- |
| `isort --profile black .` | Adapte le tri des imports au style Black         | N/A              |
| `isort --atomic .`        | Applique les changements de manière atomique     | N/A              |
| `isort --recursive .`     | Recherche récursivement tous les fichiers Python | N/A              |

## Bandit - Analyse de sécurité

**PyPI :** [https://pypi.org/project/bandit/](https://pypi.org/project/bandit/)

### Commandes courantes

| Commande                                                   | Description                          | Chemin de sortie                    |
| ---------------------------------------------------------- | ------------------------------------ | ----------------------------------- |
| `bandit -r . -f txt -o reports/bandit/bandit_report.txt`   | Analyse de sécurité et rapport texte | `reports/bandit/bandit_report.txt`  |
| `bandit -r . -f html -o reports/bandit/bandit_report.html` | Rapport HTML interactif              | `reports/bandit/bandit_report.html` |
| `bandit -r . -f json -o reports/bandit/bandit_report.json` | Rapport JSON utilisable en CI        | `reports/bandit/bandit_report.json` |

### Commandes avancées

| Commande                                                                            | Description                                                | Chemin de sortie                            |
| ----------------------------------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------- |
| `bandit -r . -b baseline.json -f html -o reports/bandit/bandit_after_baseline.html` | Ignore les vulnérabilités présentes dans `baseline.json`   | `reports/bandit/bandit_after_baseline.html` |
| `bandit -r . -lll -iii`                                                             | Filtre sur la sévérité **Haute** et la confiance **Haute** | N/A                                         |
| `bandit -r . -c bandit.yaml -f txt -o reports/bandit/bandit_custom.txt`             | Utilise un fichier de configuration personnalisé           | `reports/bandit/bandit_custom.txt`          |

## Radon - Complexité cyclomatique

**PyPI :** [https://pypi.org/project/radon/](https://pypi.org/project/radon/)

### Commandes courantes

| Commande           | Description                                             | Chemin de sortie |
| ------------------ | ------------------------------------------------------- | ---------------- |
| `radon cc . -s -a` | Calcule la complexité cyclomatique et la moyenne projet | N/A              |
| `radon mi .`       | Calcule l'indice de maintenabilité                      | N/A              |
| `radon raw .`      | Affiche les métriques brutes de chaque fichier          | N/A              |

### Commandes avancées

| Commande                                             | Description                                | Chemin de sortie                |
| ---------------------------------------------------- | ------------------------------------------ | ------------------------------- |
| `radon cc src/ -j -O reports/radon/cc_report.json`   | Rapport JSON de la complexité cyclomatique | `reports/radon/cc_report.json`  |
| `radon mi src/ -j -O reports/radon/mi_report.json`   | Rapport JSON de l'indice de maintenabilité | `reports/radon/mi_report.json`  |
| `radon raw src/ -j -O reports/radon/raw_report.json` | Rapport JSON des métriques brutes          | `reports/radon/raw_report.json` |
| `radon hal src/ -j -O reports/radon/hal_report.json` | Rapport JSON des métriques de Halstead     | `reports/radon/hal_report.json` |

## Ruff - Lint

**PyPI :** [https://pypi.org/project/ruff/](https://pypi.org/project/ruff/)

### Commandes courantes

| Commande                                                           | Description                                      | Chemin de sortie               |
| ------------------------------------------------------------------ | ------------------------------------------------ | ------------------------------ |
| `ruff check . > reports/ruff/ruff_check.txt`                       | Lint complet du code et rapport texte            | `reports/ruff/ruff_check.txt`  |
| `ruff check --fix . > reports/ruff/ruff_fix.txt`                   | Applique les correctifs automatiques disponibles | `reports/ruff/ruff_fix.txt`    |
| `ruff format . --check --diff > reports/ruff/ruff_diff.txt`        | Vérifie le formatage Black et montre le diff     | `reports/ruff/ruff_diff.txt`   |
| `ruff check . --output-format=json > reports/ruff/ruff_check.json` | Produit un rapport JSON                          | `reports/ruff/ruff_check.json` |

### Commandes avancées

| Commande                    | Description                                           | Chemin de sortie |
| --------------------------- | ----------------------------------------------------- | ---------------- |
| `ruff rule F401`            | Affiche le détail de la règle `F401`                  | N/A              |
| `ruff check . --statistics` | Montre un résumé par règle après l'analyse            | N/A              |
| `ruff clean`                | Vide le cache de Ruff                                 | N/A              |
| `ruff check --select E,F .` | Ne lance que les règles commençant par **E** et **F** | N/A              |

## Flake8 - Lint

**PyPI :** [https://pypi.org/project/flake8/](https://pypi.org/project/flake8/)

### Commandes courantes

| Commande                                                  | Description                                | Chemin de sortie                   |
| --------------------------------------------------------- | ------------------------------------------ | ---------------------------------- |
| `flake8 .`                                                | Analyse le code selon PEP8 et PyFlakes     | N/A                                |
| `flake8 --statistics --count .`                           | Résumé final du nombre d'erreurs           | N/A                                |
| `flake8 --output-file=reports/flake8/flake8_report.txt .` | Exporte le rapport complet dans un fichier | `reports/flake8/flake8_report.txt` |

### Commandes avancées

| Commande                       | Description                                          | Chemin de sortie |
| ------------------------------ | ---------------------------------------------------- | ---------------- |
| `flake8 . --max-complexity=10` | Signale les fonctions dépassant une complexité de 10 | N/A              |
| `flake8 . --exit-zero`         | Retourne toujours un code de sortie 0                | N/A              |
| `flake8 . --ignore=E501,W503`  | Ignore les règles `E501` et `W503`                   | N/A              |
| `flake8 . --select=F,E`        | Ne rapporte que les catégories **F** et **E**        | N/A              |

## MyPy - Type checking

**PyPI :** [https://pypi.org/project/mypy/](https://pypi.org/project/mypy/)

### Commandes courantes

| Commande                          | Description                                        | Chemin de sortie |
| --------------------------------- | -------------------------------------------------- | ---------------- |
| `mypy .`                          | Vérifie les annotations de type sur tout le projet | N/A              |
| `mypy . --ignore-missing-imports` | Ignore les imports sans stubs de type              | N/A              |
| `mypy . --strict`                 | Active toutes les vérifications supplémentaires    | N/A              |

### Commandes avancées

| Commande                                                 | Description                                        | Chemin de sortie            |
| -------------------------------------------------------- | -------------------------------------------------- | --------------------------- |
| `mypy . --show-error-codes --pretty`                     | Affiche les codes d'erreur et un formatage lisible | N/A                         |
| `mypy . --html-report=reports/mypy/html`                 | Génère un rapport HTML                             | `reports/mypy/html`         |
| `mypy . --xml-report=reports/mypy/xml`                   | Génère un rapport XML                              | `reports/mypy/xml`          |
| `mypy . --txt-report=reports/mypy/txt`                   | Génère un rapport texte                            | `reports/mypy/txt`          |
| `mypy . --cobertura-xml-report=reports/mypy/cobertura`   | Génère un rapport Cobertura                        | `reports/mypy/cobertura`    |
| `mypy . --linecoverage-report=reports/mypy/linecoverage` | Génère un rapport de couverture de lignes          | `reports/mypy/linecoverage` |
| `mypy . --junit-xml=reports/mypy/junit.xml`              | Produit un rapport au format JUnit                 | `reports/mypy/junit.xml`    |

---

## Pylint - Lint

**PyPI :** [https://pypi.org/project/pylint/](https://pypi.org/project/pylint/)

### Commandes courantes

| Commande                                                                        | Description                  | Chemin de sortie                    |
| ------------------------------------------------------------------------------- | ---------------------------  | ----------------------------------- |
| `pylint your_module.py`                                                         | Analyse un module spécifique | N/A                                 |
| `pylint your_package/`                                                          | Analyse un package entier    | N/A                                 |
| `pylint --output-format=text your_module.py > reports/pylint/pylint_report.txt` | Exporte le rapport en texte  | `reports/pylint/pylint_report.txt`  |
| `pylint --output-format=json your_module.py > reports/pylint/pylint_report.json`| Exporte le rapport en JSON   | `reports/pylint/pylint_report.json` |

### Commandes avancées

| Commande                                                 | Description                                          | Chemin de sortie |
| -------------------------------------------------------- | ---------------------------------------------------- | ---------------- |
| `pylint --rcfile=.pylintrc your_module.py`               | Utilise un fichier de configuration personnalisé     | N/A              |
| `pylint --disable=C0301,W0611 your_module.py`            | Désactive des messages spécifiques                   | N/A              |
| `pylint --enable=R0913 your_module.py`                   | Active des messages spécifiques                      | N/A              |
| `pylint --score=no your_module.py`                       | N'affiche pas le score final                         | N/A              |
| `pylint --reports=y your_module.py`                      | Affiche des rapports supplémentaires                 | N/A              |
