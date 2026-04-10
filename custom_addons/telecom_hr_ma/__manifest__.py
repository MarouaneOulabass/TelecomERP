# -*- coding: utf-8 -*-
{
    'name': 'TelecomERP — RH & Terrain Maroc',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'RH terrain marocain : habilitations, EPI, pointage chantier, paie CNSS/AMO/IR',
    'description': """
TelecomERP — RH & Terrain Maroc
================================
Extension RH pour entreprises télécom marocaines :

- Profil technicien terrain : spécialités, habilitations sécurité, dotations EPI
- Pointage chantier quotidien (avec calcul heures supplémentaires)
- Moteur de paie marocain (CNSS 4.48%, AMO 2.26%, CIMR, barème IR 2024)
- Bulletin de paie PDF (QWeb)

Dépend de telecom_base (groupes sécurité, telecom.specialite)
et telecom_site (telecom.site).
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': [
        'telecom_base',
        'telecom_site',
        'hr',
        'hr_contract',
        'hr_holidays',
        'mail',
    ],
    'data': [
        # Security — always first
        'security/telecom_hr_rules.xml',
        'security/ir.model.access.csv',
        # Data
        'data/telecom_paie_sequence.xml',
        'data/telecom_hr_data.xml',
        # Reports — must load before views that reference report actions
        'report/telecom_paie_report.xml',
        'report/telecom_paie_template.xml',
        # Views — action definitions must load before hr_employee_views
        'views/telecom_habilitation_views.xml',
        'views/telecom_epi_views.xml',
        'views/telecom_pointage_views.xml',
        'views/telecom_paie_views.xml',
        'views/hr_employee_views.xml',
        # Wizard — before menu
        'wizard/damancom_export_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 5,
}
