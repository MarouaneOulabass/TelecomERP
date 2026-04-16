{
    'name': 'TelecomERP — Facturation & Relances',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Facturation client télécom, suivi paiements, relances automatisées',
    'description': """
        Module de facturation pour TelecomERP :

        * Extension des factures Odoo avec champs télécom (projet, site, lot, situation)
        * Suivi des délais de paiement avec alertes loi 69-21 (> 60 jours)
        * Gestion des relances clients (email, courrier, mise en demeure)
        * Types de factures télécom : standard, situation, décompte, avoir
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': ['telecom_base', 'telecom_localization_ma', 'account', 'mail', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/telecom_relance_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 15,
}
