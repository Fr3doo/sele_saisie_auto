# Aperçu du projet

Le **sele_saisie_auto** vise à automatiser la saisie de la feuille de temps PSA Time.
Il pilote le navigateur avec Selenium et propose une interface Tkinter pour fournir les identifiants.
L'objectif est de gagner du temps sur cette tâche répétitive tout en restant simple à intégrer dans d'autres outils.

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
