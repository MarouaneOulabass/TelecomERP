# CAPABILITY_CATALOG.md

> Catalogue exhaustif et figé des capabilities du produit TelecomERP. Ce document est le contrat technique entre la vision produit et l'implémentation. Toute capability codée doit y figurer ; toute capability listée ici doit être codée selon ses critères.
>
> **Statut** : v1 — figé après validation par l'associé métier.
> **Version produit cible** : V2 (toutes vagues incluses)

---

## Préambule : règles de lecture

**Familles** : les capabilities sont organisées en 5 familles thématiques. Une famille n'est pas un module — c'est une vue d'organisation pour la lecture humaine.

**Vagues de livraison** :
- **MVP** (10 capabilities) — objectif : signer et déployer le design partner
- **V1.5** (8 capabilities) — objectif : ouvrir le SaaS au-delà du design partner
- **V2** (8 capabilities) — objectif : différenciation et upsell

**Statut "Socle"** : la capability est obligatoire et installée automatiquement chez tous les tenants. Non désactivable.

**Statut "Optionnelle"** : la capability est activable/désactivable via le tenant_profile. Une fois activée et avec des données, elle ne peut plus être désinstallée (seulement masquée des groupes d'accès).

**Dépendances dures** : la capability ne peut pas fonctionner sans celles listées. Elles seront installées automatiquement.

**Dépendances souples** : la capability fonctionne sans, mais s'enrichit si elles sont présentes.

**Granularité de cost tracking retenue** : Projet + Lot + Tâche, avec saisie obligatoire au niveau Projet+Lot et optionnelle au niveau Tâche. Le cockpit affiche au niveau le plus fin disponible et signale les coûts non attribués à une tâche.

---

## Vue synthétique du catalogue

| # | Code | Nom | Famille | Vague | Statut |
|---|---|---|---|---|---|
| 1 | telecom_base | Core technique | 1 | MVP | Socle |
| 2 | telecom_tenant (future) | Profil tenant | 1 | MVP | Socle |
| 3 | telecom_localization_ma | Localisation Maroc | 1 | MVP | Socle |
| 4 | telecom_base (security) | Sécurité et accès | 1 | MVP | Socle |
| 5 | telecom_project | Projets et lots | 2 | MVP | Optionnelle |
| 6 | telecom_cost (future) | Rattachement des coûts | 2 | MVP | Optionnelle |
| 7 | telecom_margin (future) | Cockpit de rentabilité | 2 | MVP | Optionnelle |
| 8 | telecom_finance_ma | Situations de travaux et CCAG | 2 | MVP | Optionnelle |
| 9 | telecom_site | Sites physiques | 3 | MVP | Optionnelle |
| 10 | telecom_intervention | Bons d'intervention | 3 | MVP | Optionnelle |
| 11 | telecom_hr_ma | Personnel et affectations | 4 | V1.5 | Optionnelle |
| 12 | telecom_hr_ma (paie) | Paie marocaine CNSS/AMO/IR | 4 | V1.5 | Optionnelle |
| 13 | telecom_fleet | Parc véhicules | 4 | V1.5 | Optionnelle |
| 14 | telecom_carburant (future) | Suivi consommation carburant | 4 | V1.5 | Optionnelle |
| 15 | telecom_financing (future) | Coût réel de financement | 2 | V1.5 | Optionnelle |
| 16 | telecom_facturation (future) | Facturation et relances | 5 | V1.5 | Optionnelle |
| 17 | telecom_ao | Appels d'offres et BPU | 5 | V1.5 | Optionnelle |
| 18 | telecom_contract | Contrats opérateurs et SLA | 5 | V1.5 | Optionnelle |
| 19 | telecom_hr_ma (pointage) | Pointage géolocalisé | 3 | V2 | Optionnelle |
| 20 | telecom_intervention (photos) | Preuves photo terrain | 3 | V2 | Optionnelle |
| 21 | telecom_equipment | Équipements installés | 3 | V2 | Optionnelle |
| 22 | Odoo stock (native) | Stocks de matériel | 4 | V2 | Optionnelle |
| 23 | telecom_hr_ma (habilitations) | EPI et habilitations | 4 | V2 | Optionnelle |
| 24 | telecom_contract (cautions) | Cautions bancaires | 5 | V2 | Optionnelle |
| 25 | telecom_localization_ma (CGNC) | Comptabilité générale MA | 5 | V2 | Optionnelle |
| 26 | telecom_reporting | Reporting et bilan social | 5 | V2 | Optionnelle |

---

## FAMILLE 1 — SOCLE TECHNIQUE

### 1. telecom_base — Core technique

**Vague** : MVP — **Statut** : Socle obligatoire

**Rôle** : fournit les modèles de base abstraits qui structurent toutes les autres capabilities. Aucune sémantique métier n'est codée ici.

**Modèle de données** :
- `OrgUnit` : nœud d'arbre organisationnel typé (BU, département, service, agence). Permet à chaque tenant de modéliser sa structure réelle.
- `Person` : individu, lié à un OrgUnit, avec un ou plusieurs rôles.
- `Role` : rôle fonctionnel attribuable à une Person.
- `Document` : abstraction documentaire (attachable à n'importe quelle entité).
- `Audit` : journal de traçabilité pour toute opération sensible.

**Dépendances dures** : aucune

**Critères d'acceptation** :
- Permet de modéliser une organisation plate, en départements, en BU, ou hybride
- Tous les modèles métier des autres capabilities héritent ou référencent ces objets
- Aucune chaîne en français ou en darija dans le code (i18n via _())

---

### 2. telecom_tenant (future) — Profil tenant

**Vague** : MVP — **Statut** : Socle obligatoire

**Rôle** : lit le fichier YAML de configuration du tenant et applique automatiquement la configuration : capabilities activées, structure organisationnelle, terminologie, workflows, branding.

**Modèle de données** :
- `TenantProfile` : enregistrement unique par tenant, contient le YAML source et les valeurs dérivées.
- `TerminologyMapping` : table de correspondance entre termes génériques et termes du tenant.
- `WorkflowConfig` : étapes et signataires des workflows configurables.

**Dépendances dures** : telecom_base

**Critères d'acceptation** :
- Au provisioning, lit un YAML conforme au schéma TENANT_PROFILE_SCHEMA.json
- Installe automatiquement les capabilities listées dans la section capabilities.enabled
- Crée la structure OrgUnit selon la section organization
- Échec proprement et lisible si le YAML est invalide
- Idempotent : relancer ne casse rien

**Scénarios BDD** :
```
Scénario : Provisioning d'un tenant avec profil minimal
  Étant donné un fichier tenant_profile.yaml valide minimal
  Quand le provisioning est lancé
  Alors les capabilities du socle sont installées
  Et l'organisation par défaut est créée
  Et le tenant est marqué comme "actif"

Scénario : Provisioning avec YAML invalide
  Étant donné un fichier tenant_profile.yaml avec une capability inexistante
  Quand le provisioning est lancé
  Alors le provisioning échoue avec un message clair
  Et aucune base n'est créée
```

---

### 3. telecom_localization_ma — Localisation Maroc

**Vague** : MVP — **Statut** : Socle obligatoire

**Rôle** : règles fiscales, formats légaux et données de référence marocaines. Maintenu par l'équipe produit, pas par les clients.

**Contenu** :
- Plan comptable CGNC marocain
- Taux de TVA et règles d'application
- Retenue à la source (RAS) sur prestations
- Mentions légales obligatoires sur factures (LCN, ICE, RC, IF, Patente, CNSS)
- Régions et villes du Maroc
- Devises et formats numériques

**Dépendances dures** : telecom_base

**Critères d'acceptation** :
- Les autres capabilities n'ont jamais besoin de hardcoder un taux ou une mention
- Mise à jour des taux possible sans redéploiement code

---

### 4. telecom_base (security) — Sécurité et accès

**Vague** : MVP — **Statut** : Socle obligatoire

**Rôle** : modèle de groupes, rôles et règles d'accès commun à toutes les capabilities.

**Groupes par défaut** : Technicien Terrain, Chef de Chantier, Chargé d'Affaires, Responsable, Administrateur.

**Dépendances dures** : telecom_base

**Critères d'acceptation** :
- Aucune donnée d'un tenant n'est jamais accessible depuis un autre tenant
- Test d'isolation multi-tenant automatisé dans le harnais

---

## FAMILLE 2 — PILOTAGE PROJET ET RENTABILITÉ

### 5. telecom_project — Projets et lots

**Vague** : MVP — **Statut** : Optionnelle (mais quasi-toujours activée)

**Rôle** : entité Projet avec découpage en lots et tâches, planning, statuts. C'est l'objet pivot autour duquel toute la rentabilité est calculée.

**Modèle de données** :
- `Project` : nom, client, dates, budget prévisionnel, statut, OrgUnit responsable
- `ProjectLot` : sous-ensemble d'un projet (génie civil, fibre, raccordement, mise en service…)
- `ProjectTask` : tâche optionnelle sous un lot
- `ProjectMember` : affectation d'une Person à un projet/lot

**Dépendances dures** : telecom_base

**Scénarios BDD clés** :
- Créer un projet avec 3 lots et budget prévisionnel
- Affecter des personnes à un lot
- Clôturer un lot et vérifier que les coûts sont figés

---

### 6. telecom_cost (future) — Rattachement des coûts

**Vague** : MVP — **Statut** : Optionnelle (cœur de la promesse cockpit)

**Rôle** : pivot du produit. Toute saisie de coût (carburant, main-d'œuvre, sous-traitance, matériel, frais généraux) doit obligatoirement être rattachée à un Projet et un Lot. La tâche est optionnelle.

**Modèle de données** :
- `CostEntry` : montant, devise, date, type de coût, projet, lot, tâche (optionnelle), source (manuelle, importée, calculée), justificatif
- `CostType` : taxonomie configurable des types de coûts

**Dépendances dures** : telecom_project

**Règle métier non-négociable** : aucun CostEntry ne peut exister sans projet+lot. La saisie est refusée sinon. Les coûts sans tâche sont signalés dans le cockpit comme "à rattacher" mais comptabilisés.

**Scénarios BDD clés** :
- Saisie d'un coût valide → enregistré
- Saisie sans projet → refusée avec message
- Saisie sans tâche → acceptée mais marquée "à rattacher"
- Recherche des coûts non rattachés à une tâche pour un projet donné

---

### 7. telecom_margin (future) — Cockpit de rentabilité

**Vague** : MVP — **Statut** : Optionnelle (la promesse principale)

**Rôle** : tableau de bord temps réel qui affiche, pour chaque projet et chaque lot, la marge prévisionnelle, la marge réelle à date, l'écart, la projection de fin de projet.

**Modèle de données** :
- `MarginSnapshot` : photographie périodique de la marge d'un projet
- `MarginAlert` : seuils d'alerte configurables

**Dépendances dures** : telecom_project, telecom_cost (future)

**Dépendances souples** : telecom_financing (future) (enrichit la marge avec les coûts financiers), telecom_facturation (future) (enrichit avec les revenus réels)

**Affichage clé** :
- Vue projet : budget vs engagé vs payé, marge en %, projection
- Vue lot : même chose au niveau lot
- Vue portefeuille : tous les projets actifs avec code couleur de santé

**Scénarios BDD clés** :
- Un projet avec coûts saisis affiche une marge cohérente
- Un projet sans coût affiche la marge prévisionnelle uniquement
- Une alerte se déclenche quand la marge descend sous le seuil

---

### 8. telecom_finance_ma — Situations de travaux et CCAG

**Vague** : MVP — **Statut** : Optionnelle

**Rôle** : génération des situations de travaux mensuelles et décomptes CCAG conformes au cadre marocain. C'est ce qui permet de facturer les opérateurs.

**Dépendances dures** : telecom_project

**Critères d'acceptation** : génère un PDF conforme aux exigences CCAG, avec avancement par lot, retenues, pénalités, avances.

---

### 15. telecom_financing (future) — Coût réel de financement

**Vague** : V1.5 — **Statut** : Optionnelle

**Rôle** : intègre dans la marge projet les frais financiers réels (intérêts crédit, leasing, immobilisation par cautions, avances client). Rend visible l'impact du mode de financement sur la rentabilité.

**Dépendances dures** : telecom_project, telecom_cost (future)

---

## FAMILLE 3 — OPÉRATIONNEL TERRAIN

### 9. telecom_site — Sites physiques

**Vague** : MVP — **Statut** : Optionnelle

**Rôle** : référentiel des sites où les interventions ont lieu (tours, points de mutualisation, locaux techniques). Coordonnées GPS, bailleur, technologies déployées.

**Dépendances dures** : telecom_base

---

### 10. telecom_intervention — Bons d'intervention

**Vague** : MVP — **Statut** : Optionnelle

**Rôle** : création, validation et signature des bons d'intervention terrain. Workflow configurable selon le tenant_profile (1 à 3 niveaux de validation).

**Dépendances dures** : telecom_base

**Dépendances souples** : telecom_site (rattachement à un site), telecom_project (rattachement à un projet pour le cost tracking)

---

### 19. telecom_hr_ma (pointage) — Pointage géolocalisé

**Vague** : V2 — **Statut** : Optionnelle

**Rôle** : pointage entrée/sortie sur site avec contrôle de présence dans un rayon configurable. Tue la fraude au pointage.

**Dépendances dures** : telecom_site, telecom_hr_ma

---

### 20. telecom_intervention (photos) — Preuves photo terrain

**Vague** : V2 — **Statut** : Optionnelle

**Rôle** : photos horodatées et géolocalisées attachables aux interventions, comme preuve pour facturation aux opérateurs.

**Dépendances dures** : telecom_intervention

---

### 21. telecom_equipment — Équipements installés

**Vague** : V2 — **Statut** : Optionnelle

**Rôle** : inventaire des équipements installés sur chaque site, historique, garanties.

**Dépendances dures** : telecom_site

---

## FAMILLE 4 — RESSOURCES ET LOGISTIQUE

### 11. telecom_hr_ma — Personnel et affectations

**Vague** : V1.5 — **Statut** : Optionnelle

**Rôle** : référentiel du personnel, contrats, affectations aux projets. Base pour toutes les autres capabilities RH.

**Dépendances dures** : telecom_base

---

### 12. telecom_hr_ma (paie) — Paie marocaine

**Vague** : V1.5 — **Statut** : Optionnelle

**Rôle** : calcul de paie conforme à la législation marocaine : CNSS, AMO, IR, primes. Génération des bulletins.

**Dépendances dures** : telecom_hr_ma, telecom_localization_ma

---

### 13. telecom_fleet — Parc véhicules

**Vague** : V1.5 — **Statut** : Optionnelle

**Rôle** : référentiel véhicules, affectations aux projets et aux personnes.

**Dépendances dures** : telecom_base

---

### 14. telecom_carburant (future) — Suivi consommation carburant

**Vague** : V1.5 — **Statut** : Optionnelle

**Rôle** : saisie des pleins et consommations, rattachement automatique au projet via le véhicule et la personne. Détection des surconsommations.

**Dépendances dures** : telecom_fleet, telecom_cost (future)

---

### 22. Odoo stock (native) — Stocks de matériel

**Vague** : V2 — **Statut** : Optionnelle

**Rôle** : gestion des stocks de matériel et fournitures, mouvements, valorisation.

**Dépendances dures** : telecom_base

---

### 23. telecom_hr_ma (habilitations) — EPI et habilitations

**Vague** : V2 — **Statut** : Optionnelle

**Rôle** : suivi des EPI distribués, des visites médicales, des habilitations électriques/hauteur. Alertes de péremption.

**Dépendances dures** : telecom_hr_ma

---

## FAMILLE 5 — COMMERCIAL ET FINANCIER

### 16. telecom_facturation (future) — Facturation et relances

**Vague** : V1.5 — **Statut** : Optionnelle

**Rôle** : émission des factures clients (basées sur les situations de travaux ou ad-hoc), suivi des paiements, relances automatisées.

**Dépendances dures** : telecom_localization_ma

**Dépendances souples** : telecom_finance_ma

---

### 17. telecom_ao — Appels d'offres et BPU

**Vague** : V1.5 — **Statut** : Optionnelle

**Rôle** : pipeline commercial des AO, gestion des BPU (bordereau de prix unitaire), historique des soumissions.

**Dépendances dures** : telecom_base

---

### 18. telecom_contract — Contrats opérateurs et SLA

**Vague** : V1.5 — **Statut** : Optionnelle

**Rôle** : référentiel des contrats opérateurs, SLA, pénalités, alertes échéances.

**Dépendances dures** : telecom_base

---

### 24. telecom_contract (cautions) — Cautions bancaires

**Vague** : V2 — **Statut** : Optionnelle

**Rôle** : gestion des cautions bancaires (provisoire, définitive, retenue de garantie), alertes péremption, workflow de mainlevée.

**Dépendances dures** : telecom_base

**Dépendances souples** : telecom_project, telecom_financing (future)

---

### 25. telecom_localization_ma (CGNC) — Comptabilité générale Maroc

**Vague** : V2 — **Statut** : Optionnelle

**Rôle** : comptabilité générale conforme CGNC, peut être utilisée seule ou en complément d'un logiciel comptable existant via export.

**Dépendances dures** : telecom_localization_ma

---

### 26. telecom_reporting — Reporting et bilan social

**Vague** : V2 — **Statut** : Optionnelle

**Rôle** : dashboards transverses, KPI, bilan social CNSS, rapports exportables.

**Dépendances dures** : telecom_base

---

## Carte des dépendances de la vague MVP

```
telecom_base (socle)
  ├── telecom_tenant (future) (socle)
  ├── telecom_base (security) (socle)
  ├── telecom_localization_ma (socle)
  ├── telecom_project
  │     ├── telecom_cost (future)
  │     │     └── telecom_margin (future)
  │     └── telecom_finance_ma
  ├── telecom_site
  └── telecom_intervention
```

10 capabilities, dépendances claires, livrable en ~10-12 semaines à 2 (toi + Claude).

---

## Règles de gouvernance du catalogue

1. **Aucune capability ne peut être ajoutée sans figurer dans ce document.**
2. **Aucune capability ne peut être supprimée si un tenant l'a activée.**
3. **Un changement de dépendance d'une capability est un changement majeur** qui doit être validé hors session de dev.
4. **Le passage d'une capability d'une vague à une autre** doit être tracé avec la raison.
5. **Toute nouvelle capability doit prouver qu'elle ne peut pas être absorbée par une existante** avant d'être créée.

---

*Fin du document.*
