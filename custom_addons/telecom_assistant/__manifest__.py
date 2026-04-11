{
    'name': 'TelecomERP — Assistant Conversationnel',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Assistant IA contextuel avec tool-use pour interroger les données ERP',
    'description': """
Assistant conversationnel contextuel TelecomERP
=================================================
- Questions en langage naturel (FR, AR, darija)
- Réponses exactes via tool-use (pas de RAG, pas d'hallucination de chiffres)
- Chaque module expose ses outils au registry
- Traçabilité complète (question, outils, résultats, réponse)
- Respect des record rules Odoo (isolation multi-tenant)
- Budget LLM plafonné par tenant
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': [
        'telecom_base',
        'telecom_site',
        'telecom_intervention',
        'telecom_project',
        'telecom_cost',
        'telecom_margin',
        'telecom_contract',
        'telecom_hr_ma',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/telecom_assistant_views.xml',
        'views/menu_views.xml',
    ],
    'external_dependencies': {
        'python': ['anthropic'],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 5,
}
