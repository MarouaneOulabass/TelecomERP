{
    'name': 'TelecomERP — Audit Log & Analytics',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Traçabilité complète : qui fait quoi, quand, stats d\'usage, agents IA',
    'description': """
Système centralisé de traçabilité TelecomERP
=============================================
- Log automatique de toutes les opérations CRUD sur les modèles telecom
- Traçabilité des agents IA (assistant, onboarding)
- Dashboard stats d'usage (actions/jour, modules les plus utilisés, users actifs)
- Qui a modifié quoi et quand
- Export CSV des logs
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': ['telecom_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/telecom_audit_log_views.xml',
        'views/telecom_audit_stats_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 99,
}
