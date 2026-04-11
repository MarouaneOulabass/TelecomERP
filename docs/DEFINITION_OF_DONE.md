# DEFINITION_OF_DONE.md

> Une capability est "livrée" quand elle satisfait *toutes* les conditions de ce document. Pas 99%. Toutes. Sans exception. Ce document est la checklist finale qu'un agent autonome doit valider avant de déclarer une capability terminée, et que Marouane doit valider avant de la promouvoir en production.
>
> **Statut** : v1
> **Principe** : "Done" est binaire. Une capability est faite ou elle ne l'est pas. Il n'y a pas de "done à 80%".

---

## 1. Pourquoi ce document existe

Sans définition explicite et vérifiable de "fini", chaque session de développement va déclarer "c'est bon" sur des critères différents. Au bout de 10 capabilities, le produit est un patchwork hétérogène où certaines fonctionnalités sont solides et d'autres sont des coquilles vides. **La Definition of Done est ce qui transforme un projet d'agent autonome en produit professionnel.**

---

## 2. Checklist de Definition of Done par capability

Une capability est livrée si et seulement si **toutes** les cases ci-dessous sont cochées.

### Niveau 1 — Code et structure

- [ ] Le dossier `custom_addons/telecom_<nom>/` existe et respecte la structure standard
- [ ] Le `__manifest__.py` est valide, complet (author, license, version sémantique, dépendances déclarées)
- [ ] La capability figure dans `CAPABILITY_CATALOG.md` avec le même nom technique
- [ ] Les dépendances dures du manifeste correspondent exactement à celles du catalogue
- [ ] Aucune dépendance circulaire (vérifié par le test d'architecture)
- [ ] La capability respecte les 16 sections d'`ARCHITECTURE_PRINCIPLES.md`

### Niveau 2 — Modèles de données

- [ ] Tous les modèles héritent ou référencent un modèle de `telecom_base`
- [ ] Tous les noms de champs sont en anglais
- [ ] Tous les champs monétaires ont un `currency_id` associé
- [ ] Tous les modèles métier ont un champ `active` pour le soft-delete
- [ ] Tous les modèles métier ont les champs d'audit hérités
- [ ] Aucun champ avec préfixe `x_`
- [ ] Le schéma de données est documenté dans le code (docstrings de classes)

### Niveau 3 — Sécurité

- [ ] Le fichier `security/ir.model.access.csv` couvre tous les modèles
- [ ] Les règles d'accès référencent les groupes définis dans `telecom_base (security)`
- [ ] Aucune donnée sensible accessible sans authentification
- [ ] Les champs sensibles sont marqués `groups=` quand nécessaire
- [ ] Test d'isolation multi-tenant passé sur cette capability

### Niveau 4 — Internationalisation

- [ ] Toutes les chaînes affichées passent par `_()`
- [ ] Le fichier `i18n/fr.po` est généré et complet
- [ ] Aucune chaîne en français hardcodée (vérifié par lint)
- [ ] Les libellés respectent la terminologie configurable via `telecom_tenant (future)`

### Niveau 5 — Tests fonctionnels (couche 1 du harnais)

- [ ] Au moins un fichier `.feature` Gherkin par fonctionnalité publique
- [ ] Tous les scénarios listés dans `CAPABILITY_CATALOG.md` pour cette capability sont implémentés
- [ ] Couverture de lignes ≥ 70%
- [ ] Tous les scénarios passent en CI
- [ ] Tests unitaires des modèles présents dans `tests/`

### Niveau 6 — Tests d'architecture (couche 2)

- [ ] Aucune violation de lint custom
- [ ] Aucune violation des anti-patterns interdits (§15 architecture)
- [ ] Aucun `print()`, aucun SQL brut hors `self.env.cr`
- [ ] Aucun nom de client réel hardcodé

### Niveau 7 — Tests multi-tenant (couche 3)

- [ ] La capability s'installe proprement sur les 3 profils de référence (minimal, medium, complete)
- [ ] L'installation est idempotente sur les 3 profils
- [ ] Aucune fuite de données entre tenants détectée
- [ ] La désinstallation est correctement bloquée si données présentes

### Niveau 8 — Tests de propriétés (couche 4)

- [ ] Si la capability touche au cost tracking, à l'organisation, ou aux workflows : au moins une propriété Hypothesis dédiée
- [ ] Les propriétés tournent avec 100 cas minimum
- [ ] Aucun contre-exemple non résolu

### Niveau 9 — Tests de migration (couche 5)

- [ ] Si la capability est une mise à jour d'une version précédente : test de migration N→N+1 présent et vert
- [ ] Si c'est une première version : un script de migration vide existe (préparation du futur)

### Niveau 10 — Documentation

- [ ] Un fichier `README.md` à la racine de la capability décrit : son rôle, ses dépendances, ses points d'extension, ses workflows configurables
- [ ] Les modèles complexes ont des docstrings
- [ ] Les choix d'architecture non-évidents sont commentés (pourquoi, pas quoi)
- [ ] Si la capability ajoute des paramètres au tenant_profile, ils sont documentés dans `TENANT_PROFILE_SCHEMA.json`

### Niveau 11 — Intégration tenant_profile

- [ ] Si la capability a des options configurables : elles sont déclarées dans le schéma JSON et lues depuis `telecom_tenant (future)`
- [ ] Si la capability utilise des termes métier : ils passent par `TerminologyMapping`
- [ ] Si la capability a un workflow : il est déclaré dans la section `workflows` du profil

### Niveau 12 — Validation humaine finale

- [ ] **Marouane a relu le code de la capability**
- [ ] **Marouane a testé manuellement le scénario nominal sur une instance preview**
- [ ] **Le design partner (associé ou client réel) a validé l'UX et la pertinence métier**
- [ ] **Aucun TODO sans ticket dans le code**
- [ ] **Le commit final est signé** avec mention de l'agent et de l'humain validateur

---

## 3. Conditions de "non-done"

Une capability est **explicitement non-livrée** si l'une de ces conditions est vraie, peu importe l'avancement :

| Condition | Pourquoi |
|---|---|
| Un test rouge, même un seul | Le harnais a parlé |
| Un TODO sans ticket dans le code | Dette invisible inacceptable |
| Une exception silencieusement avalée | Bombe à retardement |
| Une chaîne en français hardcodée | Casse la promesse i18n |
| Un test désactivé "temporairement" | Le temporaire devient permanent |
| Une dépendance non déclarée dans le manifeste | Casse les installations |
| Une référence à un client réel dans le code | Casse la philosophie produit |
| Un comportement validé seulement en local, pas en CI | "Ça marche chez moi" est interdit |

---

## 4. Processus de validation par capability

```
[Agent autonome déclare la capability "prête à valider"]
   ↓
[Le harnais CI tourne automatiquement]
   ├── Couches 1 à 5 toutes vertes ?
   │   └── NON → retour à l'agent avec le rapport d'échec
   │   └── OUI → continue
   ↓
[Génération automatique du rapport DoD]
   - Liste de toutes les cases cochées/non cochées
   - Métriques de couverture
   - Diff par rapport à la version précédente
   ↓
[Marouane reçoit la notification "à valider"]
   ↓
[Revue manuelle Marouane — temps cible : 20-30 min]
   - Lecture du diff
   - Test manuel du scénario nominal sur preview
   - Validation niveau 12 de la checklist
   ↓
   ├── Refus → retour à l'agent avec commentaires
   └── Validation → soumission au design partner
   ↓
[Validation design partner — temps cible : 1-3 jours]
   - Test sur cas réel du métier
   - Feedback UX et pertinence
   ↓
   ├── Refus → retour à l'agent avec apprentissages
   └── Validation → promotion en production
   ↓
[Capability marquée DONE dans le catalogue]
```

---

## 5. Definition of Done au niveau d'une vague

Une **vague** (MVP, V1.5, V2) est livrée si et seulement si :

- Toutes les capabilities de la vague sont individuellement DONE
- Le tour complet du harnais multi-tenant passe avec un profil utilisant TOUTES les capabilities de la vague
- Au moins un client réel utilise la vague en production depuis 2 semaines sans bug bloquant
- La documentation utilisateur de la vague est rédigée
- Le pricing correspondant à la vague est défini et activable

---

## 6. Ce qui n'est PAS dans la Definition of Done

Pour éviter la confusion :

- **La perfection** : DoD est un seuil de qualité minimal acceptable, pas un idéal. Une fois DoD atteint, on livre et on itère.
- **L'optimisation** : la performance peut être améliorée plus tard si elle est acceptable. DoD ne demande pas le code le plus rapide.
- **L'exhaustivité fonctionnelle** : une capability peut être DONE sans couvrir tous les cas exotiques. Elle couvre ce qui est dans le catalogue, point.
- **La beauté du code** : DoD demande du code lisible et conforme aux principes, pas du code élégant au sens esthétique.

---

## 7. Règle de discipline ultime

> **"Done" est sacré. Une capability déclarée DONE ne peut plus être modifiée à la légère. Si elle doit l'être, c'est une nouvelle version, avec ses propres tests, sa propre validation, sa propre migration. Cette discipline est ce qui sépare un produit professionnel d'un projet personnel.**

---

*Fin du document.*

---

## Annexe — Synthèse des 6 documents fondateurs

| # | Document | Rôle |
|---|---|---|
| 1 | `PRODUCT_VISION.md` | Le pourquoi et le pour qui |
| 2 | `CAPABILITY_CATALOG.md` | Le quoi : 26 capabilities en 3 vagues |
| 3 | `ARCHITECTURE_PRINCIPLES.md` | Les invariants techniques non-négociables |
| 4 | `TENANT_PROFILE_SCHEMA.json` | Le contrat de configuration par tenant |
| 5 | `TEST_HARNESS_SPEC.md` | Le filet de sécurité en 5 couches |
| 6 | `DEFINITION_OF_DONE.md` | Le seuil binaire de "fini" |

**Ces 6 documents forment le contrat entre Marouane, Claude Code, et le produit. Ils sont versionnés, immuables sans validation explicite, et relus au début de chaque session de développement.**
