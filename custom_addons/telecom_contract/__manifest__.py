# -*- coding: utf-8 -*-
{
    'name': 'TelecomERP — Contrats & SLA',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Gestion des contrats opérateurs, SLA et cautions bancaires',
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': [
        'telecom_base',
        'telecom_site',
        'telecom_ao',
        'mail',
    ],
    'data': [
        'security/telecom_contract_rules.xml',
        'security/ir.model.access.csv',
        'data/telecom_contract_sequence.xml',
        'views/telecom_caution_views.xml',
        'views/telecom_contract_views.xml',
        'views/menu_views.xml',
        'report/telecom_contract_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 25,
}
