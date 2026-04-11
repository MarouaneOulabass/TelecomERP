# SPRINT BRIEF — Verrouillage conformité ARCHITECTURE_PRINCIPLES

> À coller tel quel dans Claude Code en mode autonome. Ne pas modifier sans réfléchir aux conséquences.

---

## Contexte

Tu interviens sur le repo TelecomERP, un produit ERP vertical pour entreprises télécom marocaines basé sur Odoo 17. Le projet est encadré par 6 documents fondateurs dans `docs/` qui définissent la vision, le catalogue de capabilities, les principes d'architecture, le schéma de configuration tenant, le harnais de tests, et la définition de "fini". Tu n'as **aucun droit** de modifier ces documents.

Un audit a révélé un certain nombre de violations de `ARCHITECTURE_PRINCIPLES.md` dans le code existant. Ta mission unique pour ce sprint est de **corriger ces violations**, sans rien ajouter, sans rien refactorer au-delà du strict nécessaire, sans créer de nouvelle capability.

## Lectures obligatoires avant toute action

1. `docs/PRODUCT_VISION.md`
2. `docs/CAPABILITY_CATALOG.md`
3. `docs/ARCHITECTURE_PRINCIPLES.md`
4. `docs/TENANT_PROFILE_SCHEMA.json`
5. `docs/TEST_HARNESS_SPEC.md`
6. `docs/DEFINITION_OF_DONE.md`

Confirme leur lecture en début de session avant la moindre action sur le code.

## Périmètre strict de ce sprint

**Tu es autorisé à modifier uniquement** :
- Les fichiers Python et XML des modules listés ci-dessous
- Les fichiers de migration nécessaires aux renommages de champs
- Les fichiers de tests directement impactés par les renommages

**Tu n'es pas autorisé à** :
- Modifier les 6 documents dans `docs/`
- Créer de nouvelle capability
- Ajouter de nouvelle fonctionnalité métier
- Refactorer du code qui n'est pas dans la liste de violations
- Renommer des champs autres que ceux listés
- Toucher au control plane ou à la configuration Docker
- Modifier `__manifest__.py` au-delà de ce qui est strictement nécessaire pour passer les tests

Si tu identifies une autre violation non listée pendant ton travail, tu la signales dans le rapport final mais tu **ne la corriges pas dans ce sprint**.

## Tâche 1 — Renommage des champs en français

Six champs sont nommés en français, ce qui viole `ARCHITECTURE_PRINCIPLES.md §6` (les noms techniques doivent être en anglais).

| Fichier | Ligne | Champ actuel | Renommer en |
|---|---|---|---|
| `custom_addons/telecom_contract/models/telecom_caution_bancaire.py` | 68 | `montant` | `amount` |
| `custom_addons/telecom_carburant/models/telecom_carburant.py` | 62 | `montant` | `amount` |
| `custom_addons/telecom_site/models/telecom_site.py` | 186 | `adresse` | `address` |
| `custom_addons/telecom_finance_ma/models/telecom_avance.py` | 72 | `montant` | `amount` |
| `custom_addons/telecom_financing/models/telecom_financing.py` | 59 | `montant` | `amount` |
| `custom_addons/telecom_cost/models/telecom_cost_entry.py` | 58 | `montant` | `amount` |

### Pour chaque renommage tu dois :

1. Renommer le champ dans le fichier modèle
2. Mettre à jour **toutes les références** dans :
   - les autres fichiers Python du même module et des modules dépendants
   - les fichiers XML de vues du module et des modules dépendants
   - les fichiers de tests
   - les fichiers `.feature` BDD
   - les fichiers de données si présents
3. Conserver le libellé `string=` en français (le libellé utilisateur reste "Montant" / "Adresse"). Seul le **nom technique du champ** change.
4. Créer un **script de migration** dans le dossier `migrations/` du module concerné qui renomme la colonne en base de données via `ALTER TABLE`. Format Odoo standard.
5. Lancer les tests du module impacté et confirmer qu'ils passent.

### Exemple de script de migration attendu

Pour `telecom_cost`, créer `custom_addons/telecom_cost/migrations/17.0.1.0.1/pre-migration.py` :

```python
def migrate(cr, version):
    cr.execute("""
        ALTER TABLE telecom_cost_entry
        RENAME COLUMN montant TO amount;
    """)
```

Et incrémenter la version dans `__manifest__.py` de `17.0.1.0.0` à `17.0.1.0.1`.

## Tâche 2 — Suppression des références à des opérateurs réels

Trois fichiers contiennent des références hardcodées à des opérateurs marocains réels, ce qui viole `ARCHITECTURE_PRINCIPLES.md §5`.

| Fichier | Ligne | Action |
|---|---|---|
| `custom_addons/telecom_site/models/telecom_site.py` | 143 | Remplacer `"IAM-CASA-001"` dans le help text par un exemple générique : `"OP-VILLE-001"` |
| `custom_addons/telecom_site/tests/test_bdd_site.py` | 49 et 51 | Remplacer `"Maroc Telecom"` par un nom fictif neutre : `"Opérateur Test Alpha"` |
| `custom_addons/telecom_reporting/wizard/export_operateur.py` | 6 | Remplacer le commentaire mentionnant `"Maroc Telecom, Orange, Inwi"` par : `"opérateurs hébergeurs (référencés via res.partner)"` |

Aucune autre action sur ces fichiers.

