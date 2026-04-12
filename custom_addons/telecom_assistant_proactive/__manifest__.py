{
    'name': 'TelecomERP — Assistant Proactif',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Notifications proactives et watchers métier automatisés',
    'description': """
TelecomERP Assistant Proactif
==============================
- Watchers configurables (marge, caution, pointage, factures, habilitations, SLA)
- Notifications in-app avec niveaux de sévérité
- Canaux de livraison extensibles (in-app actif, email/whatsapp/sms préparés)
- Intégration feature flags pour activation/désactivation à chaud
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': [
        'telecom_base',
        'telecom_feature_flags',
        'telecom_cost',
        'telecom_margin',
        'telecom_contract',
        'telecom_hr_ma',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/telecom_proactive_cron.xml',
        'views/telecom_proactive_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 6,
}
