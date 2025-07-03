# Structure détaillée du projet

Ce document présente l’arborescence principale du dépôt pour localiser rapidement les fichiers essentiels.

```text
.
├── AGENT.md
├── README.md
├── TESTING.md
├── main.py
├── launcher.py
├── saisie_automatiser_psatime.py
├── remplir_jours_feuille_de_temps.py
├── app_config.py
├── config.ini
├── config_manager.py
├── docs/
│   ├── guides/
│   ├── overview/
│   ├── reference/
│   └── releases/
├── selenium_utils/
│   ├── __init__.py
│   ├── element_actions.py
│   ├── navigation.py
│   └── wait_helpers.py
├── tests/
│   ├── test_app_config.py
│   ├── test_saisie_automatiser_psatime.py
│   ├── test_remplir_jours_main_flow.py
│   └── ...
├── pyproject.toml
└── requirements.txt
```

Chaque dossier suit la philosophie « un rôle clair ». Les tests unitaires se trouvent dans `tests/`.

Le répertoire `docs/` regroupe l'ensemble de la documentation : guides pratiques,
références techniques et notes de versions. Le dossier `tests/` contient toutes
les suites de tests exécutées via `pytest` pour assurer la stabilité du projet.
