# -*- coding: utf-8 -*-
{
    'name': 'TelecomERP — Couts Financiers',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Integration des couts financiers dans la marge projet',
    'description': """
TelecomERP — Couts Financiers
===============================
Suivi des couts financiers rattaches aux projets :

- Credits bancaires, leasing, cautions provisoires/definitives
- Avances clients, escompte, frais financiers divers
- Calcul automatique des interets (montant x taux x duree)
- Creation automatique d'une ecriture de cout (telecom.cost.entry)
- Integration dans le cockpit de rentabilite projet
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': [
        'telecom_base',
        'telecom_cost',
        'telecom_project',
        'telecom_contract',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/telecom_financing_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 17,
}