## Tâche 3 — Audit des 693 strings en français potentiellement non internationalisées

Un grep automatique a trouvé 693 occurrences de chaînes en français dans les fichiers Python. La grande majorité sont **vraisemblablement des `string=` ou `help=` de champs Odoo** qui sont correctement traitées par le système de traduction Odoo via les fichiers `.po`. Ces cas sont conformes et **ne doivent pas être modifiés**.

### Ce que tu dois faire

1. Parcourir les 693 occurrences avec ce grep :
   ```bash
   grep -rEn "['\"][A-ZÉÀÈ][a-zéàèç]" custom_addons --include="*.py"
   ```
2. Classer chaque occurrence dans une de ces catégories :
   - **Catégorie A — Conforme** : `string="..."`, `help="..."`, `placeholder="..."`, `name="..."`, descriptions de Selection, libellés de groupes. Ces strings passent par le système Odoo.
   - **Catégorie B — Violation** : `raise UserError("...")`, `raise ValidationError("...")`, `_logger.info("...")`, retours de fonction, valeurs par défaut affichées à l'utilisateur. Ces strings doivent être enveloppées dans `_()`.
3. **Corriger uniquement les occurrences de catégorie B** en les enveloppant dans `_()` et en s'assurant que `_` est bien importé en haut du fichier (`from odoo import _`).
4. Produire un compteur final : combien de catégorie A (ignorées), combien de catégorie B (corrigées).

**Tu ne dois pas reformuler les chaînes.** Juste les envelopper dans `_()`. Le contenu reste identique.

## Tâche 4 — Audit des 11 SQL bruts

Onze occurrences de `cr.execute()` ou `self.env.cr.execute()` ont été détectées. C'est légitime en Odoo mais doit être justifié.

### Ce que tu dois faire

1. Lister les 11 occurrences avec leur fichier et leur ligne
2. Pour chacune, vérifier :
   - Si elle a déjà un commentaire au-dessus expliquant pourquoi le ORM n'a pas été utilisé → marquer "OK"
   - Si elle n'a pas de commentaire → ajouter un commentaire `# SQL direct : <raison>` (raison à inférer du contexte : performance, opération bulk, accès à une table système, etc.)
3. Si une occurrence est manifestement remplaçable par du ORM standard sans perte de performance, **la signaler dans le rapport** mais ne pas la modifier dans ce sprint.

## Tâche 5 — Vérification des tests après modifications

Après toutes les modifications :

1. Lancer la suite complète de tests Odoo avec :
   ```bash
   docker compose exec odoo odoo -d test_db -i telecom_base,telecom_cost,telecom_carburant,telecom_contract,telecom_site,telecom_finance_ma,telecom_financing --test-enable --stop-after-init
   ```
2. Lancer les tests pytest :
   ```bash
   pytest custom_addons/ -v
   ```
3. Si un test échoue à cause d'un renommage, le mettre à jour pour utiliser le nouveau nom de champ. Si un test échoue pour une autre raison, **arrêter le sprint et signaler le problème** dans le rapport sans tenter de le corriger.

## Livrable final

À la fin du sprint, tu produis un fichier `docs/sprint_verrouillage_rapport.md` contenant :

### Section 1 — Récapitulatif des modifications
- Liste des champs renommés avec confirmation de la migration créée
- Liste des références opérateurs corrigées
- Compteur catégorie A vs catégorie B pour les strings, avec liste des fichiers de catégorie B modifiés
- Liste des SQL bruts annotés ou signalés

### Section 2 — Tests
- Statut de la suite Odoo (modules testés, résultat)
- Statut de pytest (nombre de tests, passés/échoués)

### Section 3 — Anomalies non corrigées
- Toute violation supplémentaire identifiée pendant le travail
- Toute incohérence entre le code et les docs
- Toute occurrence de catégorie B trop ambiguë pour être corrigée mécaniquement

### Section 4 — Recommandations pour les sprints suivants
- Liste des actions à mener qui dépassent le périmètre de ce sprint

## Definition of Done de ce sprint

Le sprint est terminé si et seulement si :

- [ ] Les 6 champs ont été renommés et leurs migrations sont en place
- [ ] Les 3 fichiers contenant des références opérateurs ont été nettoyés
- [ ] Les occurrences de catégorie B ont été enveloppées dans `_()`
- [ ] Les 11 SQL bruts ont été annotés ou signalés
- [ ] La suite de tests passe au vert (ou les échecs sont documentés et signalés)
- [ ] Le rapport `docs/sprint_verrouillage_rapport.md` est rédigé
- [ ] Aucun fichier en dehors du périmètre n'a été modifié
- [ ] Aucune nouvelle fonctionnalité n'a été ajoutée

## Règles de comportement pendant le sprint

1. **Lis les 6 documents fondateurs en début de session.** Aucune action avant ça.
2. **Procède tâche par tâche, dans l'ordre.** Ne saute pas une tâche, ne mélange pas.
3. **Commit après chaque tâche.** Format : `chore(verrouillage): tâche N - <description>`. Co-author : Claude.
4. **Ne dévie pas du périmètre.** Si tu es tenté d'améliorer autre chose, note-le pour le rapport et continue.
5. **En cas d'ambiguïté, arrête-toi et signale.** Ne devine pas.
6. **Ne modifie jamais les 6 documents fondateurs**, même si tu penses avoir une amélioration à proposer. Les améliorations vont dans la section recommandations du rapport.

---

*Fin du brief.*
