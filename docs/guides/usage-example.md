# Usage classique de l'outil

Pour executer la commande classique :
```bash
poetry run sele-saisie-auto run config.ini
```

Ce guide présente l'utilisation la plus simple de la bibliothèque.

## Scénario "utilisation basique"

L'utilisateur dispose d'un fichier `config.ini` minimal et souhaite renseigner sa feuille de temps sans interface graphique.

### Commande

```bash
poetry run psatime-auto
```

Cette commande lit `config.ini` dans le répertoire courant et lance directement l'automatisation. Un fichier de log est créé automatiquement sous `logs/` si aucun chemin n'est spécifié.

### Exemple de configuration minimale

```ini
[credentials]
login = enc_login
mdp = enc_pwd

[settings]
url = http://example.com
date_cible = 01/07/2024
liste_items_planning = "En mission"

[work_schedule]
lundi = En mission,8

[project_information]
billing_action = Facturable

[additional_information_rest_period_respected]
lundi = Oui

[additional_information_work_time_range]
lundi = 8-16

[additional_information_half_day_worked]
lundi = Non

[additional_information_lunch_break_duration]
lundi = 1

[work_location_am]
lundi = CGI

[work_location_pm]
lundi = CGI

[cgi_options_billing_action]
Facturable = B
```

### PSATIME_AES_KEY

Lors du lancement, l'outil génère une clé AES aléatoire de 32 octets avec
``os.urandom``. Cette clé sert à chiffrer les identifiants et est placée en
mémoire partagée (segment ``memoire_partagee_cle``). Aucune information n'est
écrite sur le disque.

Vous pouvez aussi prédéfinir la variable d'environnement ``PSATIME_AES_KEY``
pour fournir votre propre clé (format hexadécimal ou Base64). Si cette variable
est absente, la clé est créée à chaque exécution puis effacée à la fermeture
du programme.
