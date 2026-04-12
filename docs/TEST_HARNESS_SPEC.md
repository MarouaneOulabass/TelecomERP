# TEST_HARNESS_SPEC.md

> Spécification du harnais de tests qui sécurise TelecomERP. Ce harnais est le filet sous le funambule : il doit attraper toutes les chutes possibles avant qu'elles n'atteignent un client. Quand le harnais passe, le code peut être mergé. Quand il ne passe pas, le merge est interdit, sans exception.
>
> **Statut** : v1
> **Principe directeur** : "Décrire la cible + harnais fort = on lâche la bête"

---

## 1. Les 5 couches du harnais

Chaque couche attrape un type d'erreur que les autres ne voient pas. Aucune couche ne peut être skipée.

| # | Couche | Type d'erreur attrapée | Outils |
|---|---|---|---|
| 1 | Tests fonctionnels BDD | Le code ne fait pas ce qu'il doit faire | pytest + pytest-bdd |
| 2 | Tests d'architecture | Le code n'est pas construit comme il doit | Lint custom Python |
| 3 | Tests multi-tenant | L'isolation et le cycle de vie cassent | Pytest + Docker |
| 4 | Tests de propriétés | Une combinaison rare casse une invariance | Hypothesis |
| 5 | Tests de migration | Un upgrade casse les données existantes | Pytest custom |

---

## 2. Couche 1 — Tests fonctionnels BDD

### Règle d'or
**Toute capability métier doit avoir au moins un scénario Gherkin par fonctionnalité publique.**

### Structure
```
custom_addons/telecom_<module>/tests/
  features/
    <fonctionnalité>.feature
  test_bdd_<module>.py
```

### Couverture cible
- 70% minimum de lignes par capability
- 100% des scénarios listés dans `CAPABILITY_CATALOG.md` doivent exister

### Exécution
- En CI à chaque commit
- En local avant chaque push (hook git)

### Exemples de scénarios obligatoires (extraits)

**telecom_cost (future)** :
```gherkin
Scénario : Refus d'un coût sans projet
Scénario : Refus d'un coût sans lot
Scénario : Acceptation d'un coût sans tâche, marqué "à rattacher"
Scénario : Modification d'un coût tracée dans l'audit
```

**telecom_margin (future)** :
```gherkin
Scénario : Marge cohérente avec les coûts saisis
Scénario : Alerte déclenchée au seuil configuré
Scénario : Cockpit fonctionne sans telecom_financing (future) activé
```

---

## 3. Couche 2 — Tests d'architecture (lint custom)

### Règle d'or
**Si un principe d'`ARCHITECTURE_PRINCIPLES.md` peut être vérifié automatiquement, il DOIT l'être.**

### Tests à implémenter

| Test | Vérifie | Principe source |
|---|---|---|
| `test_no_french_strings_in_python` | Aucune chaîne en français hors `_()` | §6 |
| `test_no_client_names_in_code` | Pas d'"Inwi", "Orange", "IAM", etc. | §5 |
| `test_no_tenant_id_branching` | Pas de `if tenant_id == "X"` | §5 |
| `test_no_circular_dependencies` | Aucune dépendance circulaire entre capabilities | §3 |
| `test_max_3_dependencies` | Aucune capability avec >3 dépendances dures | §3 |
| `test_all_capabilities_in_catalog` | Tout dossier `telecom_*` figure dans `CAPABILITY_CATALOG.md` | §3 |
| `test_no_field_named_in_french` | Aucun champ Odoo nommé en français | §6 |
| `test_money_fields_have_currency` | Tout champ monétaire a un `currency_id` | §7 |
| `test_no_x_prefix_fields` | Aucun champ commençant par `x_` | §7 |
| `test_no_print_statements` | Aucun `print()` dans le code de production | §15 |
| `test_no_raw_sql_without_env_cr` | Pas de SQL brut hors `self.env.cr` | §15 |
| `test_all_models_have_tests` | Tout modèle a un fichier de test associé | §11 |
| `test_no_disabled_tests` | Aucun `@pytest.skip` sans ticket | §15 |
| `test_cost_creation_only_via_pivot` | Aucun `CostEntry.create()` hors `telecom_cost (future)` | §8 |

| `test_feature_flags_declared` | Tout module avec comportement conditionnel à un flag l'a enregistré dans son `feature_flags.py` | §17 |
| `test_no_undeclared_flag_references` | Aucun code de production ne référence un flag par un `code` non déclaré | §17 |
| `test_feature_flags_both_states_tested` | Tout flag déclaré a au moins un test qui vérifie les deux états (actif/inactif) | §17 |

### Implémentation
Tous ces tests vivent dans `tests/architecture/` et tournent en CI à chaque commit. Un seul échec = build rouge.

---

## 4. Couche 3 — Tests multi-tenant

### Règle d'or
**Aucune ligne de code ne va en production sans avoir été testée sur 3 profils de tenants différents.**

### Profils de référence

| Profil | Description | Capabilities activées |
|---|---|---|
| **minimal** | Petite société, vague MVP uniquement | telecom_project, telecom_cost (future), telecom_margin (future), telecom_intervention, telecom_site, telecom_finance_ma |
| **medium** | Société moyenne, MVP + V1.5 | + telecom_hr_ma, telecom_hr_ma (paie), telecom_fleet, telecom_carburant (future), telecom_facturation (future), telecom_ao |
| **complete** | Grosse société, toutes capabilities | Toutes les 26 |

