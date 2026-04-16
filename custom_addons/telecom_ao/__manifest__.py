# -*- coding: utf-8 -*-
{
    'name': "TelecomERP — Appels d'Offres & BPU",
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Gestion des appels d\'offres, pipeline commercial et BPU télécom',
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': [
        'telecom_base',
        'telecom_site',
        'mail',
    ],
    'data': [
        'security/telecom_ao_rules.xml',
        'security/ir.model.access.csv',
        'data/telecom_ao_sequence.xml',
        'views/telecom_bpu_views.xml',
        'views/telecom_ao_views.xml',
        'views/menu_views.xml',
        'report/telecom_ao_report.xml',
        'report/telecom_ao_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 20,
}
