# 🧪 Guide de tests et couverture

---

## ✅ Configuration des tests

Ce projet utilise principalement **pytest** pour les tests unitaires. Pour d’autres environnements, il est possible d’adapter la configuration à des outils comme **Vitest** ou **Jest**.

1. Installer les dépendances nécessaires :
   ```bash
   poetry install --no-root
   # ou pour un projet JS/TS
   npm install
   ```
2. Placer la configuration spécifique à l’outil de test dans un fichier à la racine (ex. `pytest.ini`, `vitest.config.ts`).

---

## ✅ Outils de test

* [PyTest](https://docs.pytest.org/) pour la logique Python.
* [Testing Library](https://testing-library.com/docs/) pour les composants front-end (React, Vue, etc.).
* [MSW](https://mswjs.io/) pour simuler les appels réseau.
* [Vitest](https://vitest.dev/) ou [Jest](https://jestjs.io/) pour les projets TypeScript/JavaScript.

---

## ✅ Scripts disponibles

* `npm run test` — lance l’ensemble des tests.
* `npm run test:watch` — exécution en mode surveillance continue.
* `npm run coverage` — génère les rapports de couverture.
* `npm run lint` — analyse statique du code (flake8, ESLint...).

---

## ✅ Rapports de couverture

Les rapports de couverture peuvent être générés au format **HTML**, **JSON** ou directement dans la console.

### Seuils par défaut

Il est recommandé de viser au moins **80 %** de couverture globale. Les seuils peuvent être ajustés dans la configuration de l’outil choisi.

---

## ✅ Structure des tests

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
