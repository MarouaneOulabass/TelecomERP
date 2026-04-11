# Rapport Sprint Verrouillage conformite ARCHITECTURE_PRINCIPLES

> Date : 2026-04-10
> Auteur : Claude Code (agent autonome)
> Perimetre : correction des violations identifiees par l'audit

---

## Section 1 -- Recapitulatif des modifications

### 1.1 Renommage des 6 champs en francais (Tache 1)

Les 6 champs avaient deja ete renommes lors d'une session precedente. Verification effectuee :

| Module | Modele | Ancien champ | Nouveau champ | Migration | Version |
|---|---|---|---|---|---|
| `telecom_cost` | `telecom.cost.entry` | `montant` | `amount` | `migrations/17.0.1.0.1/pre-migration.py` | 17.0.1.0.1 |
| `telecom_carburant` | `telecom.plein.carburant` | `montant` | `amount` | `migrations/17.0.1.0.1/pre-migration.py` | 17.0.1.0.1 |
| `telecom_contract` | `telecom.caution.bancaire` | `montant` | `amount` | `migrations/17.0.1.0.1/pre-migration.py` | 17.0.1.0.1 |
| `telecom_site` | `telecom.site` | `adresse` | `address` | `migrations/17.0.1.0.1/pre-migration.py` | 17.0.1.0.1 |
| `telecom_finance_ma` | `telecom.avance.remboursement` | `montant` | `amount` | `migrations/17.0.1.0.1/pre-migration.py` | 17.0.1.0.1 |
| `telecom_financing` | `telecom.cout.financier` | `montant` / `montant_interets` | `amount` / `interest_amount` | `migrations/17.0.1.0.1/pre-migration.py` | 17.0.1.0.1 |

Toutes les references Python, XML (vues, rapports, donnees), tests et fichiers `.feature` utilisent les noms anglais. La vue SQL de `telecom_margin` reference correctement `ce.amount`.

### 1.2 Suppression des references a des operateurs reels (Tache 2)

Les 3 corrections avaient deja ete appliquees :

| Fichier | Ligne | Avant | Apres | Statut |
|---|---|---|---|---|
| `telecom_site/models/telecom_site.py` | 143 | `"IAM-CASA-001"` | `"OP-VILLE-001"` | Deja corrige |
| `telecom_site/tests/test_bdd_site.py` | 49, 51 | `"Maroc Telecom"` | `"Operateur Test Alpha"` | Deja corrige |
| `telecom_reporting/wizard/export_operateur.py` | 6 | `"Maroc Telecom, Orange, Inwi"` | `"operateurs hebergeurs (references via res.partner)"` | Deja corrige |

### 1.3 Audit des chaines en francais -- Categorie A vs B (Tache 3)

Grep effectue sur l'ensemble de `custom_addons/` avec le pattern `['\"][A-Z...][a-z...]`.

| Categorie | Nombre | Action |
|---|---|---|
| **A -- Conforme** (string=, help=, selection, description, docstrings, __manifest__, tests/assertions) | ~2083 | Aucune modification |
| **B -- Violation** (raise sans `_()`) | 1 | Corrigee |

**Fichier corrige (Categorie B)** :

- `custom_addons/telecom_base/tests/test_bdd_base.py` ligne 64 : `raise ValidationError("L'ICE doit contenir exactement 15 chiffres.")` enveloppe dans `_()`. Import `from odoo import _` ajoute.

### 1.4 Audit des SQL bruts (Tache 4)

18 occurrences de `cr.execute()` identifiees dans 11 fichiers. Toutes annotees avec un commentaire `# SQL direct : <raison>`.

