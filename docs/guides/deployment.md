# Guide de déploiement

Ce guide explique comment construire et lancer l'application avec Docker.

## 1. Construire l'image

```bash
docker build -t sele-app .
```

L'image compile l'application puis copie les fichiers dist dans Nginx.

## 2. Démarrer le conteneur

```bash
docker run -d -p 8080:80 --name sele sele-app
```

Accédez à `http://localhost:8080` pour voir l'application.

## 3. Mettre à jour l'image

Si le code ou le `Dockerfile` (à la racine du dépôt) change, reconstruisez l'image :

```bash
docker build --pull -t sele-app .
docker stop sele && docker rm sele
docker run -d -p 8080:80 --name sele sele-app
```

### Recréer l'image sans utiliser le cache

Si vous souhaitez forcer la reconstruction complète, ajoutez `--no-cache` :

```bash
docker build --no-cache -t sele-app .
```

## 4. Exemple minimal de `docker-compose.yml`

```yaml
version: "3"
services:
  app:
    build: .
    image: sele-app
    ports:
      - "8080:80"
```
