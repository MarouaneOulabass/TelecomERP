# -*- coding: utf-8 -*-
{
    'name': 'TelecomERP — Projets Chantier',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Gestion des projets de déploiement télécom : lots, sites, PV de réception',
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': [
        'telecom_base',
        'telecom_site',
        'telecom_hr_ma',
        'project',
        'mail',
    ],
    'data': [
        # Security — load first
        'security/telecom_project_rules.xml',
        'security/ir.model.access.csv',
        # Data
        'data/telecom_project_data.xml',
        # Views
        'views/project_project_views.xml',
        'views/telecom_lot_views.xml',
        'views/telecom_project_site_views.xml',
        'views/telecom_pv_reception_views.xml',
        'views/menu_views.xml',
        # Reports
        'report/telecom_pv_report.xml',
        'report/telecom_pv_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 15,
}