| Fichier | Nb appels | Raison | Commentaire |
|---|---|---|---|
| `telecom_cost/migrations/17.0.1.0.1/pre-migration.py` | 1 | Migration schema | Ajoute dans ce sprint |
| `telecom_carburant/migrations/17.0.1.0.1/pre-migration.py` | 1 | Migration schema | Ajoute dans ce sprint |
| `telecom_contract/migrations/17.0.1.0.1/pre-migration.py` | 1 | Migration schema | Ajoute dans ce sprint |
| `telecom_site/migrations/17.0.1.0.1/pre-migration.py` | 1 | Migration schema | Ajoute dans ce sprint |
| `telecom_finance_ma/migrations/17.0.1.0.1/pre-migration.py` | 1 | Migration schema | Ajoute dans ce sprint |
| `telecom_financing/migrations/17.0.1.0.1/pre-migration.py` | 2 | Migration schema | Ajoute dans ce sprint |
| `telecom_margin/models/telecom_project_margin.py` | 1 | CREATE VIEW (_auto=False) | Deja annote |
| `telecom_reporting/models/report_site_analysis.py` | 1 | CREATE VIEW (_auto=False) | Deja annote |
| `telecom_reporting/models/report_intervention_analysis.py` | 1 | CREATE VIEW (_auto=False) | Deja annote |
| `telecom_reporting/models/report_finance_analysis.py` | 4 | CREATE VIEW + SAVEPOINT | Deja annote |
| `telecom_hr_ma/tests/test_bdd_hr.py` | 4 | Bypass ORM recomputation pour assertions BDD | Deja annote |

**Aucune occurrence n'est trivialement remplacable par du ORM** : les migrations operent hors ORM, les vues SQL (`_auto = False`) sont le pattern Odoo standard pour les modeles de reporting, et les SQL de test contournent volontairement le recompute ORM pour fixer des valeurs de test.

---

## Section 2 -- Tests

Les tests n'ont pas pu etre executes dans cette session (pas d'environnement Docker/Odoo disponible). Les modifications apportees sont strictement cosmetiques (ajout de commentaires `# SQL direct` et wrapping d'une chaine dans `_()`), sans impact sur la logique metier.

**Risques identifies** :
- Ajout de `from odoo import _` dans `test_bdd_base.py` : risque nul (import standard Odoo).
- Wrapping dans `_()` : risque nul (la chaine reste identique, `_()` est une no-op dans le contexte des tests).
- Commentaires sur les migrations : aucun impact fonctionnel.

---

## Section 3 -- Anomalies non corrigees

### Violations supplementaires identifiees (hors perimetre)

1. **Champs nommes en francais dans d'autres modules** : de nombreux champs restent en francais (`montant_total`, `montant_marche`, `montant_avance`, `montant_verse`, `montant_situation_ht`, `loyer_mensuel`, `prix_litre`, `hauteur_pylone`, `puissance_electrique`, `bail_reference`, `bail_date_debut`, `bail_date_fin`, `kilometrage`, `justificatif`, etc.) dans `telecom_contract`, `telecom_finance_ma`, `telecom_ao`, `telecom_site`, `telecom_carburant` et d'autres modules. Ces violations de l'ARCHITECTURE_PRINCIPLES SS 6.2 n'etaient pas dans le perimetre de ce sprint.

2. **Noms de modeles en francais** : `telecom.technologie`, `telecom.cout.financier`, `telecom.plein.carburant`, `telecom.caution.bancaire`, `telecom.avance.demarrage`, `telecom.avance.remboursement`, `telecom.situation`, `telecom.decompte` contiennent des termes francais dans leur nom technique.

3. **Selection values en francais** : `'provisoire'`, `'definitive'`, `'retenue_garantie'`, `'bonne_fin'`, `'pylone_greenfield'`, `'chambre_tirage'`, `'prospection'`, `'deploiement'`, `'desactive'`, etc. sont des valeurs techniques en francais.

4. **Chaines dans les `_sql_constraints`** : certains messages de contrainte SQL sont en francais et non wrappees dans `_()` (c'est une limitation Odoo : les messages `_sql_constraints` ne passent pas par `_()`).

---

## Section 4 -- Recommandations pour les sprints suivants

1. **Sprint de renommage massif des champs francais restants** : inventorier tous les champs techniques en francais (estime a ~50-80 champs) et planifier un sprint dedie avec migrations. Prioriser par module, en commencant par `telecom_finance_ma` (le plus touche).

2. **Renommage des noms de modeles francais** : operation plus lourde (impacte les tables SQL, les references `_name`, les `ir.model.data`, les vues XML). A planifier separement.

3. **Normalisation des valeurs de Selection** : remplacer les valeurs techniques francaises par des equivalents anglais dans toutes les selections.

4. **Mise en place du lint automatise** : ajouter un test d'architecture (couche 2 du harnais) qui detecte automatiquement les noms de champs/modeles en francais et les `raise` sans `_()`.

5. **Execution de la suite de tests** : valider les modifications de ce sprint sur un environnement Docker fonctionnel.

---

*Fin du rapport.*
