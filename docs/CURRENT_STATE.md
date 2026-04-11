# CURRENT_STATE.md — État actuel du produit

> **Date** : Avril 2026
> **Version** : 17.0.1.0.0
> **Environnement** : https://erp.kleanse.fr

---

## Résumé exécutif

TelecomERP est en **MVP déployé** sur un serveur de production. 13 modules sont installés et fonctionnels. Le produit couvre les opérations terrain, la RH marocaine, la finance CCAG, et le commercial. **Le cockpit de rentabilité projet (promesse principale du produit) n'est pas encore implémenté.**

---

## Ce qui est codé et fonctionne

### Modules en production (13)

| Module | Vague | Statut | Tests |
|--------|-------|--------|-------|
| `telecom_base` | MVP | En prod | 17 scénarios |
| `telecom_localization_ma` | MVP | En prod | 10 scénarios |
| `telecom_site` | MVP | En prod | 36 scénarios |
| `telecom_intervention` | MVP | En prod | 37 scénarios |
| `telecom_hr_ma` | MVP | En prod | 38 scénarios |
| `telecom_equipment` | V1.5 | En prod | 13 scénarios |
| `telecom_fleet` | V1.5 | En prod | 8 scénarios |
| `telecom_project` | MVP | En prod | 22 scénarios |
| `telecom_ao` | V1.5 | En prod | 21 scénarios |
| `telecom_contract` | V1.5 | En prod | 21 scénarios |
| `telecom_finance_ma` | MVP | En prod | 29 scénarios |
| `telecom_reporting` | V2 | En prod | 17 scénarios |
| `telecom_test_admin` | Infra | En prod | — |

**Total : 367 tests BDD, tous passent.**

### Audits passés

- Conformité loi marocaine : **62/62** (TVA, CNSS, AMO, IR, CCAG, ANRT)
- Scope fonctionnel : **55/55** fonctionnalités implémentées
- Smoke tests vues/actions/menus : **tous passent**

### Infrastructure

- Hetzner CPX22 (3 vCPU, 4GB RAM, 80GB SSD)
- Docker Compose (Odoo 17 + PostgreSQL 15 + Nginx)
- HTTPS Let's Encrypt (auto-renew)
- Backups quotidiens PostgreSQL
- Fail2ban + UFW
- 3 langues (FR, EN, AR/RTL)

---

## Ce qui manque pour la V1 complète

### Priorité 1 — Cockpit de rentabilité (promesse principale)

| Capability | Description | Statut |
|-----------|-------------|--------|
| `telecom_cost` | Rattachement des coûts aux projets/lots | **À développer** |
| `telecom_margin` | Dashboard de marge projet temps réel | **À développer** |

C'est le **coeur de la proposition de valeur**. Sans ça, le produit est un ERP opérationnel classique, pas le "cockpit de pilotage" promis dans la vision.

### Priorité 2 — Multi-tenant SaaS

| Capability | Description | Statut |
|-----------|-------------|--------|
| `telecom_tenant` | Profil tenant YAML + provisioning auto | **À développer** |
| Isolation multi-tenant | Règles d'accès inter-tenants | **À développer** |

Nécessaire pour passer de 1 client à 50.

### Priorité 3 — Enrichissements V1.5

| Capability | Description | Statut |
|-----------|-------------|--------|
| `telecom_carburant` | Suivi consommation carburant par véhicule/projet | **À développer** |
| `telecom_financing` | Coût réel de financement dans la marge | **À développer** |
| Agent IA onboarding | Configuration assistée par conversation | **À développer** |

---

## Mapping CAPABILITY_CATALOG → Code actuel

| Capability (docs) | Module (code) | Statut |
|-------------------|---------------|--------|
| Core technique | `telecom_base` | Fait |
| Profil tenant | — | À faire |
| Localisation Maroc | `telecom_localization_ma` | Fait |
| Sécurité et accès | `telecom_base` (security/) | Fait |
| Projets et lots | `telecom_project` | Fait |
| **Rattachement des coûts** | — | **À faire** |
| **Cockpit de rentabilité** | — | **À faire** |
| Situations de travaux | `telecom_finance_ma` | Fait |
| Sites physiques | `telecom_site` | Fait |
| Bons d'intervention | `telecom_intervention` | Fait |
| Personnel et paie | `telecom_hr_ma` | Fait |
| Parc véhicules | `telecom_fleet` | Fait |
| **Suivi carburant** | — | **À faire** |
| **Coût financement** | — | **À faire** |
| Facturation | Odoo `account` natif | Fait (natif) |
| Appels d'offres | `telecom_ao` | Fait |
| Contrats et SLA | `telecom_contract` | Fait |
| Pointage terrain | `telecom_hr_ma` (pointage) | Fait |
| Photos terrain | `telecom_intervention` (photos) | Fait |
| Équipements | `telecom_equipment` | Fait |
| Stocks | Odoo `stock` natif | Fait (natif) |
| EPI et habilitations | `telecom_hr_ma` | Fait |
| Cautions bancaires | `telecom_contract` (cautions) | Fait |
| Comptabilité MA | `telecom_localization_ma` (CGNC) | Fait |
| Reporting | `telecom_reporting` | Fait |

**Score : 21/26 capabilities implémentées (81%)**

---

## Prochaine étape recommandée

**Développer `telecom_cost` + `telecom_margin`** — c'est ce qui transforme l'outil opérationnel en cockpit de rentabilité, et c'est la promesse #1 du produit.

---

*Document mis à jour : avril 2026*
