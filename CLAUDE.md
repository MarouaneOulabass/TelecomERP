# TelecomERP — Contexte Projet pour Claude Code

> **INSTRUCTION CRITIQUE** : Lire ce fichier **en entier** avant toute génération de code.
> Ne jamais modifier les fichiers dans `odoo/` (core Odoo). Tout passe par héritage.

---

## 1. VUE D'ENSEMBLE

**Produit** : Solution ERP verticale pour entreprises marocaines — déploiement et maintenance d'infrastructures télécom.

**Secteurs couverts** :
- Déploiement fibre optique (FTTH/FTTB)
- Déploiement sites mobiles (2G/3G/4G/5G)
- Maintenance infrastructure télécom
- Déploiement courant fort / courant faible

**Base technique** : Odoo 17 Community + modules custom dans `/custom_addons/`
**Principe fondamental** : Le core Odoo n'est JAMAIS modifié. Toute personnalisation = héritage ORM ou XML xpath.

**Stack** :
```
Backend   : Python 3.11, Odoo 17 ORM, PostgreSQL 15
Frontend  : Odoo QWeb (XML), OWL (JavaScript)
Tests BDD : pytest + pytest-bdd + freezegun
Dev       : Docker Compose
Versioning: Git
```

---

## 2. ARCHITECTURE DES MODULES

```
custom_addons/
├── telecom_base/              # P1 — Fondations, groupes sécurité, extension partenaires marocains
├── telecom_localization_ma/   # P1 — TVA, CGNC, mentions légales, LCN, RAS
├── telecom_site/              # P1 — Fiche site physique, GPS, bailleur, documents
├── telecom_intervention/      # P1 — Bons d'intervention terrain, rapports, photos, signature
├── telecom_hr_ma/             # P1 — Paie CNSS/AMO/IR, pointage chantier, habilitations, EPI, planning
├── telecom_equipment/         # P2 — Équipements par site, N° série, garantie, outillages
├── telecom_fleet/             # P2 — Parc véhicules terrain
├── telecom_project/           # P2 — Projets chantier, lots, planning, PV réception
├── telecom_ao/                # P2 — Pipeline appels d'offres, BPU, contrats-cadres
├── telecom_contract/          # P2 — Contrats opérateurs, SLA, cautions bancaires
├── telecom_finance_ma/        # P3 — Situations travaux, décomptes, avances, retenues
└── telecom_reporting/         # P3 — Dashboards métier, KPIs, exports opérateurs
```

**Modules Odoo natifs utilisés (ne pas recréer)** :

| Module Odoo | Usage |
|---|---|
| `contacts` / `res.partner` | Tiers — étendre avec champs marocains |
| `sale` | Devis et commandes clients |
| `purchase` | Commandes fournisseurs |
| `stock` | Inventaire, entrepôts, mouvements |
| `account` | Facturation, comptabilité |
| `project` | Structure projet/tâches — étendre |
| `hr` | Fiches employés — étendre |
| `hr_leave` | Congés |
| `hr_expense` | Notes de frais |
| `crm` | Opportunités commerciales, pipeline AO |
| `sale_subscription` | Contrats maintenance récurrents |
| `maintenance` | Base équipements — étendre |

**Modules exclus (ne pas installer)** :
```
website, website_sale, pos_restaurant, pos_retail,
mrp, mrp_workcenter, lunch, fleet (remplacé par telecom_fleet),
helpdesk (remplacé par telecom_intervention)
```

---

## 3. CONVENTIONS DE DÉVELOPPEMENT

### Nommage

| Élément | Convention | Exemple |
|---|---|---|
| Modèles Python | `telecom.xxx` | `telecom.site`, `telecom.intervention` |
| Tables SQL | `telecom_xxx` | `telecom_site`, `telecom_intervention` |
| Vues XML | `view_telecom_xxx_form/tree` | `view_telecom_site_form` |
| Actions | `action_telecom_xxx` | `action_telecom_site` |
| Menus | `menu_telecom_xxx` | `menu_telecom_site` |
| Séquences | `seq.telecom.xxx` | `seq.telecom.intervention` |

### Structure obligatoire d'un module custom

