# Limitations connues

- Python 3.x ou version supérieure requis.
- L'algorithme vise un temps d'exécution inférieur à ``.
- Selenium testé principalement avec **Chrome** et **Firefox**.
- Certains sites peuvent détecter l'automatisation et bloquer l'accès.



## Limites de débit

Aucun mécanisme de limitation n'est inclus. Si le sele_saisie_auto est exposé via un
service web, prévoyez un contrôle de taux pour éviter les abus.
Pour plus de détails, consultez le [guide de déploiement](../guides/deployment.md).

## Formats d'entrée

Les paramètres sont lus depuis un fichier `config.ini` situé à la racine du
projet. Ce fichier contient notamment les sections `[credentials]` et
`[settings]`.

Chaque option peut être surchargée via les variables d'environnement
suivantes :

- `PSATIME_URL` — URL du portail PSA Time
- `PSATIME_DATE_CIBLE` — date cible au format `JJ/MM/AAAA`
- `PSATIME_LOGIN` — identifiant chiffré
- `PSATIME_MDP` — mot de passe chiffré
- `PSATIME_DEBUG_MODE` — niveau de log (`INFO`, `DEBUG`, …)
- `PSATIME_LISTE_ITEMS_PLANNING` — liste d'items séparés par des virgules

Les variables d'environnement ont priorité sur le fichier `config.ini`.
