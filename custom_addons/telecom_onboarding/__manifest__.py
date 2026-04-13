{
    'name': 'TelecomERP — Agent IA Onboarding',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Onboarding assisté par IA : upload docs, extraction auto, provisioning',
    'description': """
Agent IA d'onboarding TelecomERP
==================================
1. Le client upload ses documents (RC, organigramme, statuts, patente)
2. L'agent IA (Claude API vision) extrait les informations
3. L'agent pose les questions manquantes via chat
4. Génération automatique du tenant_profile.yaml
5. Provisioning de la base client
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': ['telecom_base', 'telecom_tenant'],
    'data': [
        'security/ir.model.access.csv',
        'views/telecom_onboarding_views.xml',
        'views/menu_views.xml',
    ],
    'external_dependencies': {
        'python': ['anthropic'],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 0,
}
