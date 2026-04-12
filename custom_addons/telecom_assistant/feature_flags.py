"""
Feature flags for the telecom_assistant capability.
Standardized format read automatically at installation time.
"""

FLAGS = [
    {
        'code': 'assistant.enabled',
        'name': "Assistant activé",
        'description': "Active ou désactive l'assistant conversationnel globalement.",
        'category': 'core',
        'default_value': True,
    },
    {
        'code': 'assistant.context_capture',
        'name': "Capture contexte",
        'description': "Capture automatique du contexte courant (modèle, record, filtres) pour enrichir les requêtes.",
        'category': 'core',
        'default_value': True,
    },
    {
        'code': 'assistant.show_tool_calls',
        'name': "Afficher appels outils (debug)",
        'description': "Affiche les appels d'outils dans l'interface utilisateur en mode debug.",
        'category': 'debug',
        'default_value': False,
    },
]
