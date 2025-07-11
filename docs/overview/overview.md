# Aperçu du projet

Le **sele_saisie_auto** vise à automatiser la saisie de la feuille de temps PSA Time.
Il pilote le navigateur avec Selenium et propose une interface Tkinter pour fournir les identifiants.
L'objectif est de gagner du temps sur cette tâche répétitive tout en restant simple à intégrer dans d'autres outils.

## Fonctionnalités principales

* Interface graphique simple pour saisir les identifiants et lancer l'automatisation
* Chiffrement AES des identifiants stockés dans `config.ini`
* Remplissage automatique des jours et tâches PSA Time via Selenium
* Journalisation HTML pour suivre l'exécution
* Système de plugins permettant d'ajouter des hooks personnalisés (voir `examples/example_plugin.py`)

## Mise en route rapide

```bash
poetry install --no-root
poetry run psatime-launcher
```
Cette commande effectue automatiquement la phase `prepare` avant de lancer
`PageNavigator.run()`.

Pour aller plus loin, référez-vous à [../guides/installation.md](../guides/installation.md) et [../index.md](../index.md).

## Chaîne ExtraInfoHelper -> DescriptionProcessor -> ElementFillingStrategy

Lorsque les informations supplémentaires sont saisies, `ExtraInfoHelper`
appelle `process_description` du module `DescriptionProcessor`.
Chaque champ est alors rempli via un `ElementFillingStrategy` adapté
(`InputFillingStrategy` ou `SelectFillingStrategy`).

```mermaid
flowchart LR
    ExtraInfoHelper --> DescriptionProcessor
    DescriptionProcessor --> ElementFillingStrategy
```

