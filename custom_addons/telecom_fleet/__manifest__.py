# -*- coding: utf-8 -*-
{
    'name': 'TelecomERP — Flotte Véhicules',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Gestion flotte terrain : véhicules, entretiens, stock mobile, alertes documents',
    'description': """
TelecomERP — Flotte Véhicules
==============================
Gestion complète de la flotte de véhicules terrain pour entreprises télécom marocaines :

- Suivi des véhicules (immatriculation, documents légaux, assurance, vignette)
- Affectation aux techniciens terrain
- Historique des entretiens et alertes kilométriques
- Entrepôt mobile Odoo lié à chaque véhicule (stock mobile terrain)
- Alertes automatiques d'expiration documents (60 jours)
- Fiche véhicule PDF (QWeb)

Dépend de telecom_base (groupes sécurité) et telecom_hr_ma (techniciens terrain).
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': [
        'telecom_base',
        'telecom_hr_ma',
        'hr',
        'stock',
        'mail',
    ],
    'data': [
        # Security — always first
        'security/telecom_fleet_rules.xml',
        'security/ir.model.access.csv',
        # Data
        'data/telecom_fleet_data.xml',
        # Views
        'views/telecom_vehicle_views.xml',
        'views/telecom_vehicle_entretien_views.xml',
        'views/menu_views.xml',
        # Reports
        'report/telecom_vehicle_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 12,
}
