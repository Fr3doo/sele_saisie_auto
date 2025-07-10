# 📋 Plan de Refactorisation - sele_saisie_auto

## 🎯 Objectif
Décomposer `PSATimeAutomation` et implémenter les recommandations critiques pour améliorer la maintenabilité et respecter les principes SOLID.

---

## 📊 État actuel vs Objectif

| Critère | Actuel | Objectif |
|---------|--------|----------|
| **SOLID** | 1/10 | 8-9/10 |
| **DRY** | 4/10 | 8/10 |
| **KISS** | 5/10 | 8/10 |
| **Score global** | 3/10 | 8/10 |

---

## 🚀 PHASE 1 - Refactorisation PSATimeAutomation (CRITIQUE)
**Durée estimée : 1-2 semaines**

### Étape 1.1 - Création des nouvelles classes (2-3 jours)

#### Mini-tâche 1.1.1 - AutomationOrchestrator
- [ ] Créer `src/sele_saisie_auto/orchestration/automation_orchestrator.py`
- [ ] Implémenter la méthode `run()` principale
- [ ] Gérer uniquement l'orchestration du flux
- [ ] Tests unitaires pour `AutomationOrchestrator`

#### Mini-tâche 1.1.2 - ResourceManager
- [ ] Créer `src/sele_saisie_auto/resources/resource_manager.py`
- [ ] Implémenter la gestion des ressources (mémoire, navigateur)
- [ ] Context manager pour le nettoyage automatique
- [ ] Tests unitaires pour `ResourceManager`

#### Mini-tâche 1.1.3 - PageNavigator
- [ ] Créer `src/sele_saisie_auto/navigation/page_navigator.py`
- [ ] Déléguer la navigation aux pages existantes
- [ ] Centraliser la logique de navigation
- [ ] Tests unitaires pour `PageNavigator`

#### Mini-tâche 1.1.4 - ServiceConfigurator
- [ ] Créer `src/sele_saisie_auto/configuration/service_configurator.py`
- [ ] Factory methods pour tous les services
- [ ] Configuration centralisée des dépendances
- [ ] Tests unitaires pour `ServiceConfigurator`

### Étape 1.2 - Migration progressive (3-4 jours)

#### Mini-tâche 1.2.1 - Extraction des responsabilités
- [ ] Identifier toutes les méthodes de `PSATimeAutomation`
- [ ] Mapper chaque méthode vers la nouvelle classe appropriée
- [ ] Créer un tableau de correspondance

#### Mini-tâche 1.2.2 - Refactorisation par blocs
- [ ] Migrer la gestion des ressources vers `ResourceManager`
- [ ] Migrer l'orchestration vers `AutomationOrchestrator`
- [ ] Migrer la navigation vers `PageNavigator`
- [ ] Migrer la configuration vers `ServiceConfigurator`

#### Mini-tâche 1.2.3 - Mise à jour des dépendances
- [ ] Modifier `main()` pour utiliser les nouvelles classes
- [ ] Mettre à jour tous les imports
- [ ] Adapter les tests existants

### Étape 1.3 - Validation et tests (1-2 jours)

#### Mini-tâche 1.3.1 - Tests d'intégration
- [ ] Vérifier que le flux complet fonctionne
- [ ] Tests end-to-end avec les nouvelles classes
- [ ] Validation manuelle de l'automatisation

#### Mini-tâche 1.3.2 - Nettoyage
- [ ] Supprimer l'ancienne classe `PSATimeAutomation`
- [ ] Nettoyer les imports inutilisés
- [ ] Mise à jour de la documentation

---

## 🔄 PHASE 2 - Réduction de la duplication (HAUTE)
**Durée estimée : 2-3 semaines**

### Étape 2.1 - AlertHandler centralisé (3-4 jours)

#### Mini-tâche 2.1.1 - Création de la classe
- [ ] Créer `src/sele_saisie_auto/alerts/alert_handler.py`
- [ ] Définir les types d'alertes (save, date, validation)
- [ ] Implémenter la gestion centralisée

#### Mini-tâche 2.1.2 - Migration du code existant
- [ ] Identifier tous les endroits gérant les alertes
- [ ] Remplacer par des appels à `AlertHandler`
- [ ] Tests unitaires pour `AlertHandler`

### Étape 2.2 - ElementIdBuilder (2-3 jours)

#### Mini-tâche 2.2.1 - Factorisation des ID
- [ ] Créer `src/sele_saisie_auto/elements/element_id_builder.py`
- [ ] Implémenter les patterns de construction d'ID
- [ ] Gérer les cas spéciaux (UC_DAILYREST, etc.)

#### Mini-tâche 2.2.2 - Remplacement du code dupliqué
- [ ] Remplacer `_build_input_id` dans `remplir_informations_supp_utils.py`
- [ ] Mettre à jour tous les usages
- [ ] Tests unitaires pour `ElementIdBuilder`

### Étape 2.3 - Décorateurs de gestion d'erreur (2-3 jours)

#### Mini-tâche 2.3.1 - Création des décorateurs
- [ ] Créer `src/sele_saisie_auto/decorators/error_handling.py`
- [ ] Implémenter `@handle_selenium_errors`
- [ ] Gérer les exceptions courantes (NoSuchElement, StaleElement, etc.)

