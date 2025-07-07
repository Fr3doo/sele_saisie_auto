# Tests avancés

Ce guide explique comment atteindre les branches difficiles des utilitaires en mockant la configuration et en simulant les APIs du DOM.

## Utiliser `pytest` et `pytest-mock`

`pytest` facilite l'organisation des tests et le marquage des cas avancés. Le paquet `pytest-mock` ajoute une fixture `mocker` qui simplifie la création de doubles.

### Exemple avec `mocker.patch`

```python
def test_fetch_data(mocker):
    fake_resp = mocker.Mock()
    fake_resp.json.return_value = {"status": "ok"}
    mocker.patch("requests.get", return_value=fake_resp)

    result = fetch_data("http://example.com")
    assert result["status"] == "ok"
```

## Exemples de monkeypatching

La fixture `monkeypatch` intégrée de `pytest` permet de modifier temporairement des variables ou des fonctions. C'est utile pour ajuster la configuration sans toucher aux fichiers.

### Modifier une variable d'environnement

```python
def test_override_setting(monkeypatch):
    monkeypatch.setenv("APP_MODE", "test")
    assert os.getenv("APP_MODE") == "test"
```

### Patcher un attribut

```python
def test_replace_attribute(monkeypatch):
    class Dummy:
        value = 1

    monkeypatch.setattr(Dummy, "value", 99)
    assert Dummy.value == 99
```

## Simuler les appels externes

Pour tester les interactions avec une API ou le DOM, il est préférable de remplacer les appels réels par des mocks. `pytest-mock` fournit `mocker.spy` ou `mocker.patch`.

### Surveiller l'appel d'une méthode

```python
def test_check_call(mocker):
    spy = mocker.spy(service, "process")
    run_service()
    assert spy.called
```

## Mesurer la couverture

`pytest-cov` produit un rapport de couverture détaillé.

```bash
poetry run pytest --cov=sele_saisie_auto --cov-report=term-missing
```

Atteindre les branches difficiles demande de forcer les chemins rares : options invalides, exceptions volontairement déclenchées et scénarios de timeout. Les assertions de couverture indiquent quelles lignes restent à tester.

## Centraliser la construction des ID

Les pages PSA Time utilisent des identifiants de champs dont le patron varie en fonction du contexte. Pour éviter la duplication de chaînes dans les tests, le module `ElementIdBuilder` expose la méthode
`build_day_input_id(base_id, day_index, row_index)`.

```python
from sele_saisie_auto.elements import ElementIdBuilder

input_id = ElementIdBuilder.build_day_input_id("POL_TIME", 3, 0)
```

Cette fonction applique automatiquement les règles particulières comme l’offset
des entrées "UC_TIME_LIN_WRK_UC_DAILYREST". Centraliser la construction des ID permet de maintenir un code de test plus lisible et plus robuste.
