{
    'name': 'TelecomERP — Administration Tests BDD',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Interface d\'administration des tests BDD depuis Odoo',
    'description': """
Administration des tests BDD TelecomERP
========================================
Permet au métier de :
- Visualiser tous les scénarios BDD par module
- Consulter les résultats de la dernière exécution
- Lancer les tests depuis l'interface Odoo
- Suivre la couverture par module
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': ['telecom_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/telecom_test_scenario_views.xml',
        'views/telecom_test_run_views.xml',
        'views/telecom_test_feature_views.xml',
        'views/telecom_test_dashboard_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 100,
}