#### Mini-tâche 2.3.2 - Application aux méthodes existantes
- [ ] Identifier les patterns try/catch répétitifs
- [ ] Appliquer les décorateurs
- [ ] Tests unitaires pour les décorateurs

---

## 🧩 PHASE 3 - Simplification de la complexité (MOYENNE)
**Durée estimée : 2-3 semaines**

### Étape 3.1 - Pattern Strategy pour les éléments (4-5 jours)

#### Mini-tâche 3.1.1 - Interface Strategy
- [ ] Créer `src/sele_saisie_auto/strategies/element_filling_strategy.py`
- [ ] Définir l'interface `ElementFillingStrategy`
- [ ] Implémenter `SelectFillingStrategy` et `InputFillingStrategy`

#### Mini-tâche 3.1.2 - Context et Factory
- [ ] Créer `ElementFillingContext`
- [ ] Remplacer les conditions if/else par le pattern Strategy
- [ ] Tests unitaires pour les stratégies

### Étape 3.2 - Décomposition de traiter_description (3-4 jours)

#### Mini-tâche 3.2.1 - Classe DescriptionProcessor
- [ ] Créer `src/sele_saisie_auto/form_processing/description_processor.py`
- [ ] Décomposer en méthodes courtes et focalisées
- [ ] Séparer la logique de collecte et de remplissage

#### Mini-tâche 3.2.2 - Refactorisation avec early returns
- [ ] Éliminer l'imbrication profonde
- [ ] Appliquer le pattern early return
- [ ] Tests unitaires pour `DescriptionProcessor`

### Étape 3.3 - Optimisation des méthodes longues (2-3 jours)

#### Mini-tâche 3.3.1 - Audit des méthodes
- [ ] Identifier toutes les méthodes > 20 lignes
- [ ] Analyser la complexité cyclomatique
- [ ] Prioriser les refactorisations

#### Mini-tâche 3.3.2 - Décomposition ciblée
- [ ] Décomposer les méthodes identifiées
- [ ] Créer des méthodes helper privées
- [ ] Maintenir la lisibilité

---

## ✅ PHASE 4 - Tests et validation (CRITIQUE)
**Durée estimée : 1 semaine**

### Étape 4.1 - Tests unitaires complets (3-4 jours)

#### Mini-tâche 4.1.1 - Couverture des nouvelles classes
- [ ] Tests pour `AutomationOrchestrator`
- [ ] Tests pour `ResourceManager`
- [ ] Tests pour `PageNavigator`
- [ ] Tests pour `ServiceConfigurator`
- [ ] Tests pour `AlertHandler`
- [ ] Tests pour `ElementIdBuilder`
- [ ] Tests pour `DescriptionProcessor`

#### Mini-tâche 4.1.2 - Tests d'intégration
- [ ] Tests end-to-end complets
- [ ] Tests de régression
- [ ] Validation de la couverture (objectif : 95%+)

### Étape 4.2 - Validation fonctionnelle (2-3 jours)

#### Mini-tâche 4.2.1 - Tests manuels
- [ ] Test complet de l'automatisation PSA Time
- [ ] Validation de tous les scénarios utilisateur
- [ ] Vérification des logs et erreurs

#### Mini-tâche 4.2.2 - Performance et stabilité
- [ ] Tests de performance (temps d'exécution)
- [ ] Tests de stabilité (plusieurs exécutions)
- [ ] Validation mémoire (pas de fuites)

---

## 📋 Checklist de validation par phase

### ✅ Phase 1 - Terminée quand :
- [ ] `PSATimeAutomation` n'existe plus
- [ ] 4 nouvelles classes créées et testées
- [ ] Flux principal fonctionne identiquement
- [ ] Tests passent à 100%

### ✅ Phase 2 - Terminée quand :
- [ ] Plus de code dupliqué pour les alertes
- [ ] Plus de `_build_input_id` dupliqué
- [ ] Décorateurs appliqués aux méthodes critiques
- [ ] Tests de régression passent

### ✅ Phase 3 - Terminée quand :
- [ ] Plus de conditions if/else hardcodées pour les types d'éléments
- [ ] `traiter_description` décomposée et lisible
- [ ] Toutes les méthodes < 20 lignes
- [ ] Complexité cyclomatique réduite

### ✅ Phase 4 - Terminée quand :
- [ ] Couverture de tests ≥ 95%
- [ ] Tous les tests d'intégration passent
- [ ] Validation manuelle réussie
- [ ] Performance maintenue ou améliorée

---

## 🎯 Résultats attendus

Après implémentation complète :

| Critère | Avant | Après |
|---------|-------|-------|
| **SOLID** | 1/10 | 8-9/10 |
| **DRY** | 4/10 | 8/10 |
| **KISS** | 5/10 | 8/10 |
| **Score global** | 3/10 | **8/10** 🎉 |

---

## 📝 Notes importantes

1. **Priorité absolue** : Phase 1 (PSATimeAutomation)
2. **Tests obligatoires** : Chaque mini-tâche doit inclure ses tests
3. **Validation continue** : Tester après chaque étape
4. **Documentation** : Mettre à jour `AGENT.md` au fur et à mesure
5. **Commits atomiques** : Un commit par mini-tâche terminée

---

## 🚀 Prêt à commencer ?

**Prochaine action recommandée :**
Commencer par la **Mini-tâche 1.1.1** - Création d'`AutomationOrchestrator`

Voulez-vous que je commence par implémenter cette première mini-tâche ?