# Guide d’installation

Ce guide explique comment installer et utiliser localement le **sele_saisie_auto**.

1. **Pré-requis**
2. **Installation**
3. **Sans Poetry : création d’un environnement virtuel**
4. **Lancement de la CLI**
5. **Exécution des tests**

   ```bash
   poetry run pre-commit run --all-files
   poetry run pytest
   ```

La couverture doit rester supérieure à 95 %.

---

## Dépannage

Pour exécuter la CLI :

```bash
poetry run sele-saisie-auto --help
poetry run sele-saisie-auto run config.ini
```

