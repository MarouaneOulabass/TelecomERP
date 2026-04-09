# -*- coding: utf-8 -*-
{
    'name': 'TelecomERP — Interventions Terrain',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Gestion des Bons d\'Intervention (BI) pour les interventions terrain télécom',
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': [
        'telecom_base',
        'telecom_site',
        'hr',
        'stock',
        'sale',
        'mail',
    ],
    'data': [
        # Security — load first
        'security/telecom_intervention_rules.xml',
        'security/ir.model.access.csv',
        # Sequences / reference data
        'data/telecom_intervention_sequence.xml',
        # Views
        'views/telecom_intervention_views.xml',
        'views/menu_views.xml',
        # Reports
        'report/telecom_intervention_report.xml',
        'report/telecom_intervention_report_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 10,
}
