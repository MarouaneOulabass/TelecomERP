{
    'name': 'TelecomERP — Localisation Maroc',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Localisation comptable marocaine : CGNC, TVA, RAS, LCN, mentions légales',
    'description': """
        Localisation comptable pour les entreprises télécom marocaines :

        * Plan comptable CGNC (classes 1 à 7)
        * Taux de TVA marocains (20 %, 14 %, 10 %, 7 %, 0 %)
        * Retenue à la source (RAS) 10 % sur prestations de services
        * Mentions légales obligatoires sur les factures (ICE, IF, RC, Patente, Capital social)
        * Lettre de Change Normalisée (LCN) sur les journaux de paiement
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': ['telecom_base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_tax_data.xml',
        'data/cgnc_chart_data.xml',
        'views/account_move_views.xml',
        'views/account_journal_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 2,
}
