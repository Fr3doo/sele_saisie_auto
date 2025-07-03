# Changelog

Toutes les modifications importantes apportées à ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
et ce projet respecte le [versionnage sémantique](https://semver.org/spec/v2.0.0.html).

Ce changelog documente l'ensemble des évolutions du projet. Les modifications en cours
figurent sous la section **[Non publié]**. Lorsqu'une version est finalisée,
créez le tag Git correspondant et déplacez les entrées de cette section vers la
version publiée.

## [Non publié]
Modifications depuis la dernière version officielle.

### Ajouté

### Modifié
- Amélioration du démarrage du navigateur WebDriver

### Obsolète

### Supprimé

### Corrigé
- Correction du chemin par défaut du fichier de log sous Windows

### Sécurité


### Prévu

- Ajout d'un mode CLI pour exécuter l'automatisation sans interface graphique

## [0.1.0] - 2025-01-XX

### Ajouté
- Automatisation de la saisie de la feuille de temps PSA Time
- Interface graphique Tkinter pour renseigner les identifiants
- Chiffrement AES des données stockées dans `config.ini`
- Journaux HTML et système de plugins minimal
- Exemple de fichier `config.ini` fourni

### Performance
- Lancement en mode headless plus rapide

### Corrigé
- Correction de l'affichage de la fenêtre d'authentification

### Sécurité
- Renforcement des permissions du fichier de configuration

[Non publié]: ../../compare/0.1.0...HEAD 
[0.1.0]: ../../releases/tag/0.1.0 
