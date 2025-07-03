# Aperçu du projet

Le **sele_saisie_auto** est une application Python permettant d'automatiser la saisie de la feuille de temps PSA Time.
Il combine Selenium pour piloter le navigateur et Tkinter pour l'interface graphique.
L'objectif est de gagner du temps lors du remplissage hebdomadaire tout en restant facile à intégrer dans d'autres projets.

## Fonctionnalités principales

* Interface graphique simple pour saisir les identifiants et lancer l'automatisation
* Chiffrement AES des identifiants stockés dans `config.ini`
* Remplissage automatique des jours et tâches PSA Time via Selenium
* Journalisation HTML pour suivre l'exécution
* Système de plugins permettant d'ajouter des hooks personnalisés

## Mise en route rapide

```bash
poetry install --no-root
poetry run psatime-launcher
```

Pour aller plus loin, référez-vous à [../guides/installation.md](../guides/installation.md) et [../index.md](../index.md).