### Tests à implémenter

| Test | Vérifie |
|---|---|
| `test_provisioning_from_yaml` | Un YAML valide produit un tenant fonctionnel |
| `test_provisioning_idempotent` | Relancer le provisioning ne casse rien |
| `test_invalid_yaml_fails_clean` | YAML invalide → échec lisible, pas de base partielle |
| `test_tenant_isolation_data` | Un tenant ne voit jamais les données d'un autre |
| `test_tenant_isolation_config` | Modifier la config d'un tenant n'affecte pas les autres |
| `test_capability_activation_at_runtime` | Activer une capability en cours de vie ne casse rien |
| `test_capability_uninstall_blocked_with_data` | Désinstallation refusée si données présentes |
| `test_three_profiles_provision_in_parallel` | Les 3 profils peuvent coexister sur la même instance |

### Exécution
- À chaque PR avant merge
- Spinne 3 conteneurs Docker en parallèle, chacun avec son YAML
- Durée cible : <15 minutes pour le tour complet

---

## 5. Couche 4 — Tests de propriétés (Hypothesis)

### Règle d'or
**Les invariants critiques sont testés sur des centaines de profils générés aléatoirement, pas sur des exemples écrits à la main.**

### Stratégie de génération

Une stratégie Hypothesis `tenant_profile_strategy()` génère des profils valides aléatoires en respectant le `TENANT_PROFILE_SCHEMA.json`. Combinaisons d'organisation, de capabilities, de workflows.

### Propriétés à tester

| Propriété | Énoncé |
|---|---|
| `prop_any_valid_profile_provisions` | Pour tout profil valide, le provisioning réussit |
| `prop_capabilities_dependencies_resolved` | Pour toute capability activée, ses dépendances sont installées |
| `prop_org_tree_walkable` | L'arbre d'OrgUnit est toujours navigable, sans cycle |
| `prop_cost_always_attached` | Pour tout coût créé, il est toujours rattaché à un projet+lot |
| `prop_margin_dashboard_never_crashes` | Le cockpit s'affiche pour tout état de données possible |
| `prop_terminology_consistent` | Les termes du tenant_profile sont appliqués partout dans l'UI |
| `prop_workflow_completes_or_fails_clean` | Tout workflow lancé soit se complète, soit échoue proprement, jamais en limbo |

### Exécution
- À chaque PR
- 100 cas générés par propriété minimum
- Les contre-exemples trouvés sont commit comme tests fixes

---

## 6. Couche 5 — Tests de migration

### Règle d'or
**Aucune nouvelle version d'une capability ne sort sans test de migration depuis la version précédente.**

### Tests à implémenter par capability

| Test | Vérifie |
|---|---|
| `test_migration_N_to_N1_preserves_data` | Tous les enregistrements existants sont préservés |
| `test_migration_N_to_N1_idempotent` | Rejouer la migration ne casse rien |
| `test_migration_rollback` | En cas d'échec, on peut revenir à N proprement |

### Exécution
- À chaque release de capability
- Sur snapshot de chaque profil de référence

---

## 7. Pipeline CI complet

```
[Commit local]
   ↓
[Hook pre-commit : ruff + black + lint architecture rapide]
   ↓
[Push]
   ↓
[CI GitHub Actions]
   ├── Étape 1 : Lint complet (couche 2)         → ~2 min
   ├── Étape 2 : Tests unitaires + BDD (couche 1) → ~5 min
   ├── Étape 3 : Tests multi-tenant (couche 3)    → ~15 min
   ├── Étape 4 : Tests de propriétés (couche 4)   → ~10 min
   └── Étape 5 : Tests de migration (couche 5)    → ~5 min
   ↓
[Si tout vert : merge autorisé]
   ↓
[Déploiement preview chez le design partner]
   ↓
[REVUE HUMAINE OBLIGATOIRE — Marouane]
   - Cohérence métier ?
   - UX raisonnable ?
   - Arbitrages d'archi sains ?
   ↓
[Si validé : promotion vers prod]
```

---

## 8. Ce que le harnais ne peut PAS attraper

Honnêteté intellectuelle : trois catégories d'erreurs échappent au harnais et nécessitent une revue humaine systématique.

1. **La cohérence métier du spec lui-même.** Si le spec est faux, le code conforme au spec sera faux aussi. → Mitigation : design partner réel qui valide chaque livrable.

2. **L'UX et l'ergonomie terrain.** Aucun test ne dit si un écran est utilisable par un technicien sur tablette en plein soleil. → Mitigation : tests utilisateurs périodiques sur le terrain.

3. **La dette technique invisible.** Une mauvaise abstraction passe tous les tests mais coince à 6 mois. → Mitigation : revue d'architecture par un second avis (autre instance Claude en mode chat) sur les choix structurants.

**Ces trois mitigations sont aussi importantes que le harnais lui-même. Elles ne sont pas optionnelles.**

---

## 9. Règles de gouvernance du harnais

1. **Aucun test ne peut être désactivé sans ticket associé.**
2. **Un test rouge ne peut jamais être contourné** par un merge forcé.
3. **Toute nouvelle capability ajoute ses tests dans les 5 couches** avant d'être considérée comme livrée.
4. **Le harnais lui-même est versionné et testé.** Les tests sur le lint custom existent.
5. **Le harnais évolue mais ne s'allège jamais.** Une règle ajoutée n'est jamais retirée sans décision tracée.

---

*Fin du document.*