```
telecom_xxx/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── telecom_xxx.py
├── views/
│   └── telecom_xxx_views.xml
├── security/
│   ├── ir.model.access.csv      ← OBLIGATOIRE — sans ça Odoo refuse de charger
│   └── telecom_security.xml
├── data/
│   └── telecom_xxx_data.xml
├── report/
│   └── telecom_xxx_report.xml
├── tests/                       ← OBLIGATOIRE — BDD non négociable
│   ├── __init__.py
│   ├── features/
│   │   ├── xxx_creation.feature
│   │   ├── xxx_workflow.feature
│   │   └── xxx_regles_metier.feature
│   └── test_bdd_xxx.py
└── static/description/icon.png
```

### Règles Python
- Toujours hériter : `_inherit = 'res.partner'` plutôt que recréer
- Contraintes SQL : `_sql_constraints`
- Contraintes Python : `@api.constrains`
- Onchange : `@api.onchange`
- Champs calculés : `store=True` si utilisés en recherche/filtre
- Zéro logique métier dans les vues — tout dans les modèles
- Champs `monetary` : toujours avec `currency_id`, devise par défaut MAD

### Règles XML
- `id` unique par enregistrement, toujours
- Héritage de vues : `inherit_id` + `xpath`
- Pas de `eval` sauf si indispensable
- Séquences de chargement respectées dans `__manifest__.py`

### Règles générales
- Commentaires de code : **anglais**
- Documentation utilisateur : **français**
- Un commit par fonctionnalité, message en anglais
- Tester l'upgrade après chaque modif : `docker compose exec odoo odoo -u nom_module --stop-after-init`
- Pour chaque nouveau module : modèle → sécurité → vues → rapports → **tests BDD**

---

## 4. GROUPES DE SÉCURITÉ

```
Technicien Terrain        → lecture + saisie interventions
Chef de Chantier          → validation interventions, planning (hérite Technicien)
Chargé d'Affaires         → projets, commercial, facturation (hérite Chef de Chantier)
Responsable               → accès complet sauf config système (hérite Chargé d'Affaires)
Administrateur TelecomERP → configuration complète (hérite Responsable)
```

---

## 5. PÉRIMÈTRE FONCTIONNEL DÉTAILLÉ

### 5.1 Tiers & Contacts (`telecom_base` + `res.partner`)

| Fonctionnalité | Description | Statut |
|---|---|---|
| Fiche partenaire unifiée | client, fournisseur, prospect, sous-traitant, opérateur, bailleur | ✅ Garder |
| Champs légaux marocains | ICE (15 chiffres), IF, RC, Patente, CNSS | 🔧 Adapter |
| Type de tiers | opérateur télécom, bailleur de site, organisme public... | 🔧 Adapter |
| Contacts multiples | interlocuteur technique ≠ commercial ≠ comptable | ✅ Garder |
| Partenariats commerciaux | apporteur d'affaires, groupement, JV — conditions et commissions | 🆕 Développer |
| Sous-traitants | agrément, spécialités, capacité, contrats-cadres actifs | 🔧 Adapter |
| Certifications tiers | agrément ANRT, ONEE, ISO — suivi expiration + alertes | 🆕 Développer |
| Historique complet | toutes interactions, devis, contrats, interventions liés au tiers | ✅ Garder |

### 5.2 RH & Terrain (`telecom_hr_ma`)

| Fonctionnalité | Description | Statut |
|---|---|---|
| Fiche employé | données personnelles, contrat, poste, rattachement | ✅ Garder |
| Contrats de travail | CDI, CDD, intérim — suivi échéances | ✅ Garder |
| Congés & absences | demande, validation, soldes — règles code travail marocain | 🔧 Adapter |
| Notes de frais | déplacements, hébergement, per diem par zone géographique | 🔧 Adapter |
| Paie marocaine | CNSS (4,48%/10,64%), AMO (2,26%/3,96%), IR barème progressif, CIMR | 🔧 Adapter |
| Export DAMANCOM | fichier déclaration CNSS mensuelle format compatible | 🆕 Développer |
| Profil technicien | spécialités (fibre, RF, courant fort/faible), niveau, zone d'intervention | 🆕 Développer |
| Habilitations & certifications | travail en hauteur, habilitation électrique B1/B2/BR — suivi expiration | 🆕 Développer |
| Formations | plan de formation, suivi sessions, renouvellements obligatoires | 🆕 Développer |
| Pointage chantier | présence par site/jour, validation chef de chantier, intégration paie | 🆕 Développer |
| EPI & dotations | suivi équipements protection individuelle (casque, harnais, chaussures...) | 🆕 Développer |
| Planning terrain | affectation techniciens par site/jour, tournées, vue planning | 🆕 Développer |

