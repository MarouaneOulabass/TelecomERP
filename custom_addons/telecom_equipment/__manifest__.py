# -*- coding: utf-8 -*-
{
    'name': 'TelecomERP — Équipements & Outillages',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Gestion du parc équipements télécom et de l\'outillage terrain',
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': [
        'telecom_base',
        'telecom_site',
        'hr',
        'stock',
        'mail',
    ],
    'data': [
        # Security — must come first
        'security/telecom_equipment_rules.xml',
        'security/ir.model.access.csv',
        # Initial data
        'data/telecom_equipment_data.xml',
        # Views
        'views/telecom_equipment_views.xml',
        'views/telecom_equipment_category_views.xml',
        'views/telecom_outillage_views.xml',
        'views/menu_views.xml',
        # Reports
        'report/telecom_equipment_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 4,
}
