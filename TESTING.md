# 🧪 Guide de tests et couverture

---

## Installation des dépendances

Ce projet utilise **pytest** pour les tests unitaires.

```bash
poetry install --no-root
```

Placer la configuration spécifique aux tests dans un fichier à la racine du projet (ex. `pytest.ini`).

---

## Exécution de `pre-commit`

L’analyse automatique du code se lance avec :

```bash
poetry run pre-commit run --all-files
```

---

## Exécution de `pytest`

Lancer l’ensemble des tests :

```bash
poetry run pytest
```

Un exemple avec génération de couverture :

```bash
poetry run pytest --cov=sele_saisie_auto --cov-report=term-missing
```

## Configuration de l'environnement de test

Certains tests utilisent des variables d'environnement pour surcharger les
valeurs du fichier `config.ini`. Les principales variables reconnues sont :

- `PSATIME_URL` – URL du portail PSA Time
- `PSATIME_DATE_CIBLE` – date cible par défaut
- `PSATIME_LOGIN` – identifiant chiffré
- `PSATIME_MDP` – mot de passe chiffré
- `PSATIME_DEBUG_MODE` – niveau de log
- `PSATIME_LISTE_ITEMS_PLANNING` – liste d'items de planning

Un fichier `config.ini` doit être présent à la racine du projet. Les tests
créent au besoin une copie temporaire dans un répertoire isolé.

### Exemple d'exécution

```bash
PSATIME_URL=http://localhost \
PSATIME_LOGIN=enc_user \
PSATIME_MDP=enc_pass \
poetry run pytest
```

---

## Commandes de couverture

Les rapports de couverture peuvent être générés au format **HTML**, **JSON** ou directement dans la console.

### Seuils par défaut

Il est recommandé de viser au moins **95 %** de couverture globale. Les seuils peuvent être ajustés dans la configuration de l’outil choisi.

---

## Structure des tests

```text
project-root/
├─ src/
│   ├─ ...
├─ tests/
│   ├─ unit/
│   ├─ integration/
│   └─ e2e/
```

---

## ✅ Exemples de tests

### Hook personnalisé
```typescript
import { renderHook } from '@testing-library/react'
import { useCustomHook } from '@/hooks/useCustomHook'

test('doit retourner la valeur attendue', () => {
  const { result } = renderHook(() => useCustomHook())
  expect(result.current).toBe(true)
})
```

### Composant
```typescript
import { render, screen } from '@testing-library/react'
import MyComponent from '@/components/MyComponent'

test('affiche le titre', () => {
  render(<MyComponent />)
  expect(screen.getByText(/bonjour/i)).toBeInTheDocument()
})
```

### Repository
```python
import pytest
from myapp.repositories import UserRepository


def test_get_user_by_id(mock_session):
    repo = UserRepository(session=mock_session)
    user = repo.get_by_id(1)
    assert user.name == 'Alice'
```

---

## ✅ Bonnes pratiques

* Utiliser des **données de test** claires et réutilisables.
* Isoler les tests pour éviter les effets de bord.
* Favoriser la **lisibilité** : un test = un comportement.
* Exécuter les tests localement avant chaque commit.

---

## ✅ Exclusions du coverage

Certaines ressources peuvent être exclues, par exemple :

* Fichiers générés automatiquement (`**/generated/**`).
* Scripts de migration ou de déploiement.
* Dossier `tests/` lui-même.

---

## ✅ Surveillance continue

Mettre en place un workflow **GitHub Actions** pour lancer les tests et produire la couverture à chaque push ou pull request.

---

## ✅ 🛠️ Troubleshooting / FAQ

* **Les tests ne se lancent pas**
  - Vérifiez la configuration de votre outil (chemins, glob patterns).
* **La couverture reste nulle**
  - Assurez-vous que les tests s’exécutent vraiment et que le répertoire `coverage/` est correctement généré.
* **Problèmes de chemins relatifs**
  - Utilisez des chemins absolus ou configurez un alias (ex. `PYTHONPATH` ou `tsconfig.json`).
