# ARCHITECTURE_PRINCIPLES.md

> Règles techniques non-négociables de TelecomERP. Ce document est le contrat technique entre les humains, les agents de développement, et le code lui-même. Toute violation d'un principe doit être détectée par le harnais de tests, ou alors le harnais est incomplet.
>
> **Statut** : v1
> **Public cible** : développeurs humains, agents Claude Code, code reviewers

---

## Préambule

Ce document ne décrit pas *comment* écrire le code. Il décrit les **invariants** que le code doit respecter quel que soit qui l'écrit. Chaque principe est formulé comme une règle vérifiable, idéalement automatisable dans le harnais de tests (`TEST_HARNESS_SPEC.md`).

Les principes sont classés par criticité :
- **🔴 NON-NÉGOCIABLE** : violation = build cassé, merge interdit
- **🟡 FORTEMENT RECOMMANDÉ** : violation = warning bloquant en code review humaine
- **🟢 BONNE PRATIQUE** : violation = à justifier dans le commit

---

## 1. Stack technique figée

🔴 **NON-NÉGOCIABLE**

- **Plateforme** : Odoo 17 Community
- **Langage** : Python 3.10
- **Base de données** : PostgreSQL 15
- **Conteneurisation** : Docker Compose v2
- **Tests fonctionnels** : pytest + pytest-bdd + Gherkin
- **Linting** : ruff + black
- **Format de configuration tenant** : YAML validé par JSON Schema

Aucun changement de stack sans décision explicite tracée. Pas d'ajout de dépendance Python sans justification dans le commit.

---

## 2. Structure du repo

🔴 **NON-NÉGOCIABLE**

```
TelecomERP/
├── custom_addons/
│   ├── telecom_base/                # Une capability = un dossier
│   │   ├── __manifest__.py
│   │   ├── models/
│   │   ├── views/
│   │   ├── data/
│   │   ├── security/
│   │   ├── tests/
│   │   └── i18n/
│   ├── telecom_site/
│   └── ... (une par capability du catalogue)
├── control_plane/                  # Hors Odoo : provisioning, agent IA
│   ├── provisioning/
│   ├── onboarding_agent/
│   └── migration_agent/
├── tests/
│   ├── architecture/               # Tests d'architecture (couche 2)
│   ├── multi_tenant/               # Tests d'isolation et cycle de vie
│   └── property_based/             # Tests Hypothesis
├── docs/
│   ├── PRODUCT_VISION.md
│   ├── CAPABILITY_CATALOG.md
│   ├── ARCHITECTURE_PRINCIPLES.md
│   ├── TENANT_PROFILE_SCHEMA.json
│   ├── TEST_HARNESS_SPEC.md
│   └── DEFINITION_OF_DONE.md
├── deploy/
└── docker-compose.yml
```

**Règles** :
- Le nom du dossier = le nom technique de la capability dans le catalogue (préfixe `telecom_`)
- Aucun module sans manifeste valide
- Aucun fichier Python à la racine d'une capability (toujours dans `models/`, `controllers/`, etc.)

---

## 3. Règles de découpage des capabilities

🔴 **NON-NÉGOCIABLE**

1. **Une capability = une décision business indépendante**, pas une décision technique. Si un client ne dirait pas "oui je veux ça" ou "non je n'en veux pas" sans hésiter, c'est qu'elle est mal découpée.
2. **Maximum 3 dépendances dures** par capability. Au-delà, c'est qu'elle est trop intriquée.
3. **Aucune dépendance circulaire**, ni directe ni transitive. Vérifié au build.
4. **Aucune capability ne peut référencer une capability hors catalogue**. Le catalogue est la seule source de vérité des dépendances autorisées.
5. **Toute capability doit pouvoir être installée seule** (avec ses dépendances dures résolues automatiquement) sans erreur.

---

## 4. Règles d'isolation multi-tenant

🔴 **NON-NÉGOCIABLE**

1. **Une base PostgreSQL par tenant.** Pas de table partagée entre tenants.
2. **Aucune donnée d'un tenant n'est jamais visible depuis un autre.** Test d'isolation automatique dans le harnais.
3. **Aucune capability ne peut écrire dans une autre base que celle de son tenant.** Pas de cross-tenant queries, jamais.
4. **Le control plane est le seul composant qui parle à plusieurs tenants à la fois**, et uniquement via l'API XML-RPC/JSON-RPC d'Odoo, jamais en accès SQL direct.
5. **Aucun secret partagé entre tenants** (clés API, tokens, hashs).

