# Cycle des logs et des messages

Ce document illustre la circulation des messages lors d’une résolution.

## Étapes principales


```mermaid

```

Le cycle garantit que chaque erreur est journalisée et qu’un message clair est
retourné à l’utilisateur.

## Rediriger les logs vers un fichier

Pour conserver l'historique des événements, configurez un `......`
en complément du handler par défaut :

```python

```

Si la CLI propose l'option `--debug`, activez-la pour obtenir les messages au niveau `DEBUG` dans ce fichier.
