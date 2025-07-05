# Installer Poetry sous Windows

Ce guide explique comment ajouter **Poetry** sur un poste Windows.

## 1. Installation via PowerShell

Ouvrez une invite PowerShell puis lancez :

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

## 2. Finaliser l'installation

Fermez puis rouvrez votre terminal pour que la commande soit disponible.

Vérifiez ensuite l'installation :

```bash
poetry --version
```

La version courante s'affiche si tout s'est bien passé.

