{
    'name': 'TelecomERP — Feature Flags',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Feature flags runtime pour activer/désactiver des sous-fonctionnalités à chaud',
    'description': """
TelecomERP Feature Flags
========================
Mécanisme de feature flags runtime permettant aux administrateurs
d'activer ou désactiver des sous-fonctionnalités à chaud,
sans redéploiement et sans modifier le tenant_profile.

- Déclaration des flags par capability via feature_flags.py
- Décorateur @feature_flag pour conditionner le code
- Historique complet des changements
- Écran d'administration avec toggle
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': ['telecom_base'],
    'data': [
        'security/telecom_security.xml',
        'security/ir.model.access.csv',
        'views/feature_flag_views.xml',
        'views/menu_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 0,
}