### 5.3 Sites & Infrastructure (`telecom_site`)

| Fonctionnalité | Description | Statut |
|---|---|---|
| Fiche site | code interne + code opérateur, nom, type, statut, wilaya/commune | 🆕 Nouveau |
| Types de sites | pylône greenfield, rooftop, shelter, indoor/DAS, datacenter, cabinet FTTH, chambre tirage | 🆕 Nouveau |
| Géolocalisation | coordonnées GPS, affichage carte, recherche par zone | 🆕 Nouveau |
| Cycle de vie site | Prospection → Étude → Autorisation → Déploiement → Livré → Maintenance → Désactivé | 🆕 Nouveau |
| Opérateurs hébergés | lien vers fiches opérateurs (Maroc Telecom, Orange, Inwi, ONEE...) | 🆕 Nouveau |
| Bailleur & bail | propriétaire, référence contrat, date expiration, loyer mensuel, alertes | 🆕 Nouveau |
| Accès & sécurité | instructions accès, contact local, accès 24h/24, autorisation préalable | 🆕 Nouveau |
| Caractéristiques techniques | hauteur pylône, puissance électrique, groupe électrogène, batterie, clim | 🆕 Nouveau |
| Technologies déployées | tags : 2G, 3G, 4G, 5G, FTTH, MW, VSAT... | 🆕 Nouveau |
| Documents site | plans, PV réception, autorisations, photos, rapports — classés par type | 🆕 Nouveau |
| Historique site | toutes interventions, projets, équipements liés au site | 🆕 Nouveau |

### 5.4 Équipements & Outillages (`telecom_equipment`)

| Fonctionnalité | Description | Statut |
|---|---|---|
| Fiche équipement | catégorie, marque, modèle, N° série, site d'installation, fournisseur | 🆕 Nouveau |
| Catégories | antenne, BTS/NodeB/eNodeB, OLT/ONT, câble, shelter, groupe électrogène, clim, batterie... | 🆕 Nouveau |
| N° de série | traçabilité individuelle de chaque équipement | 🆕 Nouveau |
| Cycle de vie | En stock → Installé → En panne → En réparation → Retiré → Mis au rebut | 🆕 Nouveau |
| Garantie & contrat maintenance | date fin garantie, alertes renouvellement, contrat maintenance fournisseur | 🆕 Nouveau |
| Historique équipement | toutes interventions, pannes, remplacements | 🆕 Nouveau |
| Outillages terrain | OTDR, analyseur de spectre, testeur fibre — suivi, affectation, étalonnage | 🆕 Nouveau |
| Alertes maintenance préventive | rappels selon planning ou compteur d'heures | 🆕 Nouveau |

### 5.5 Parc Véhicules (`telecom_fleet`)

| Fonctionnalité | Description | Statut |
|---|---|---|
| Fiche véhicule | immatriculation, marque, modèle, kilométrage, affectation technicien | 🆕 Nouveau |
| Contrôle technique & assurance | dates expiration, alertes renouvellement | 🆕 Nouveau |
| Stock véhicule | chaque véhicule = entrepôt mobile dédié (lien stock Odoo) | 🆕 Nouveau |
| Entretiens & révisions | planning maintenance, historique réparations | 🆕 Nouveau |

### 5.6 Interventions Terrain (`telecom_intervention`)

| Fonctionnalité | Description | Statut |
|---|---|---|
| Bon d'intervention (BI) | création, numérotation auto, type (préventive/corrective/installation/audit) | 🆕 Nouveau |
| Affectation techniciens | un ou plusieurs techniciens, vérification habilitations requises | 🆕 Nouveau |
| Planification | date/heure planifiée, durée estimée, matériels à emporter | 🆕 Nouveau |
| Rapport d'intervention | description travaux, problèmes rencontrés, travaux restants | 🆕 Nouveau |
| Photos terrain | avant / pendant / après, associées au BI | 🆕 Nouveau |
| Matériels consommés | lien direct vers stock → sortie automatique des pièces utilisées | 🆕 Nouveau |
| Signature électronique | validation terrain technicien + représentant client | 🆕 Nouveau |
| Rapport PDF | génération PDF formaté, prêt à envoyer à l'opérateur | 🆕 Nouveau |
| SLA & délais | délai contractuel d'intervention, alertes dépassement SLA | 🆕 Nouveau |
| Facturation intervention | lien vers facture client si intervention hors contrat forfait | 🆕 Nouveau |

