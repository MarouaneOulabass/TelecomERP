{
    'name': 'TelecomERP — Cockpit de Rentabilité',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Dashboard temps réel de la marge projet par lot',
    'description': """
Promesse principale de TelecomERP.

Affiche pour chaque projet et chaque lot :
- Budget prévisionnel vs coûts engagés vs coûts payés
- Marge en % et en valeur absolue
- Projection de marge en fin de projet
- Alertes quand la marge descend sous un seuil

Alimenté par telecom_cost et telecom_finance_ma.
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': ['telecom_base', 'telecom_project', 'telecom_cost'],
    'data': [
        'security/ir.model.access.csv',
        'views/telecom_margin_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 16,
}
