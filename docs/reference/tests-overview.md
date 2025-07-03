## 🧪 Aperçu des tests

Les tests unitaires se trouvent dans le dossier `tests/` et sont exécutés avec
`pytest`.

Pour lancer la suite complète :

```bash
poetry run pytest
```

La couverture doit rester au-dessus de 95 %. Les scénarios principaux sont dans
`tests/xxx.py`.

---

## 🛡️ Exclusions de couverture

Certains fichiers ou portions de code sont **exclus des rapports de couverture**, car ils ne contiennent pas de logique testable ou relèvent de comportements techniques spécifiques. Ces exclusions garantissent des rapports **clairs, pertinents et orientés métier**.

### 🗂️ Fichiers et dossiers exclus des tests et de la couverture

| Chemin                             | Justification                                                              |
| ---------------------------------- | -------------------------------------------------------------------------- |
| `tests/` | Les tests ne sont pas comptés dans la couverture |
| `docs/` | Documentation sans logique métier |
| `example_plugin.py` | Module d'exemple non exécuté en production |
| `calendar_icon.png` | Ressource statique hors périmètre de tests |
| `design_notes.md` | Notes techniques non exécutables |
| `*/__init__.py` | Fichiers d'initialisation sans logique à tester |
| `tests/helpers/` | Utilitaires de tests non soumis à la couverture |


Ces éléments sont volontairement ignorés afin de concentrer la couverture sur la logique applicative réellement testable.

### 🌐 Cas spécifiques

Pour l'instant, aucun cas spécifique supplémentaire n'est recensé.

[⬅️ Retour au guide complet des tests](../../TESTING.md)