### 5.7 Projets & Chantiers (`telecom_project`)

| Fonctionnalité | Description | Statut |
|---|---|---|
| Structure projet | Projet → Lot → Site → Tâche (hiérarchie 4 niveaux) | 🔧 Adapter |
| Types de projets | déploiement FTTH, rollout 4G/5G, maintenance préventive, courant fort/faible | 🔧 Adapter |
| Affectation sites | liste des sites du projet, statut par site, responsable site | 🆕 Développer |
| Planning Gantt | vue Gantt par site, par lot, par technicien | 🔧 Adapter |
| Suivi avancement | % réalisation par site, par étape | 🆕 Développer |
| PV de réception | partielle / définitive, réserves, levée de réserves, signature | 🆕 Développer |
| KPIs projet | sites déployés/total, délai moyen, taux respect planning, coût réel vs budget | 🆕 Développer |
| Documents projet | DAO, CCAP, CCTP, plans, rapports — classés par type | ✅ Garder |

### 5.8 Commercial & Appels d'Offres (`telecom_ao`)

| Fonctionnalité | Description | Statut |
|---|---|---|
| Pipeline AO | référence DAO, maître d'ouvrage, date remise, lots visés, montant estimatif | 🆕 Nouveau |
| Statuts AO | Détecté → En étude → Soumis → Gagné/Perdu → Projet | 🆕 Nouveau |
| Bordereau de Prix Unitaires (BPU) | structure spécifique marchés travaux | 🆕 Nouveau |
| Cautions bancaires | caution provisoire (1,5%), définitive (3%) | 🆕 Nouveau |
| Contrat-cadre opérateur | conditions tarifaires négociées, durée, reconduction | 🆕 Nouveau |

### 5.9 Contrats (`telecom_contract`)

| Fonctionnalité | Description | Statut |
|---|---|---|
| Contrat de maintenance | périmètre sites, SLA, tarif forfaitaire vs à l'acte, durée, renouvellement | 🆕 Nouveau |
| Cautions bancaires | suivi caution provisoire, définitive, retenue de garantie | 🆕 Nouveau |
| Contrats récurrents | facturation périodique contrats maintenance | ✅ Garder |

### 5.10 Facturation & Finance (`telecom_finance_ma` + Odoo account)

| Fonctionnalité | Description | Statut |
|---|---|---|
| Plan comptable CGNC | remplacement plan comptable Odoo par CGNC marocain (classes 1 à 7) | 🆕 Développer |
| TVA marocaine | taux 20%, 14%, 10%, 7%, 0% — déclarations DGI | 🆕 Développer |
| Retenue à la source (RAS) | 10% prestations — déduction sur factures fournisseurs + certificat | 🆕 Développer |
| Effets de commerce (LCN) | Lettre de Change Normalisée — émission, suivi, remise en banque | 🆕 Développer |
| Situations de travaux | facturation progressive : % avancement × montant marché | 🆕 Nouveau |
| Décomptes provisoire/définitif | format CCAG Travaux marocain, retenue de garantie déduite | 🆕 Nouveau |
| Avances & acomptes marché | avance de démarrage (10-15%), suivi remboursement | 🆕 Nouveau |
| Retenue de garantie | 10% retenu à chaque décompte, libéré à réception définitive | 🆕 Nouveau |
| Délai paiement légal | alerte dépassement 60 jours (loi 69-21 marchés publics) | 🆕 Nouveau |

### 5.11 Reporting & Dashboards (`telecom_reporting`)

| Dashboard / Rapport | Contenu | Statut |
|---|---|---|
| Dashboard Direction | CA mensuel, marge brute, projets actifs, sites déployés, pipeline | 🆕 Développer |
| Dashboard Opérations | interventions du jour, techniciens terrain, alertes SLA, pannes | 🆕 Développer |
| Dashboard Commercial | pipeline AO, taux conversion, CA par opérateur | 🆕 Développer |
| Dashboard RH | présences terrain, congés, habilitations expirant, EPI à renouveler | 🆕 Développer |
| Rapport de production | sites livrés par période/type/opérateur, délai moyen | 🆕 Développer |
| Export format opérateur | rapports aux formats Maroc Telecom / Orange / Inwi | 🆕 Développer |
| Bilan social CNSS | état récapitulatif cotisations, export DAMANCOM | 🆕 Développer |

---

