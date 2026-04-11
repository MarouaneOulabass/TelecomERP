{
    'name': 'TelecomERP — Multi-Tenant SaaS',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Provisioning multi-tenant, profil YAML, isolation par base de données',
    'description': """
TelecomERP Multi-Tenant SaaS
==============================
- Provisioning automatique de nouveaux tenants via profil YAML
- Chaque tenant = 1 base de données isolée
- Configuration automatique : modules, société, devise, langue, branding
- Interface admin pour gérer les tenants
- Compatible avec le TENANT_PROFILE_SCHEMA.json
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': ['telecom_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/telecom_tenant_views.xml',
        'wizard/telecom_tenant_provision_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 0,
}
