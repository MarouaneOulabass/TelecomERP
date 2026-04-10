# TelecomERP — Documentation Complète

> **Version** : 17.0.1.0.0
> **Date** : Avril 2026
> **Stack** : Odoo 17 Community + PostgreSQL 15 + Docker + Nginx
> **URL Production** : https://erp.kleanse.fr
> **Repo** : https://github.com/MarouaneOulabass/TelecomERP

---

## Table des matières

1. [Présentation générale](#1-présentation-générale)
2. [Architecture technique](#2-architecture-technique)
3. [Module telecom_base — Fondations](#3-module-telecom_base--fondations)
4. [Module telecom_localization_ma — Localisation marocaine](#4-module-telecom_localization_ma--localisation-marocaine)
5. [Module telecom_site — Sites & Infrastructure](#5-module-telecom_site--sites--infrastructure)
6. [Module telecom_intervention — Interventions terrain](#6-module-telecom_intervention--interventions-terrain)
7. [Module telecom_hr_ma — RH & Paie marocaine](#7-module-telecom_hr_ma--rh--paie-marocaine)
8. [Module telecom_equipment — Équipements & Outillages](#8-module-telecom_equipment--équipements--outillages)
9. [Module telecom_fleet — Parc véhicules](#9-module-telecom_fleet--parc-véhicules)
10. [Module telecom_project — Projets & Chantiers](#10-module-telecom_project--projets--chantiers)
11. [Module telecom_ao — Appels d'Offres](#11-module-telecom_ao--appels-doffres)
12. [Module telecom_contract — Contrats](#12-module-telecom_contract--contrats)
13. [Module telecom_finance_ma — Finance CCAG](#13-module-telecom_finance_ma--finance-ccag)
14. [Module telecom_reporting — Reporting & Dashboards](#14-module-telecom_reporting--reporting--dashboards)
15. [Module telecom_test_admin — Administration des tests](#15-module-telecom_test_admin--administration-des-tests)
16. [Conformité légale marocaine](#16-conformité-légale-marocaine)
17. [Tests BDD — Couverture complète](#17-tests-bdd--couverture-complète)
18. [Corrections et améliorations Odoo 17](#18-corrections-et-améliorations-odoo-17)
19. [Infrastructure & Déploiement](#19-infrastructure--déploiement)
20. [Données de démonstration](#20-données-de-démonstration)
21. [Guide utilisateur](#21-guide-utilisateur)

---

## 1. Présentation générale

### Qu'est-ce que TelecomERP ?

TelecomERP est un **ERP vertical** conçu pour les entreprises marocaines de déploiement et maintenance d'infrastructures télécom. Il couvre l'ensemble du cycle de vie d'un marché public de travaux télécom, de l'appel d'offres à la facturation finale.

### Secteurs couverts

- **Fibre optique** — Déploiement FTTH/FTTB, raccordement abonnés
- **Sites mobiles** — Installation et maintenance stations de base 2G/3G/4G/5G
- **Maintenance télécom** — Interventions préventives et correctives sur infrastructure
- **Courant fort / courant faible** — Installations électriques et réseaux

### Opérateurs partenaires

- **Maroc Telecom (IAM)** — Opérateur historique
- **Orange Maroc (Médi Telecom)** — Deuxième opérateur
- **Inwi (Wana Corporate)** — Troisième opérateur
- **ONEE** — Office National de l'Électricité et de l'Eau Potable

### Principe fondamental

Le core Odoo n'est **jamais modifié**. Toute personnalisation passe par héritage ORM (`_inherit`) ou extension XML (`xpath`). Cela garantit la compatibilité avec les mises à jour Odoo.

---

## 2. Architecture technique

### Stack technologique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Backend | Python + Odoo ORM | 3.10 / 17.0 |
| Base de données | PostgreSQL | 15 |
| Frontend | Odoo QWeb + OWL | 17.0 |
| Conteneurisation | Docker Compose | 29.4 |
| Reverse proxy | Nginx | 1.29 |
| SSL | Let's Encrypt (Certbot) | Auto-renew |
| Tests | pytest + pytest-bdd + freezegun | 8.1 / 1.4 |
| Serveur | Hetzner CPX22 (Helsinki) | Ubuntu 24.04 |

### Architecture des modules

```
custom_addons/                    13 modules
├── telecom_base/                 P1 — Fondations, sécurité, partenaires marocains
├── telecom_localization_ma/      P1 — TVA, CGNC, RAS, LCN, mentions légales
├── telecom_site/                 P1 — Sites physiques, GPS, bailleur, documents
├── telecom_intervention/         P1 — Bons d'intervention terrain
├── telecom_hr_ma/                P1 — Paie CNSS/AMO/IR, habilitations, EPI, pointage
├── telecom_equipment/            P2 — Équipements par site, outillages
├── telecom_fleet/                P2 — Parc véhicules terrain
├── telecom_project/              P2 — Projets, lots, PV réception
├── telecom_ao/                   P2 — Pipeline appels d'offres, BPU
├── telecom_contract/             P2 — Contrats, SLA, cautions bancaires
├── telecom_finance_ma/           P3 — Situations travaux, décomptes CCAG
├── telecom_reporting/            P3 — Dashboards, KPIs, exports
└── telecom_test_admin/           — Interface admin tests BDD
```

### Modules Odoo natifs utilisés (non recréés)

| Module natif | Usage dans TelecomERP |
|---|---|
| `contacts` / `res.partner` | Tiers — étendu avec champs marocains |
| `sale` | Devis et commandes clients |
| `purchase` | Commandes fournisseurs |
| `stock` | Inventaire, entrepôts mobiles véhicules |
| `account` | Facturation, comptabilité |
| `project` | Structure projets — étendu avec lots et PV |
| `hr` | Fiches employés — étendu techniciens terrain |
| `hr_contract` | Contrats de travail CDI/CDD |
| `hr_holidays` | Congés et absences |
| `crm` | Opportunités commerciales |
| `maintenance` | Base équipements — étendu |
| `mail` | Chatter, notifications, activités |

### Groupes de sécurité (hiérarchie)

```
Technicien Terrain        → Lecture + saisie interventions
  ↑
Chef de Chantier          → Validation interventions, planning
  ↑
Chargé d'Affaires         → Projets, commercial, facturation
  ↑
Responsable               → Accès complet sauf config système
  ↑
Administrateur TelecomERP → Configuration complète
```

---

## 3. Module telecom_base — Fondations

### Modèles

| Modèle | Description |
|--------|-------------|
| `res.partner` (hérité) | Extension partenaire avec champs légaux marocains |
| `res.company` (hérité) | Extension société avec ICE, IF, RC, capital social |
| `telecom.specialite` | Table de référence des spécialités techniques |
| `telecom.certification` | Certifications et agréments des partenaires |

### Fonctionnalités détaillées

**Extension partenaire (`res.partner`)** :
- **ICE** — Identifiant Commun de l'Entreprise (15 chiffres, validation regex)
- **IF** — Identifiant Fiscal
- **RC** — Registre de Commerce
- **Patente** — Numéro de patente
- **N° CNSS** — Numéro CNSS employeur
- **Forme juridique** — SARL, SA, SARL AU, SAS, SNC, GIE, Auto-entrepreneur
- **Capital social** — En MAD avec champ monétaire
- **Type de tiers télécom** — Opérateur, Bailleur, Sous-traitant, Organisme public, Fournisseur
- **Spécialités** — Many2many vers telecom.specialite (fibre, RF, courant fort...)
- **Apporteur d'affaires** — Boolean + taux commission (%)

**Certifications (`telecom.certification`)** :
- Types : Agrément ANRT, Qualification ONEE, ISO 9001/14001/45001, Qualibat, Autre
- Suivi expiration avec statut automatique (valid / expiring_soon / expired)
- Document scanné attachable
- Alertes 60 jours avant expiration

**Page d'accueil** :
- Route `/telecom/welcome` avec dashboard visuel
- Statistiques live (sites, interventions, employés, contrats)
- Cards modules cliquables
- Badges secteurs et opérateurs partenaires

---

## 4. Module telecom_localization_ma — Localisation marocaine

### TVA marocaine (CGI Art. 89-103)

| Taux | Application | Vente | Achat |
|------|-------------|-------|-------|
| 20% | Standard — prestations services, équipements | Oui | Oui |
| 14% | Transport, travaux immobiliers | Oui | Oui |
| 10% | Certains travaux, hôtellerie | Oui | Oui |
| 7% | Eau, électricité, médicaments | Oui | Oui |
| 0% | Exonéré / Export | Oui | — |

Toutes les taxes sont créées avec `country_id = Maroc` et un groupe de taxe dédié (`TVA Maroc`).

### Retenue à la Source — RAS (CGI Art. 15)

- **Taux** : 10% sur prestations de services entre entreprises
- **Application** : Factures fournisseurs (`type_tax_use = purchase`)
- **Montant négatif** : -10% (réduit le net à payer)
- **Marqueur** : Champ `is_ras = True` sur `account.tax`
- **Groupe de taxe** : `RAS Maroc`
- Apparaît en déduction sur factures fournisseurs
- Génération certificat de retenue (à développer)

### Plan comptable CGNC (Loi 9-88)

80+ comptes créés couvrant les 7 classes du Code Général de Normalisation Comptable :

| Classe | Intitulé | Comptes |
|--------|----------|---------|
| 1 | Comptes de financement permanent | Capital, réserves, résultat, emprunts, provisions |
| 2 | Comptes d'actif immobilisé | Immobilisations incorporelles, corporelles, financières, amortissements |
| 3 | Comptes d'actif circulant | Stocks matières/produits, créances clients, État débiteur |
| 4 | Comptes de passif circulant | Fournisseurs, personnel, CNSS, AMO, CIMR, État TVA/IS |
| 5 | Comptes de trésorerie | Banques, CCP, caisse, virements de fonds |
| 6 | Comptes de charges | Achats, services extérieurs, impôts, charges sociales, dotations, charges financières, IS |
| 7 | Comptes de produits | Ventes services/marchandises, variation stocks, produits financiers, reprises |

### Lettre de Change Normalisée (LCN)

- Champ `is_lcn` sur `account.journal`
- Configuration spécifique pour les effets de commerce marocains
- Champs : numéro LCN, date échéance, date endossement

### Mentions légales obligatoires factures (CGI Art. 145)

Champs disponibles sur `res.partner` et `res.company` :
- ICE émetteur et client (15 chiffres)
- Identifiant Fiscal (IF)
- Registre de Commerce (RC)
- Patente
- Capital social et forme juridique
- Numérotation séquentielle continue

---

## 5. Module telecom_site — Sites & Infrastructure

### Modèles

| Modèle | Description |
|--------|-------------|
| `telecom.site` | Fiche site physique principale |
| `telecom.site.document` | Documents attachés à un site |
| `telecom.technologie` | Table de référence technologies (2G, 4G, FTTH...) |

### Types de sites

| Type | Code | Description |
|------|------|-------------|
| Pylône Greenfield | `pylone_greenfield` | Pylône construit sur terrain vierge |
| Rooftop | `rooftop` | Équipements installés en toiture |
| Shelter | `shelter` | Abri technique préfabriqué |
| Indoor / DAS | `indoor_das` | Système d'antennes distribuées en intérieur |
| Datacenter | `datacenter` | Centre de données |
| Cabinet FTTH | `cabinet_ftth` | Armoire de distribution fibre |
| Chambre de tirage | `chambre_tirage` | Chambre souterraine câbles |
| Autre | `autre` | Autre type |

### Cycle de vie du site (7 états)

```
Prospection → Étude technique → En cours d'autorisation → Déploiement → Livré / Opérationnel → En maintenance → Désactivé
```

### Géolocalisation

- **Latitude / Longitude** — Coordonnées GPS avec validation (-90/+90, -180/+180)
- **Bouton Google Maps** — Ouvre la localisation dans Google Maps
- **12 régions du Maroc** (Wilaya) :
  - Casablanca-Settat, Rabat-Salé-Kénitra, Marrakech-Safi, Fès-Meknès
  - Tanger-Tétouan-Al Hoceïma, Souss-Massa, Drâa-Tafilalet, Béni Mellal-Khénifra
  - L'Oriental, Guelmim-Oued Noun, Laâyoune-Sakia El Hamra, Dakhla-Oued Ed-Dahab

### Bailleur et bail

- **Bailleur** — Lien vers `res.partner` (type `lessor`)
- **Référence bail** — Numéro de contrat bail
- **Dates** — Début et fin de bail
- **Alerte expiration** — Champ calculé `bail_expiration_warning` (< 90 jours)

### Technologies déployées

- Tags many2many vers `telecom.technologie`
- Valeurs prédéfinies : 2G, 3G, 4G LTE, 5G NR, FTTH, FH/MW, VSAT

### Documents site

- Modèle `telecom.site.document`
- Types : Plan, PV réception, Autorisation, Photo, Rapport, Autre
- Fichier binaire attachable
- Compteur documents sur la fiche site

---

## 6. Module telecom_intervention — Interventions terrain

### Modèles

| Modèle | Description |
|--------|-------------|
| `telecom.intervention` | Bon d'Intervention (BI) |
| `telecom.intervention.photo` | Photos terrain (avant/pendant/après) |
| `telecom.materiel.consomme` | Matériels consommés par intervention |

### Types d'intervention

| Type | Description |
|------|-------------|
| Préventive | Maintenance planifiée |
| Corrective | Dépannage suite à panne |
| Installation | Mise en service nouvel équipement |
| Audit | Contrôle technique (ANRT, opérateur) |
| Dépose | Retrait d'équipement |

### Workflow complet (7 états)

```
Brouillon → Planifié → En cours → Terminé (terrain) → Validé (chef) → Facturé → Annulé
```

Règles de transition :
- **Planification** : requiert date planifiée
- **Démarrage** : enregistre date/heure réelle de début
- **Terminaison** : enregistre date/heure réelle de fin
- **Validation** : réservée au Chef de Chantier ou supérieur
- **Annulation** : impossible si déjà facturé
- **Remise en brouillon** : uniquement depuis Annulé

### SLA et délais

- **Délai SLA** (`sla_delai_heures`) — Heures contractuelles d'intervention
- **Échéance SLA** (`sla_echeance`) — Date planifiée + délai SLA
- **SLA dépassé** (`sla_depasse`) — Boolean calculé
- **Couleur SLA** (`sla_couleur`) :
  - Vert (0) — Plus de 24h avant échéance, ou BI validé/annulé
  - Orange (1) — Moins de 24h avant échéance
  - Rouge (2) — SLA dépassé et BI encore en cours

### Durée réelle

- Calculée automatiquement : `date_fin_reelle - date_debut_reelle`
- Exprimée en heures décimales (ex: 2h30 = 2.5)

### Photos terrain

- Types : Avant intervention, Pendant, Après, Anomalie, Autre
- Fichier binaire avec nom de fichier
- Liées au BI via One2many

### Signature électronique

- **Signature technicien** — Champ `signature_technicien` (binary)
- **Signature client** — Champ `signature_client` (binary)
- **Nom signataire client** — Texte libre

### Matériels consommés

- Modèle `telecom.materiel.consomme`
- Lien vers `product.product` (article Odoo)
- Quantité utilisée
- Sortie stock automatique possible (lien stock.move)

### Rapport PDF

- Template QWeb `telecom_intervention_report`
- Format A4 avec toutes les informations du BI
- Prêt à envoyer à l'opérateur

---

## 7. Module telecom_hr_ma — RH & Paie marocaine

### Modèles

| Modèle | Description |
|--------|-------------|
| `hr.employee` (hérité) | Extension profil technicien |
| `hr.contract` (natif) | Contrats de travail |
| `telecom.paie.bulletin` | Bulletin de paie marocain |
| `telecom.habilitation.type` | Types d'habilitations sécurité |
| `telecom.habilitation.employee` | Habilitations par employé |
| `telecom.epi.type` | Types d'EPI |
| `telecom.epi.dotation` | Dotations EPI par employé |
| `telecom.pointage.chantier` | Pointage quotidien terrain |
| `telecom.damancom.export.wizard` | Export DAMANCOM (CNSS) |

### Profil technicien terrain

Champs ajoutés sur `hr.employee` :
- **Technicien télécom** (`telecom_technicien`) — Boolean
- **Taux CIMR salarié / patronal** — Pourcentages variables
- **Nombre de parts IR** — Pour déductions charges de famille
- **Habilitations** — One2many avec alertes expiration
- **Dotations EPI** — One2many avec alertes renouvellement

### Paie marocaine — Bulletin de paie

#### CNSS (Loi 1-72-184, Dahir 27/07/1972)

| Cotisation | Taux salarié | Taux patronal | Plafond |
|------------|-------------|---------------|---------|
| CNSS | 4,48% | 10,64% | 6 000 MAD/mois |

- Base CNSS = min(salaire brut, 6 000)
- Au-delà du plafond : cotisation figée à 268,80 MAD (salarié) / 638,40 MAD (patronal)

#### AMO (Loi 65-00)

| Cotisation | Taux salarié | Taux patronal | Plafond |
|------------|-------------|---------------|---------|
| AMO | 2,26% | 3,96% | **Sans plafond** |

- Calculée sur la totalité du salaire brut

#### CIMR (retraite complémentaire)

- Taux variable par employé (configuré sur la fiche)
- Typiquement 3% à 6% salarié / 3,5% à 6,5% patronal
- Calculée sur le salaire brut sans plafond

#### IR — Impôt sur le Revenu (Barème 2024)

| Tranche annuelle | Taux |
|-----------------|------|
| 0 → 30 000 MAD | 0% |
| 30 001 → 50 000 MAD | 10% |
| 50 001 → 60 000 MAD | 20% |
| 60 001 → 80 000 MAD | 30% |
| 80 001 → 180 000 MAD | 34% |
| > 180 000 MAD | 38% |

- **Frais professionnels** : 20% du salaire brut, plafonnés à 2 500 MAD/mois (30 000 MAD/an)
- **Déductions charges de famille** : 30 MAD/mois par part supplémentaire au-delà de la 1ère
- **IR mensuel** = max(0, IR mensuel brut - déductions famille)

#### Prime d'ancienneté (Code du Travail Art. 350-353)

| Ancienneté | Taux |
|------------|------|
| < 2 ans | 0% |
| 2 à 5 ans | 5% |
| 5 à 12 ans | 10% |
| 12 à 20 ans | 15% |
| > 20 ans | 20% |

- Calculée sur le salaire de base
- Date d'ancienneté = date du premier contrat

#### Formule complète du net à payer

```
Salaire brut = Salaire de base + Prime ancienneté + Avantages en nature
Cotisations salariales = CNSS + AMO + CIMR
Salaire net imposable = Brut - Cotisations salariales + Avantages en nature
Frais professionnels = min(Salaire net imposable × 20%, 2 500)
Salaire imposable IR = Net imposable - Frais pro - Indemnités déplacement
IR mensuel brut = Barème progressif / 12
IR mensuel net = max(0, IR brut - 30 × (parts - 1))
Net à payer = max(0, Brut - Cotisations salariales - IR mensuel net)
```

#### Workflow bulletin

```
Brouillon → Confirmé (séquence auto) → Validé → Payé
```

- Un seul bulletin par employé par mois (contrainte SQL unique)
- Salaire de base négatif refusé (contrainte Python)
- Rapport PDF QWeb

### Habilitations sécurité

Types prédéfinis :
- Travail en hauteur (36 mois)
- Habilitation électrique B1 (24 mois), B2 (12 mois), BR (24 mois)
- CACES Nacelle (60 mois)
- SST — Sauveteur Secouriste du Travail (24 mois)
- Risques chimiques N1 (36 mois)
- Conduite engins de chantier (60 mois)

Fonctionnalités :
- Date d'expiration calculée auto (obtention + périodicité)
- Statut automatique : valid / expiring_soon (< 60j) / expired
- Alertes sur fiche employé
- Code et nom uniques (contraintes SQL)

### EPI — Équipements de Protection Individuelle

Types prédéfinis :
- Casque de chantier (36 mois)
- Harnais antichute (12 mois)
- Chaussures de sécurité (12 mois)
- Gants isolants (12 mois)
- Lunettes de protection (24 mois)
- Gilet haute visibilité (24 mois)
- Protection auditive (36 mois)
- Masque respiratoire (12 mois)

Fonctionnalités :
- Date expiration calculée auto (dotation + périodicité)
- Statut automatique : valid / expiring_soon / expired
- État physique : Neuf / Bon état / Usé / À remplacer / Remplacé
- Quantité par dotation

### Pointage chantier

- Un pointage par employé × site × jour (contrainte SQL unique)
- Heures début/fin en format décimal (8.5 = 08h30)
- **Durée calculée** automatiquement
- **Heures supplémentaires** = max(0, durée - 8h)
- **Prime de déplacement** — Montant en MAD par jour
- **Workflow** : Brouillon → Validé / Refusé
- **Vue calendrier** pour le planning terrain
- Validation par chef de chantier

### Export DAMANCOM

- Wizard transient (`telecom.damancom.export.wizard`)
- Sélection mois/année
- Génère un fichier CSV avec colonnes :
  - N° CNSS employé, Nom, Prénom, Salaire brut, Jours travaillés, CNSS salarié, CNSS patronal
- Téléchargement direct du fichier

---

## 8. Module telecom_equipment — Équipements & Outillages

### Modèles

| Modèle | Description |
|--------|-------------|
| `telecom.equipment` | Équipement physique individuel |
| `telecom.equipment.category` | Catégories d'équipements |
| `telecom.equipment.historique` | Journal d'événements immuable |
| `telecom.outillage` | Outillages terrain |

### Catégories d'équipements

Antenne 4G/5G, eNodeB/gNodeB, OLT, ONT, Shelter, Groupe électrogène, Batterie, Climatisation, Câble fibre optique, Baie de brassage

### Cycle de vie équipement (6 états)

```
En stock → Installé → En panne → En réparation/SAV → Retiré du service → Mis au rebut
```

Règles de transition :
- **Installation** : requiert un site assigné, enregistre la date d'installation
- **Panne** : uniquement depuis l'état Installé
- **Réparation** : depuis En panne ou Installé
- **Remise en service** : depuis Réparation ou En stock, requiert un site

### Traçabilité

- **Code auto-généré** : EQ/CAT/00001 (catégorie + ID)
- **Numéro de série** unique par société (contrainte SQL)
- **Historique automatique** : un enregistrement `telecom.equipment.historique` est créé à chaque changement d'état via override de `write()`
- Types d'événements : Installation, Panne, Réparation, Maintenance préventive, Retrait, Autre

### Garantie

- Date de fin de garantie fournisseur
- Alerte `garantie_expiring` — True si expiration dans les 60 prochains jours
- Contrainte : date fin garantie > date achat

### Outillages terrain

Types : OTDR, Analyseur de spectre, Testeur puissance fibre, Multimètre, Analyseur antenne, Testeur câble, Autre

Fonctionnalités :
- Numéro de série unique
- Date dernier étalonnage + périodicité (mois)
- Alerte `etalonnage_expiring` — étalonnage dû
- Cycle de vie : Disponible / En mission / En étalonnage / Hors service

---

## 9. Module telecom_fleet — Parc véhicules

### Modèles

| Modèle | Description |
|--------|-------------|
| `telecom.vehicle` | Véhicule de la flotte terrain |
| `telecom.vehicle.entretien` | Enregistrement d'entretien |

### Fiche véhicule

- **Immatriculation** — Unique par société (format marocain : 12345-A-78)
- **Marque / Modèle** — Requis
- **Année de mise en circulation**
- **Carburant** — Diesel, Essence, Hybride, Électrique
- **Puissance fiscale** (CV)
- **Kilométrage actuel** — Mis à jour manuellement ou via entretien
- **Catégorie** — Camionnette/Pick-up, Utilitaire, Van, Berline/SUV, Moto, Autre

### Cycle de vie véhicule (5 états)

```
Disponible → En mission → En entretien → Hors service → Vendu
```

### Documents réglementaires marocains et alertes

| Document | Champ | Alerte (60j) |
|----------|-------|-------------|
| Carte grise / Visite technique | `carte_grise_expiration` | `visite_technique_expiring` |
| Assurance | `assurance_expiration` | `assurance_expiring` |
| Vignette fiscale | `vignette_expiration` | `vignette_expiring` |

### Maintenance

- **Intervalle entretien** — En km (défaut : 10 000 km)
- **Km prochain entretien** = Km dernier entretien + Intervalle
- **Alerte km** (`entretien_km_alerte`) — True si km actuel >= km prochain - 500
- **Historique entretiens** — Types : Vidange, Révision, Pneus, Freins, Courroie, Carrosserie, Électrique, Autre
- Coût par entretien (MAD)
- Prochain entretien recommandé (date + km)
- Mise à jour auto du véhicule à la création d'un entretien

### Entrepôt mobile

- Chaque véhicule peut être lié à un `stock.warehouse` Odoo
- Bouton "Créer entrepôt mobile" — génère un entrepôt avec code court unique
- Permet la gestion du stock terrain embarqué dans le véhicule

---

## 10. Module telecom_project — Projets & Chantiers

### Modèles

| Modèle | Description |
|--------|-------------|
| `project.project` (hérité) | Extension projet Odoo |
| `telecom.lot` | Lot au sein d'un projet |
| `telecom.project.site` | Rattachement site ↔ projet |
| `telecom.pv.reception` | PV de réception (partiel/définitif) |

### Structure hiérarchique

```
Projet (project.project)
  └── Lot (telecom.lot)
       └── Site de projet (telecom.project.site)
            └── Tâche (project.task)
```

### Lots

- Code unique par projet (contrainte SQL)
- Description, chef de lot, dates début/fin
- **Taux d'avancement** calculé automatiquement : sites livrés / sites total
- **Workflow** : Planifié → En cours → Livré → Suspendu

### Sites de projet

- Rattachement d'un `telecom.site` à un `project.project`
- Un site ne peut être rattaché qu'une fois par projet (contrainte SQL unique)
- **Workflow** : Planifié → En cours → Installé → Testé → Livré → Suspendu

### PV de réception

- **Types** : Partielle / Définitive
- **Signatures** :
  - Signature entreprise (`signature_entreprise`) — Binary
  - Signature client (`signature_client`) — Binary
- **Workflow** : Brouillon → Signé → Approuvé
- Règles :
  - Signature impossible sans les deux signatures
  - Approbation impossible depuis Brouillon
  - PV définitif approuvé → passage automatique du site à l'état "Livré"
  - PV partiel approuvé → pas de changement d'état site

---

## 11. Module telecom_ao — Appels d'Offres

### Modèles

| Modèle | Description |
|--------|-------------|
| `telecom.ao` | Appel d'offres |
| `telecom.bpu.ligne` | Ligne de Bordereau de Prix Unitaires |

### Pipeline AO (7 états)

```
Détecté → En étude → Soumis → Gagné / Perdu → Transformé en projet → Abandonné
```

Règles :
- **Soumission** : requiert une date limite de remise
- **Transformation en projet** : uniquement depuis l'état Gagné
- **Abandon** : possible depuis tout état actif
- Transition directe Détecté → Soumis refusée

### Cautions bancaires automatiques

| Caution | Taux | Base |
|---------|------|------|
| Provisoire | 1,5% | Montant soumissionné |
| Définitive | 3,0% | Montant soumissionné |

- Recalculées automatiquement à la modification du montant
- Cohérence : définitive = 2 × provisoire

### BPU — Bordereau de Prix Unitaires

- Lignes avec : Désignation, Unité, Quantité, Prix unitaire
- **Total BPU** calculé automatiquement (somme des lignes)
- Compteur de lignes BPU

### Délai de remise

- Date limite de remise
- **Jours avant remise** calculé automatiquement
- Vue Kanban pipeline avec indicateurs visuels

---

## 12. Module telecom_contract — Contrats

### Modèles

| Modèle | Description |
|--------|-------------|
| `telecom.contract` | Contrat opérateur / maintenance |
| `telecom.caution.bancaire` | Caution bancaire liée à un contrat |

### Types de contrats

| Type | Code | Description |
|------|------|-------------|
| Contrat-cadre opérateur | `cadre_operateur` | Conditions tarifaires négociées |
| Maintenance | `maintenance` | Maintenance préventive/corrective |
| Déploiement | `deploiement` | Marché de travaux |
| Sous-traitance | `sous_traitance` | Contrat avec sous-traitant |
| Bail site | `bail_site` | Location terrain/toiture |

### Cycle de vie contrat (5 états)

```
Brouillon → Actif → Expiré → Résilié → Suspendu
```

### SLA contractuels

- **Délai intervention** (`sla_delai_intervention_h`) — En heures
- **Délai réparation** (`sla_delai_reparation_h`) — En heures
- **Disponibilité contractuelle** — Pourcentage (%)
- **Pénalités SLA** — Description textuelle

### Alertes

- **Alerte expiration** (`expiry_warning`) — Contrat actif expirant dans < 90 jours
- **Jours avant expiration** — Calculé automatiquement

### Cautions bancaires

- Types : Provisoire / Définitive
- Banque émettrice, référence bancaire
- Montant, date émission, date expiration
- État : Active / Expirée / Libérée
- Alerte si expiration dans < 60 jours

---

## 13. Module telecom_finance_ma — Finance CCAG

### Modèles

| Modèle | Description |
|--------|-------------|
| `telecom.situation` | Situation de travaux (facturation progressive) |
| `telecom.situation.line` | Détail par lot/site |
| `telecom.decompte` | Décompte provisoire/définitif (CCAG) |
| `telecom.avance.demarrage` | Avance de démarrage |
| `telecom.avance.remboursement` | Remboursement partiel d'avance |
| `account.move` (hérité) | Extension facture avec lien décompte/situation |

### Situation de travaux

Facturation progressive sur avancement d'un marché public.

**Formules** :
```
Montant cumulé HT = Montant marché × Avancement cumulé (%)
Montant situation HT = Cumulé - Situations précédentes
TVA = Montant situation × Taux TVA (%)
TTC = Montant situation + TVA
Retenue de garantie = Montant situation × Taux RG (%)
Net à payer = TTC - RG - Remboursement avance
```

**Workflow** : Brouillon → Soumis → Approuvé → Facturé → Payé

### Décompte de travaux (CCAG)

Document de règlement financier conforme au CCAG Travaux marocain.

**Types** :
- **Provisoire** (DC/YYYY/NNN) — Après chaque phase significative
- **Définitif** (DDF/YYYY/NNN) — Règlement final avec libération RG

**Sections du décompte** :

| Section | Contenu |
|---------|---------|
| I — Cumul travaux | Travaux HT + Supplémentaires + Révisions de prix |
| II — Déductions | Retenue de garantie + Avances + Situations antérieures |
| III — TVA | Base TVA × Taux |
| IV — Net | Net à régler - RAS 10% |
| V — Libération RG | Uniquement sur décompte définitif |

**Formules** :
```
Total HT cumulé = Travaux HT + Supplémentaires + Révisions prix
Retenue de garantie = Total HT × Taux RG (défaut 10%)
Base TVA = Total HT - RG - Avance période - Situations antérieures
TVA = Base TVA × Taux TVA (défaut 20%)
Net à régler = Base TVA + TVA
RAS = Base TVA × 10%
Net après RAS = Net à régler - RAS
```

**Workflow** : Brouillon → Soumis → Approuvé → Phase contradictoire → Signé → Payé

**Délai de paiement (Loi 69-21)** :
- Date limite = Date soumission + 60 jours
- Alerte `delai_depasse` si non payé après 60 jours

### Avance de démarrage

Réglementation marocaine (CCAG Travaux) :
- **Taux standard** : 10% du montant marché
- **Taux majoré** : jusqu'à 15% selon le CCAP
- **Montant théorique** calculé automatiquement

**Workflow** : En attente → Versée → En cours de remboursement → Entièrement remboursée

**Remboursements** :
- Modèle `telecom.avance.remboursement`
- Remboursement progressif sur chaque situation/décompte
- Solde restant calculé automatiquement
- Clôture impossible si solde > 0

---

## 14. Module telecom_reporting — Reporting & Dashboards

### Vues d'analyse SQL (performantes)

| Vue | Modèle | Données |
|-----|--------|---------|
| Analyse interventions | `report.telecom.intervention.analysis` | Type, durée, SLA, technicien, site |
| Analyse sites | `report.telecom.site.analysis` | Type, état, wilaya, interventions |
| Analyse finance | `report.telecom.finance.analysis` | Situations, décomptes, montants |

### Dashboard Direction

3 vues pivot/graph :
- **CA et Finance** — Chiffre d'affaires depuis situations et décomptes
- **Sites déployés** — Répartition par état et type
- **Interventions du mois** — Volume et types d'interventions en cours

### Dashboard RH

3 actions dédiées :
- **Techniciens sur site aujourd'hui** — Pointages du jour
- **Habilitations expirant** — État `expiring_soon` ou `expired`
- **EPI à renouveler** — Dotations expirant ou expirées

### KPIs Commercial

- Comptage AO par état
- Taux de succès : gagné / (gagné + perdu)
- Contrats actifs par type
- Montant total sous contrat actif
- Alertes contrats expirant < 90 jours

### KPIs Opérations

- Nombre d'interventions par état
- SLA dépassé (agrégé)
- Durée réelle exposée
- Nombre d'interventions par site
- Répartition par type de site et wilaya

### Export format opérateur

- Wizard `telecom.export.operateur.wizard`
- Filtre par date et opérateur
- Génère CSV : Code site, Nom site, Date, Type, Durée, Statut, Technicien, Opérateur
- Format compatible IAM / Orange / Inwi

### Bilan social CNSS annuel

- Rapport QWeb PDF
- Par employé : nom, N° CNSS, mois travaillés, salaire brut total, CNSS salarié/patronal, AMO salarié/patronal
- Totaux et sous-totaux
- Groupé par année

---

## 15. Module telecom_test_admin — Administration des tests

### Interface Odoo pour les tests BDD

Menu **"Tests BDD"** accessible depuis l'ERP :

| Vue | Contenu |
|-----|---------|
| Dashboard | Kanban des 25 fichiers .feature groupés par module |
| Fichiers .feature | Liste avec contenu, scénarios, statut pass/fail |
| Scénarios | 261 scénarios individuels avec dernier résultat |
| Exécutions | Historique des lancements + bouton "Lancer les tests" |

### Fonctionnalités

- **Synchronisation auto** — Bouton pour recharger les .feature depuis le disque
- **Parsing Gherkin** — Extraction automatique des scénarios depuis les fichiers
- **Lancement pytest** — Exécution directe depuis l'interface Odoo
- **Capture résultats** — Sortie pytest stockée, compteurs pass/fail
- **Couleurs** — Vert (tous passent), Orange (partiels), Rouge (tous échouent)

---

## 16. Conformité légale marocaine

### Audit automatisé — 62/62 contrôles conformes (100%)

| Domaine | Référence légale | Contrôles | Statut |
|---------|-----------------|-----------|--------|
| TVA | CGI Art. 89-103 | 5 taux vente + 3 achat | 8/8 |
| RAS | CGI Art. 15 | Taxe 10% + marqueur | 2/2 |
| CNSS | Loi 1-72-184 | Taux, plafond 6000, calculs | 5/5 |
| AMO | Loi 65-00 | Taux, sans plafond, calculs | 2/2 |
| IR | LF 2024, Art. 73 | 6 tranches + frais pro | 7/7 |
| Ancienneté | Code Travail Art. 350-353 | 5 paliers | 5/5 |
| Factures | CGI Art. 145 | ICE, IF, RC, Patente, forme juridique | 8/8 |
| CCAG | Décret 2-12-349 | Cautions, RG, délai 60j, avances, PV | 12/12 |
| Sécurité travail | Code Travail Art. 281-303 | Habilitations, EPI, alertes | 7/7 |
| ANRT | Loi 24-96 | Agréments, GPS, 12 régions | 4/4 |
| Devise | Bank Al-Maghrib | MAD active | 1/1 |
| **TOTAL** | | | **62/62** |

Le script d'audit est exécutable via :
```bash
ssh root@65.108.146.17 "cd /opt/telecomerp && docker compose exec -T odoo python3 /mnt/extra-addons/audit_maroc.py"
```

---

## 17. Tests BDD — Couverture complète

### Architecture BDD

```
Fichier .feature (Gherkin FR)     → Propriété du MÉTIER
  ↕
Step definitions (Python)         → Propriété des DÉVELOPPEURS
  ↕
Modèles Odoo (Python + XML)      → Code source
```

### Statistiques

| Module | Fichiers | Scénarios |
|--------|----------|-----------|
| telecom_site | 3 | 36 |
| telecom_intervention | 2 | 37 |
| telecom_hr_ma | 5 | 38 |
| telecom_finance_ma | 3 | 29 |
| telecom_ao | 2 | 21 |
| telecom_contract | 1 | 21 |
| telecom_project | 2 | 22 |
| telecom_equipment | 2 | 13 |
| telecom_fleet | 1 | 8 |
| telecom_base | 1 | 9 |
| telecom_localization_ma | 1 | 10 |
| telecom_reporting | 2 | 17 |
| **Total** | **25** | **359** |

### Résultat : 359/359 passent (100%)

### Stack technique tests

| Outil | Usage |
|-------|-------|
| pytest | Runner de tests |
| pytest-bdd 8.x | Parsing Gherkin + liaison steps |
| freezegun | Simulation de dates (SLA, bail, délais) |
| pytest-cov | Couverture de code |

### Lancer les tests

```bash
# Tous les modules
bash bin/pre-deploy-tests.sh

# Un module spécifique
bash bin/pre-deploy-tests.sh --module site

# Avec rapport HTML
bash bin/pre-deploy-tests.sh --report
```

---

## 18. Corrections et améliorations Odoo 17

### Compatibilité Odoo 17 — Corrections apportées

| Problème | Correction | Fichiers |
|----------|-----------|----------|
| `attrs=` supprimé en Odoo 17 | Remplacé par `invisible="..."`, `readonly="..."`, `required="..."` | 30+ fichiers XML |
| `<list>` non reconnu | Remplacé par `<tree>` dans toutes les vues | 21 fichiers XML |
| `# language: fr` + mots-clés anglais | Mots-clés Gherkin traduits (`Fonctionnalité:`, `Scénario:`, `Contexte:`, `Exemples:`) | 25 fichiers .feature |
| `kanban-card` template | Remplacé par `kanban-box` (requis par Odoo 17 OWL) | telecom_site |
| `@api.depends('id')` interdit | Retiré de `_compute_code` | telecom_equipment |
| `hr_leave` module inexistant | Remplacé par `hr_holidays` | telecom_hr_ma manifest |
| `account.tax_group_taxes` xmlid inexistant | Créé des groupes de taxe custom (TVA Maroc, RAS Maroc) | telecom_localization_ma |
| xpath `general_information` inexistant | Corrigé en `general_info` | res_company_views.xml |
| `base.paperformat_a4` inexistant | Remplacé par `base.paperformat_euro` | intervention report |
| Import `custom_addons.*` | Remplacé par `odoo.addons.*` | test_bdd_hr.py |
| `navigator.clipboard` crash mobile HTTP | Polyfill JS ajouté | clipboard_fix.js |
| Conftest Odoo bootstrap | `pytest_configure` hook + aliasing `sys.modules` | conftest.py |

### Corrections de données et champs

| Problème | Correction |
|----------|-----------|
| `partner_id` sur `telecom.contract` | Renommé `partenaire_id` dans les step definitions |
| `date_start` sur `hr.employee` | Remplacé par `first_contract_date` via `hr.contract` |
| `date_controle_technique` sur véhicule | Remplacé par `carte_grise_expiration` |
| `description` sur intervention | Remplacé par `description_travaux` |
| `technicien_id` (M2O) | Remplacé par `technician_ids` (M2M) |
| UniqueViolation habilitation/EPI | Pattern search-or-create dans les steps |
| `db_password` incorrect | Corrigé dans `odoo.conf` |

---

## 19. Infrastructure & Déploiement

### Serveur de production

| Paramètre | Valeur |
|-----------|--------|
| Hébergeur | Hetzner Cloud |
| Plan | CPX22 |
| CPU | 3 vCPU (AMD EPYC) |
| RAM | 4 GB + 2 GB swap |
| Disque | 80 GB SSD local |
| OS | Ubuntu 24.04 LTS |
| Localisation | Helsinki (eu-central) |
| IPv4 | 65.108.146.17 |
| Domaine | erp.kleanse.fr |
| SSL | Let's Encrypt (auto-renew) |

### Architecture Docker

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────→│    Odoo     │────→│  PostgreSQL  │
│  (port 80/  │     │  (port 8069)│     │  (port 5432) │
│   443 SSL)  │     │  3 workers  │     │  15-alpine   │
└─────────────┘     └─────────────┘     └─────────────┘
       ↑                   ↑                    ↑
   Reverse proxy      custom_addons        pgdata volume
   + SSL termination   /mnt/extra-addons
```

### Fichiers de déploiement

| Fichier | Usage |
|---------|-------|
| `deploy/docker-compose.prod.yml` | Composition de production |
| `deploy/config/odoo.conf` | Configuration Odoo production |
| `deploy/nginx/default.conf` | Configuration Nginx + SSL |
| `deploy/setup-server.sh` | Script setup serveur initial |
| `deploy/deploy.sh` | Script déploiement automatisé |
| `deploy/demo_data.py` | Chargement données de démonstration |
| `deploy/audit_maroc.py` | Audit conformité loi marocaine |
| `deploy/audit_fonctionnel.py` | Audit scope fonctionnel |

### Déployer une mise à jour

```bash
# Depuis la machine de dev
bash deploy/deploy.sh
```

---

## 20. Données de démonstration

### Contenu chargé

| Donnée | Quantité | Détail |
|--------|----------|--------|
| Opérateurs | 4 | Maroc Telecom, Orange, Inwi, ONEE |
| Sous-traitants | 5 | Avec spécialités et certifications |
| Bailleurs | 4 | Propriétaires fonciers |
| Fournisseurs | 5 | Huawei, Nokia, Ericsson, Corning, CommScope |
| Certifications | 6 | ANRT, ONEE, ISO 9001/14001/45001 |
| Spécialités | 8 | Fibre, RF, courant fort/faible, génie civil... |
| Sites télécom | 25 | 12 régions du Maroc, GPS réel |
| Habilitations types | 8 | Hauteur, électrique, CACES, SST... |
| EPI types | 8 | Casque, harnais, chaussures, gants... |
| Employés techniciens | 20 | Avec contrats, habilitations, EPI |
| Équipements | 20 | Antennes, eNodeB, OLT, shelters, batteries |
| Outillages | 7 | OTDR, soudeuses, analyseurs |
| Véhicules | 8 | Toyota, Renault, Ford, Mitsubishi, Dacia |
| Entretiens véhicules | 8 | Historique vidanges |
| Projets | 4 | FTTH Casa, 4G Rabat, Maintenance Nord, 4G Sud |
| Lots | 8 | 2 lots par projet |
| AO | 6 | Pipeline complet (détecté → gagné) |
| Lignes BPU | 10 | Pour les AO gagnés |
| Contrats | 5 | Cadre, maintenance, déploiement, sous-traitance |
| Cautions bancaires | 4 | Provisoires et définitives |
| Interventions | 15 | Tous stades du workflow |
| Pointages | ~130 | 20 jours ouvrés × 8 techniciens |
| Bulletins de paie | 10 | Mars 2026 |
| Situations travaux | 3 | Avancement progressif |
| Décomptes | 1 | Provisoire avec calculs CCAG |

---

## 21. Guide utilisateur

### Accès

- **URL** : https://erp.kleanse.fr
- **Login** : admin / (mot de passe à définir)
- **Langues** : Français (défaut), English, العربية (RTL)

### Changer de langue

Profil utilisateur (coin supérieur droit) → Préférences → Langue

### Menus principaux

| Menu | Contenu |
|------|---------|
| Sites & Infrastructure | Gestion des sites télécom |
| Interventions | Bons d'intervention terrain |
| RH & Terrain | Employés, paie, habilitations, EPI, pointage |
| Projets | Projets, lots, PV réception |
| Commercial | Pipeline AO, BPU |
| Contrats | Contrats opérateurs, SLA, cautions |
| Finance | Situations travaux, décomptes CCAG, avances |
| Reporting | Dashboards, KPIs, exports |
| Tests BDD | Administration des tests (admin uniquement) |
| Configuration | Paramètres, types, séquences |

### Workflow type — Nouveau marché

```
1. Détecter un AO (menu Commercial → Appels d'offres)
2. Constituer le dossier + BPU
3. Soumettre → Gagné → Transformer en projet
4. Créer le contrat avec SLA et cautions
5. Créer les lots et rattacher les sites
6. Planifier les interventions et affecter les techniciens
7. Réaliser les interventions (terrain)
8. Créer les PV de réception (partielle puis définitive)
9. Émettre les situations de travaux (facturation progressive)
10. Émettre le décompte définitif (libération retenue de garantie)
```

### Workflow type — Intervention corrective

```
1. Créer un BI (Bons d'intervention → Nouveau)
2. Sélectionner le site, type = Corrective
3. Affecter les techniciens
4. Planifier (date + durée estimée)
5. Démarrer sur le terrain (enregistre heure début)
6. Terminer (enregistre heure fin + rapport)
7. Ajouter photos et matériels consommés
8. Signer (technicien + client)
9. Validation chef de chantier
10. Facturation si hors contrat forfait
```

---

*Document généré le 10 avril 2026 — TelecomERP v17.0.1.0.0*
