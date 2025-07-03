# Guide de configuration

Ce guide explique comment ajuster les limites d’exécution et les options de traitement.

## 1. Limites de sécurité

Les paramètres de sécurité sont définis dans `src/`.



## 2. Constantes d’application

| Constante   | Description                           | Valeur par défaut |
| ----------- | ------------------------------------- | ----------------- |
| TIMEOUT     | Délai maximum pour chaque étape       | 30                |
| RETRY_LIMIT | Nombre de tentatives autorisées       | 3                 |

Modifiez ces valeurs dans `config.ini` ou via des variables d’environnement si besoin.

## 3. Exemple de fichier `.env`

```dotenv
TIMEOUT=60
RETRY_LIMIT=5
```

```python
manager = ConfigManager()
cfg = manager.config
timeout = int(cfg.get("settings", "timeout", fallback="30"))
```

## 4. Conseils pour la production