## 6. FLUX MÉTIER PRINCIPAUX

### Flux Déploiement
```
AO détecté (telecom_ao)
  → Constitution dossier + BPU + cautions
    → Contrat signé (telecom_contract)
      → Projet créé avec lots et sites (telecom_project + telecom_site)
        → Planning techniciens (telecom_hr_ma)
          → Commande matériels (Odoo Purchase + telecom_equipment)
            → Interventions terrain / BI (telecom_intervention)
              → Sortie stock automatique (Odoo Stock)
                → PV réception partielle/définitive (telecom_project)
                  → Situation de travaux / Décompte (telecom_finance_ma)
                    → Facture client (Odoo Account)
                      → Paiement & clôture
```

### Flux Maintenance
```
Contrat maintenance actif (telecom_contract + Odoo Subscription)
  → Déclenchement intervention (panne ou préventive) → BI (telecom_intervention)
    → Affectation technicien + vérification habilitations (telecom_hr_ma)
      → Intervention réalisée + rapport + photos
        → Vérification SLA — délai respecté ? (telecom_contract)
          → Facturation si hors contrat forfait (Odoo Account)
            → Clôture + mise à jour historique site/équipement
```

---

## 7. LOCALISATION MAROCAINE

### TVA

| Taux | Application |
|---|---|
| 20% | Standard — prestations services, équipements |
| 14% | Transport |
| 10% | Certains travaux, hôtellerie |
| 7% | Eau, électricité, médicaments |
| 0% | Exonéré (export) |

### Retenue à la source (RAS)
- **10%** sur prestations de services entre entreprises
- Apparaît en déduction sur factures fournisseurs
- Générer un certificat de retenue pour chaque fournisseur

### Mentions obligatoires sur chaque facture
```
ICE émetteur   : 15 chiffres (Identifiant Commun de l'Entreprise)
ICE client     : 15 chiffres
IF             : Identifiant Fiscal
RC             : Registre de Commerce
Patente        : Numéro de patente
Capital social : montant en MAD
Forme juridique: SARL, SA, etc.
Numérotation   : séquentielle continue sans rupture
```

### Plan comptable CGNC
```
Classe 1 : Comptes de financement permanent
Classe 2 : Comptes d'actif immobilisé
Classe 3 : Comptes d'actif circulant (stocks)
Classe 4 : Comptes de passif circulant (tiers)
Classe 5 : Comptes de trésorerie
Classe 6 : Comptes de charges
Classe 7 : Comptes de produits
```

### Paie marocaine

| Cotisation | Taux salarié | Taux patronal | Plafond |
|---|---|---|---|
| CNSS | 4,48% | 10,64% | 6 000 MAD/mois |
| AMO | 2,26% | 3,96% | Sans plafond |
| CIMR | Variable | Variable | Selon accord |
| IR | Barème 0%→38% | — | — |

Barème IR 2024 :
```
0        → 30 000 MAD  : 0%
30 001   → 50 000 MAD  : 10%
50 001   → 60 000 MAD  : 20%
60 001   → 80 000 MAD  : 30%
80 001   → 180 000 MAD : 34%
> 180 000 MAD          : 38%
```

### Marchés publics — CCAG Travaux Maroc

| Règle | Valeur | Module |
|---|---|---|
| Caution provisoire | 1,5% du montant estimatif | telecom_contract |
| Caution définitive | 3% du montant attribué | telecom_contract |
| Retenue de garantie | 10% déduit sur chaque décompte | telecom_finance_ma |
| Délai paiement légal | 60 jours max (loi 69-21) | telecom_finance_ma |
| Avance de démarrage | 10% à 15% selon CCAP | telecom_finance_ma |
| PV réception partielle | Obligatoire avant décompte | telecom_project |
| PV réception définitive | Libération retenue de garantie | telecom_project |

---

## 8. GLOSSAIRE MÉTIER