---

## 5. Règles sur le code "client-spécifique"

🔴 **NON-NÉGOCIABLE**

1. **Aucune chaîne hardcodée nommant un client réel** dans le code (pas de "Inwi", "Orange", "IAM", "TowerCo", noms d'opérateurs ou de prospects).
2. **Aucune branche conditionnelle basée sur l'identité d'un tenant** (`if tenant_id == "X"`). Tout comportement spécifique passe par le tenant_profile.
3. **Aucun fork de capability pour un client.** Si un besoin émerge, soit on enrichit la capability existante, soit on crée une nouvelle capability optionnelle, soit on refuse.
4. **Aucune migration de données client-spécifique dans le code des modules.** Les migrations vivent dans `control_plane/migration_agent/` et sont des artefacts ponctuels, pas du code produit.

Vérifié par lint custom dans le harnais (recherche de patterns interdits).

---

## 6. Internationalisation et terminologie

🔴 **NON-NÉGOCIABLE**

1. **Toutes les chaînes affichées à l'utilisateur passent par `_()`.** Aucune exception.
2. **Les noms de champs, modèles, classes sont en anglais.** Aucun nom en français ou en darija dans le code.
3. **Aucune chaîne en français hardcodée dans les fichiers Python.** Vérifié par lint.
4. **La terminologie spécifique à un tenant** (chantier vs projet, intervention vs ordre de travail) **est gérée exclusivement via le `TerminologyMapping` du telecom_tenant (futur)**, jamais en dur.

---

## 7. Règles sur les modèles de données

🔴 **NON-NÉGOCIABLE**

1. **Tout modèle hérite ou référence un modèle de `telecom_base`.** Pas de modèle orphelin.
2. **Tout champ devise doit être accompagné d'un champ devise (`currency_id`).** Pas de Float pour de l'argent.
3. **Tout modèle métier a un champ `active` pour le soft-delete.** Pas de DELETE physique sauf cas exceptionnel justifié.
4. **Tout modèle métier a des champs d'audit** (`created_at`, `created_by`, `modified_at`, `modified_by`) hérités de `telecom_base`.
5. **Aucun champ n'a un nom commençant par `x_`** (réservé Odoo Studio).

---

## 8. Règles sur le cost tracking

🔴 **NON-NÉGOCIABLE** (spécifique au cœur de la promesse produit)

1. **Tout `CostEntry` doit obligatoirement référencer un `Project` et un `ProjectLot`.** La saisie échoue sinon.
2. **Le rattachement à une `ProjectTask` est optionnel** mais signalé dans le cockpit comme "à rattacher".
3. **Aucune capability ne peut créer un coût opérationnel sans passer par `telecom_cost (futur)`.** Ni `telecom_carburant (futur)`, ni `telecom_hr_ma`, ni aucune autre. Le pivot est unique.
4. **Une fois saisi, un `CostEntry` ne peut être modifié que par son créateur ou un Responsable**, et toute modification est tracée.

---

## 9. Règles sur les workflows configurables

🟡 **FORTEMENT RECOMMANDÉ**

1. **Les workflows à étapes (validation, signature, approbation) sont déclarés dans le tenant_profile**, pas dans le code des capabilities.
2. **Le moteur d'exécution est `base.automation` d'Odoo**, pas un moteur custom.
3. **Une capability fournit les "points d'extension"** (les événements sur lesquels un workflow peut s'attacher), pas les workflows eux-mêmes.

---

## 10. Règles sur l'installation et la désinstallation

🔴 **NON-NÉGOCIABLE**

1. **Toute capability doit être installable proprement** sur une base Odoo neuve avec uniquement le socle.
2. **L'installation est idempotente** : la rejouer ne casse rien.
3. **La désinstallation est interdite si la capability contient des données métier.** Une fois activée et utilisée, elle reste — elle peut être masquée via les groupes.
4. **Toute capability doit avoir un script de migration vide ou fonctionnel pour passer de la version N à N+1.** Pas de migration "à faire plus tard".

---

## 11. Règles sur les tests

🔴 **NON-NÉGOCIABLE**

1. **Toute capability avec un modèle Odoo doit avoir un dossier `tests/`.**
2. **Couverture minimale par capability : 70% de lignes.** Vérifié en CI.
3. **Toute capability métier doit avoir au moins 1 scénario BDD Gherkin** par fonctionnalité publique.
4. **Le harnais multi-tenant teste chaque capability sur 3 profils différents** (minimal, moyen, complet) avant tout merge sur master.
5. **Les tests d'architecture (lint custom) tournent à chaque commit**, pas seulement à chaque merge.

---

## 12. Règles sur les commits et la collaboration agent/humain

🟡 **FORTEMENT RECOMMANDÉ**

1. **Tout commit fait par un agent autonome doit être signé** dans le message de commit (`Co-authored-by: Claude`).
2. **Aucun agent ne peut modifier les 6 documents fondateurs** (`PRODUCT_VISION.md`, `CAPABILITY_CATALOG.md`, `ARCHITECTURE_PRINCIPLES.md`, `TENANT_PROFILE_SCHEMA.json`, `TEST_HARNESS_SPEC.md`, `DEFINITION_OF_DONE.md`) sans validation humaine explicite.
3. **Une session d'agent autonome ne peut modifier qu'une capability à la fois**, sauf refactoring transverse explicitement briefé.
4. **Toute session d'agent commence par lire les 6 documents fondateurs** avant toute action.

---

## 13. Règles sur la sécurité et les données sensibles

🔴 **NON-NÉGOCIABLE**

1. **Aucun secret en clair dans le repo.** Variables d'environnement uniquement.
2. **Aucune donnée client réelle dans les fixtures de tests.** Toujours des données synthétiques.
3. **Tout export de données par un utilisateur est tracé** dans l'audit.
4. **Les mots de passe utilisateurs respectent la politique Odoo standard renforcée** (12 caractères minimum, complexité).

---

## 14. Règles sur le control plane

🔴 **NON-NÉGOCIABLE**

1. **Le control plane est isolé du code Odoo.** Il vit dans `control_plane/` et communique avec les tenants uniquement via API.
2. **Le provisioning est scriptable et reproductible.** Un même tenant_profile produit toujours la même configuration.
3. **Le control plane a sa propre base de données** (métadonnées tenants, billing, monitoring), distincte de toute base tenant.
4. **L'agent IA d'onboarding ne génère que du YAML conforme au schéma.** Aucune écriture directe dans les bases tenants.
5. **L'agent IA de migration produit des fichiers d'import** validés avant chargement, jamais d'écriture directe non validée.

---

## 15. Anti-patterns explicitement interdits

🔴 **NON-NÉGOCIABLE**

| Anti-pattern | Pourquoi c'est interdit |
|---|---|
| `if tenant == "X"` | Crée un fork client invisible |
| Champ nommé en français | Casse l'i18n |
| `print()` ou `logging.info()` au lieu de `_logger` Odoo | Ingérable en multi-tenant |
| SQL brut sans `self.env.cr` | Casse la sécurité multi-tenant |
| Suppression physique de données métier | Casse l'audit |
| Modification d'un module standard Odoo | Casse les upgrades |
| Hack d'`ir.model.data` pour résoudre un conflit d'install | Bombes à retardement |
| Désactivation d'un test "temporairement" | Devient permanent |
| TODO sans ticket associé | Dette invisible |

---

## 17. Règles sur les feature flags

NON-NEGOTIABLE

1. Tout comportement optionnel ou évolutif d'une capability est contrôlé par un feature flag déclaré dans son fichier `feature_flags.py`.
2. Les feature flags remplacent tout paramètre de configuration modifiable à chaud. Jamais de paramètre en dur ni en code.
3. Chaque flag a une valeur par défaut sûre (généralement `False` pour les nouvelles features non encore éprouvées).
4. L'activation d'un flag ne nécessite jamais un redéploiement ni une modification du `tenant_profile.yaml`.
5. Tout test métier peut forcer un flag via un décorateur de test standardisé `@with_feature_flag('code', active=True/False)`.
6. Tout flag est documenté : à quoi il sert, quel comportement il active, quel est l'impact quand il est inactif.
7. Un flag jamais activé par aucun tenant pendant 12 mois doit être signalé pour décommissionnement (éviter la dette de code mort).

---

## 18. Ce qui n'est pas dans ce document

Pour éviter les confusions :

- Le **format précis du tenant_profile** est dans `TENANT_PROFILE_SCHEMA.json`.
- La **liste exhaustive des tests à mettre en place** est dans `TEST_HARNESS_SPEC.md`.
- Les **critères de "fini" par capability** sont dans `DEFINITION_OF_DONE.md`.
- Les **décisions stratégiques produit** sont dans `PRODUCT_VISION.md`.

---

*Fin du document.*
