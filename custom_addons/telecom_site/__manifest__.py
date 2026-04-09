# -*- coding: utf-8 -*-
{
    'name': 'TelecomERP — Sites',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Gestion des sites télécom : pylônes, rooftops, shelters, FTTH, etc.',
    'description': """
TelecomERP — Sites
==================
Module central de gestion des sites physiques télécom pour les opérateurs
et entreprises de déploiement marocaines.

Fonctionnalités :
- Référentiel complet des sites (pylônes, rooftops, cabinets FTTH, shelters...)
- Suivi de l'état du cycle de vie (prospection → livré → maintenance)
- Gestion des baux et bailleurs de sites
- Localisation GPS et informations d'accès terrain
- Technologies déployées (2G, 3G, 4G, 5G, FTTH, MW, VSAT...)
- Gestion documentaire par site (plans, PV, autorisations...)
- Fiche site PDF (QWeb)
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': [
        'telecom_base',
        'mail',
    ],
    'data': [
        # Security — always first
        'security/telecom_site_security.xml',
        'security/ir.model.access.csv',
        # Initial data
        'data/telecom_site_data.xml',
        # Views
        'views/telecom_site_views.xml',
        'views/menu_views.xml',
        # Reports
        'report/telecom_site_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 2,
}