| Terme | Définition |
|---|---|
| Site | Emplacement physique d'infrastructure (pylône, rooftop, shelter, datacenter) |
| Bailleur | Propriétaire du terrain ou bâtiment hébergeant le site |
| Opérateur | Client donneur d'ordre (Maroc Telecom, Orange Maroc, Inwi, ONEE) |
| BI | Bon d'Intervention — document de mission terrain pour un technicien |
| BPU | Bordereau de Prix Unitaires — grille tarifaire marchés travaux |
| Situation de travaux | Facturation progressive sur avancement d'un marché |
| Décompte | Document de décompte financier marché public (provisoire/définitif) |
| Retenue de garantie | 10% retenu sur décomptes, libéré à réception définitive |
| Caution bancaire | Garantie financière : provisoire (1,5%) / définitive (3%) |
| CCAG Travaux | Cahier des Clauses Administratives Générales — marchés publics Maroc |
| DAO | Dossier d'Appel d'Offres |
| CCAP | Cahier des Clauses Administratives Particulières |
| CCTP | Cahier des Clauses Techniques Particulières |
| AO | Appel d'Offres |
| PV réception | Procès-verbal de réception (partielle ou définitive) |
| Habilitation | Certification technicien (travail en hauteur, électrique B1/B2/BR) |
| EPI | Équipements de Protection Individuelle |
| FTTH | Fiber To The Home |
| FTTB | Fiber To The Building |
| OLT | Optical Line Terminal — équipement central réseau fibre |
| ONT | Optical Network Terminal — équipement abonné réseau fibre |
| BTS | Base Transceiver Station — station de base 2G |
| NodeB | Station de base 3G |
| eNodeB | Station de base 4G LTE |
| gNodeB | Station de base 5G |
| OTDR | Optical Time Domain Reflectometer — outil de test fibre optique |
| LCN | Lettre de Change Normalisée — effet de commerce marocain |
| DAMANCOM | Plateforme déclaration CNSS en ligne |
| CGNC | Code Général de Normalisation Comptable — plan comptable marocain |
| RAS | Retenue À la Source |
| ICE | Identifiant Commun de l'Entreprise (15 chiffres) |
| IF | Identifiant Fiscal |
| RC | Registre de Commerce |
| ANRT | Agence Nationale de Réglementation des Télécommunications |
| ONEE | Office National de l'Électricité et de l'Eau Potable |

---

## 9. PLAN DE DÉVELOPPEMENT

### Phase 1 — Fondations & Core métier (8-10 semaines)

| Module | Contenu |
|---|---|
| `telecom_base` | Structure, sécurité, extension partenaires marocains |
| `telecom_localization_ma` | TVA, CGNC, mentions légales, LCN, RAS |
| `telecom_site` | Fiche site, GPS, statuts, bailleur, documents |
| `telecom_intervention` | BI terrain, rapport, photos, signature, PDF |
| `telecom_hr_ma` | Paie marocaine, pointage chantier, habilitations, EPI, planning |

### Phase 2 — Projet, Commercial & Logistique (6-8 semaines)

| Module | Contenu |
|---|---|
| `telecom_project` | Projets chantier, Gantt, avancement, PV réception |
| `telecom_ao` | Pipeline AO, BPU, contrats-cadres opérateurs |
| `telecom_contract` | Contrats, SLA, cautions bancaires, alertes |
| `telecom_equipment` | Équipements par site, outillages, historique |
| `telecom_fleet` | Parc véhicules terrain, stocks mobiles |

### Phase 3 — Finance avancée & Reporting (4-5 semaines)

| Module | Contenu |
|---|---|
| `telecom_finance_ma` | Situations travaux, décomptes, avances, retenues, délais paiement |
| `telecom_reporting` | Dashboards, KPIs, exports formats opérateurs, bilan social |

---

## 10. POINTS OUVERTS

> Décisions à prendre avant de démarrer les modules concernés.

| # | Sujet | Option A | Option B | Décision |
|---|---|---|---|---|
| 1 | Portail client opérateur | Dans V1 | En V2 | ⏳ En attente |
| 2 | Pipeline AO | Extension CRM natif | Module `telecom_ao` dédié | ⏳ En attente |
| 3 | Contrats | Intégré dans Projet/Site | Module `telecom_contract` dédié | ⏳ En attente |
| 4 | Outillages terrain | Dans `telecom_equipment` | Modèle `telecom.tool` séparé | ⏳ En attente |

---

## 11. INSTRUCTIONS CLAUDE CODE

