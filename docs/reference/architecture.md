# Architecture

Le projet suit une architecture simple en plusieurs modules :



Les tests unitaires résident dans le dossier `tests/` et sont exécutés avec
`pytest`.

## Vue d’ensemble des composants

```mermaid
graph TD
    subgraph UI
        A[Utilisateur] --> B(SeleniumFiller)
    end
    B --> C(TimeSheetHelper)
    B --> D(ExtraInfoHelper)
    B --> E(ConfigManager)
    B --> F(EncryptionService)
    C --> G(SeleniumUtils)
    D --> G
    E --> H(Logger)
    F --> H
```




