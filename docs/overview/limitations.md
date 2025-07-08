# Limitations connues

- Python 3.x ou version supérieure requis.
- L'algorithme est prévu pour s'exécuter en quelques secondes, suivant la
  vitesse de la connexion et de la machine.
- Navigateur recommandé : **Edge Chromium**. L'outil fonctionne également avec
  **Chrome** et **Firefox**, à condition d'avoir les drivers installés.
- Safari n'a pas été testé et peut présenter des incompatibilités.
- Certains sites peuvent détecter l'utilisation de Selenium et bloquer
  l'automatisation. Une mise à jour du code peut être nécessaire si la page
  change ou si un mécanisme anti-bot est activé.



## Limites de débit

Aucun mécanisme de limitation n'est inclus. Si le sele_saisie_auto est exposé via un
service web, prévoyez un contrôle de taux pour éviter les abus.
Pour plus de détails, consultez le [guide de déploiement](../guides/deployment.md).

## Formats d'entrée

Les paramètres sont lus depuis un fichier `config.ini` situé à la racine du
projet. Ce fichier contient principalement la section `[settings]`.

Le chemin du fichier peut être passé en argument lors de l'exécution. Si aucun
chemin n'est fourni, une copie du `config.ini` embarqué est générée dans le
répertoire courant.

Chaque option peut être surchargée via les variables d'environnement
suivantes :

- `PSATIME_URL` — URL du portail PSA Time
- `PSATIME_DATE_CIBLE` — date cible au format `JJ/MM/AAAA`
- `PSATIME_DEBUG_MODE` — niveau de log (`INFO`, `DEBUG`, …)
- `PSATIME_LISTE_ITEMS_PLANNING` — liste d'items séparés par des virgules
- `PSATIME_DEFAULT_TIMEOUT` — délai d'attente par défaut pour Selenium
- `PSATIME_LONG_TIMEOUT` — délai prolongé pour certaines opérations

Les variables d'environnement ont priorité sur le fichier `config.ini`.
Un fichier `.env` peut également être présent ; ses valeurs sont chargées mais
sont remplacées si la même variable existe déjà dans l'environnement système.