1. **Lire ce fichier en entier** avant toute génération de code
2. **Ne jamais modifier** les fichiers dans `odoo/` (core)
3. **Toujours inclure** `ir.model.access.csv` dans chaque module
4. **Toujours tester** l'upgrade : `docker compose exec odoo odoo -u nom_module --stop-after-init`
5. **Commits atomiques** : un commit par fonctionnalité, message en anglais
6. En cas de doute sur un modèle Odoo existant → inspecter avant d'hériter
7. **Rapports PDF** : QWeb XML — toujours template + action rapport
8. **Commentaires code en anglais**, documentation utilisateur en français
9. Champs `monetary` → toujours `currency_id`, devise par défaut MAD
10. Démarrer chaque module dans cet ordre : modèle → sécurité → vues → rapports → **tests BDD**
11. **JAMAIS de déploiement** sans avoir exécuté : `bash bin/pre-deploy-tests.sh`

---

## 12. ARCHITECTURE BDD — TESTS DE NON-RÉGRESSION

### Philosophie

Le projet adopte une **architecture BDD (Behavior-Driven Development)** :
- Les règles métier sont définies en **Gherkin** (`.feature` files) — langage naturel lisible par le métier
- Le métier a la main sur la définition du comportement attendu
- Les développeurs implémentent les step definitions en Python
- La suite BDD bloque tout déploiement en cas d'échec

### Structure par module

```
telecom_xxx/
└── tests/
    ├── __init__.py
    ├── features/                    ← PROPRIÉTÉ DU MÉTIER
    │   ├── xxx_creation.feature     ← "Quand je crée X, alors Y se passe"
    │   ├── xxx_workflow.feature     ← Transitions d'état, règles de passage
    │   ├── xxx_calculs.feature      ← Formules, barèmes, calculs automatiques
    │   └── xxx_regles_metier.feature← Contraintes, validations, interdictions
    └── test_bdd_xxx.py              ← PROPRIÉTÉ DES DÉVELOPPEURS
                                        (implémentation des steps)
```

### Stack technique

```
pytest         : runner de tests
pytest-bdd     : parsing Gherkin + liaison Given/When/Then → Python
freezegun      : simulation de dates (SLA, bail, délais paiement)
pytest-cov     : couverture de code
pytest-html    : rapport HTML lisible par le management
```

### Conventions Gherkin

```gherkin
# language: fr
Feature: [Nom de la fonctionnalité]
  En tant que [rôle métier]
  Je veux [objectif]
  Afin de [bénéfice]

  Background:         # données communes à tous les scénarios
    Given ...

  Scenario: [Cas nominal]
    Given  [contexte initial]
    When   [action déclenchante]
    Then   [résultat attendu]
    And    [résultat complémentaire]

  Scenario Outline: [Cas paramétré — barèmes, taux, tranches]
    Given un salaire de "<salaire>"
    Then  le calcul donne "<résultat>"
    Examples:
      | salaire | résultat |
      | 4000    | 179.20   |
      | 10000   | 268.80   |
```

### Lancer les tests

```bash
# Tous les modules
bash bin/pre-deploy-tests.sh

# Un module spécifique
bash bin/pre-deploy-tests.sh --module paie

# Tests smoke uniquement (rapides)
bash bin/pre-deploy-tests.sh --smoke

# Avec rapport HTML
bash bin/pre-deploy-tests.sh --report

# Directement avec pytest (si Odoo accessible localement)
pytest custom_addons/telecom_site/tests/ -v
pytest custom_addons/ -m paie -v
pytest custom_addons/ -k "cnss or amo" -v
```

### Couverture minimale exigée par module

| Module | Scénarios minimum | Cas critiques obligatoires |
|---|---|---|
| `telecom_site` | 15 | GPS invalides, bail expiry, cycle de vie complet |
| `telecom_intervention` | 20 | Workflow complet, SLA, contrôle accès chef |
| `telecom_hr_ma` | 30 | Toutes tranches IR, plafonds CNSS, paliers ancienneté |
| `telecom_finance_ma` | 25 | CCAG complet, loi 69-21, décompte définitif |
| `telecom_ao` | 15 | Pipeline AO, cautions 1.5%/3%, BPU |
| `telecom_contract` | 10 | SLA, alertes, transitions |
| `telecom_equipment` | 12 | Cycle vie, garantie, étalonnage |
| `telecom_fleet` | 8 | CT, assurance, alertes |
| `telecom_project` | 12 | Structure hiérarchique, PV réception |
| `telecom_base` | 8 | ICE validation, types partenaires |
| `telecom_localization_ma` | 10 | TVA taux, RAS 10% |
| `telecom_reporting` | 5 | Cohérence KPIs |

### Règle d'or

> **Un scénario BDD = une règle métier = un test automatisé.**
> Si la règle n'est pas dans un `.feature` file, elle n'existe pas.
