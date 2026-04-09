# TelecomERP

Solution ERP verticale Odoo 17 pour entreprises marocaines de déploiement et maintenance d'infrastructures télécom.

## Démarrage rapide

```bash
# 1. Copier et adapter les variables d'environnement
cp .env .env.local    # modifier POSTGRES_PASSWORD

# 2. Lancer l'environnement
docker compose up -d

# 3. Ouvrir Odoo
# http://localhost:8069
# Créer une base de données, installer les modules dans l'ordre ci-dessous
```

## Ordre d'installation des modules

**Phase 1 — Fondations (installer en premier)**
1. `telecom_base`
2. `telecom_localization_ma`
3. `telecom_site`
4. `telecom_intervention`
5. `telecom_hr_ma`

**Phase 2 — Projet, Commercial, Logistique**
6. `telecom_project`
7. `telecom_ao`
8. `telecom_contract`
9. `telecom_equipment`
10. `telecom_fleet`

**Phase 3 — Finance & Reporting**
11. `telecom_finance_ma`
12. `telecom_reporting`

## Commandes utiles

```bash
# Mettre à jour un module après modification
docker compose exec odoo odoo -u telecom_base --stop-after-init

# Mettre à jour tous les modules custom
docker compose exec odoo odoo -u telecom_base,telecom_localization_ma,telecom_site,telecom_intervention,telecom_hr_ma,telecom_project,telecom_ao,telecom_contract,telecom_equipment,telecom_fleet,telecom_finance_ma,telecom_reporting --stop-after-init

# Logs en direct
docker compose logs -f odoo

# Accès shell Odoo
docker compose exec odoo odoo shell
```

## Architecture modules

```
custom_addons/
├── telecom_base/              # Fondations, groupes sécurité, partenaires marocains
├── telecom_localization_ma/   # TVA, CGNC, RAS, mentions légales, LCN
├── telecom_site/              # Sites physiques, GPS, bailleur, technologies
├── telecom_intervention/      # Bons d'intervention terrain, PDF, signature
├── telecom_hr_ma/             # Paie CNSS/AMO/IR, habilitations, EPI, pointage
├── telecom_project/           # Projets chantier, lots, sites, PV réception
├── telecom_ao/                # Appels d'offres, BPU, pipeline commercial
├── telecom_contract/          # Contrats opérateurs, SLA, cautions bancaires
├── telecom_equipment/         # Équipements par site, outillages, historique
├── telecom_fleet/             # Parc véhicules terrain, stocks mobiles
├── telecom_finance_ma/        # Situations travaux, décomptes CCAG, avances
└── telecom_reporting/         # Dashboards KPI, analyses, bilan social CNSS
```

## Stack technique

| Composant | Version |
|---|---|
| Odoo | 17.0 Community |
| Python | 3.11 |
| PostgreSQL | 15 |
| Docker Compose | v2 |

## Groupes de sécurité

| Groupe | Périmètre |
|---|---|
| Technicien Terrain | Lecture + saisie interventions |
| Chef de Chantier | Validation interventions, planning |
| Chargé d'Affaires | Projets, commercial, facturation |
| Responsable | Accès complet sauf config système |
| Administrateur TelecomERP | Configuration complète |

## Licence

Propriétaire — TelecomERP. Tous droits réservés.
Basé sur Odoo 17 Community (LGPL-3.0).
