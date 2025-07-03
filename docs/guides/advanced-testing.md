# Tests avancés

Ce guide explique comment atteindre les branches difficiles des utilitaires en mockant la configuration et en simulant les APIs du DOM.

## Utiliser `pytest` et `pytest-mock`

`pytest` facilite l'organisation des tests et le marquage des cas avancés. Le paquet `pytest-mock` ajoute une fixture `mocker` qui simplifie la création de doubles.

```python

```

## Exemples de monkeypatching

La fixture `monkeypatch` intégrée de `pytest` permet de modifier temporairement des variables ou des fonctions. C'est utile pour ajuster la configuration sans toucher aux fichiers.

```python

```

## Simuler les appels externes

Pour tester les interactions avec une API ou le DOM, il est préférable de remplacer les appels réels par des mocks. `pytest-mock` fournit `mocker.spy` ou `mocker.patch`.

```python

```

## Mesurer la couverture

`pytest-cov` produit un rapport de couverture détaillé.

```bash
poetry run pytest --cov=sele_saisie_auto --cov-report=term-missing
```

Atteindre les branches difficiles demande de forcer les chemins rares : options invalides, exceptions volontairement déclenchées et scénarios de timeout. Les assertions de couverture indiquent quelles lignes restent à tester.
