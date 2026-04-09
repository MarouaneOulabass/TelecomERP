# -*- coding: utf-8 -*-
{
    'name': 'TelecomERP — Finance & Décomptes Maroc',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Situations de travaux, décomptes CCAG, avances de démarrage, retenues de garantie',
    'description': """
        Module de gestion financière des marchés publics de travaux télécom au Maroc :

        * Situations de travaux (facturation d'avancement en %)
        * Décomptes provisoires et définitifs (format CCAG Travaux)
        * Avances de démarrage (10 % ou 15 %) et suivi des remboursements
        * Retenue de garantie (10 %) et libération sur réception définitive
        * Alertes délai de paiement légal 60 jours (loi 69-21)
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': [
        'telecom_base',
        'telecom_site',
        'telecom_project',
        'telecom_contract',
        'telecom_localization_ma',
        'account',
        'mail',
    ],
    'data': [
        # Security first
        'security/telecom_finance_rules.xml',
        'security/ir.model.access.csv',
        # Sequences / master data
        'data/telecom_finance_sequences.xml',
        # Views
        'views/telecom_situation_views.xml',
        'views/telecom_decompte_views.xml',
        'views/telecom_avance_views.xml',
        'views/account_move_views.xml',
        'views/menu_views.xml',
        # Reports
        'report/telecom_decompte_report.xml',
        'report/telecom_decompte_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 40,
}
