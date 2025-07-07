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

---

## 3. Problème : « poetry » non reconnu

Il se peut que `poetry.exe` soit bien installé mais que Windows ne trouve pas la commande car le dossier d'installation n'est pas dans votre variable d'environnement `PATH`.

### 3.1. Vérifier l'emplacement de `poetry.exe`

Dans PowerShell, exécutez :

```powershell
Test-Path "$env:APPDATA\Python\Scripts\poetry.exe"
Test-Path "$env:APPDATA\pypoetry\venv\Scripts\poetry.exe"
```

Chaque commande renverra `True` si le fichier existe. Notez les chemins exacts.

### 3.2. Ajouter les dossiers au `PATH`

#### a) Pour la session courante seulement

```powershell
$env:PATH += ";$env:APPDATA\Python\Scripts;$env:APPDATA\pypoetry\venv\Scripts"
```

#### b) Pour votre utilisateur (permanent)

```powershell
[Environment]::SetEnvironmentVariable(
  'PATH',
  "$env:PATH;$env:APPDATA\Python\Scripts;$env:APPDATA\pypoetry\venv\Scripts",
  'User'
)
```

> **Important :** Fermez **toutes** les fenêtres PowerShell puis rouvrez-en une nouvelle pour prendre en compte la modification.

### 3.3. Vérifier la mise à jour du `PATH`

Dans la nouvelle session PowerShell, tapez :

```powershell
echo $env:PATH
```

Vous devez voir, en fin de ligne, les chemins :

```
…;C:\Users\<votre_utilisateur>\AppData\Roaming\Python\Scripts;C:\Users\<votre_utilisateur>\AppData\Roaming\pypoetry\venv\Scripts
```

### 3.4. Validation finale

```powershell
poetry --version
```

Vous devriez obtenir :

```
Poetry (version 2.1.3)
```

---

## 4. Alternative : installation via pipx

Si vous préférez éviter les manipulations de `PATH`, utilisez :

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
pipx install poetry
```

Fermez puis rouvrez votre terminal, puis vérifiez :

```bash
poetry --version
```

