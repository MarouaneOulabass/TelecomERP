"""
Feature flags for the telecom_assistant_proactive capability.
Standardized format read automatically at installation time.
"""

FLAGS = [
    # Watchers pilotes (actifs par défaut)
    {
        'code': 'assistant_proactive.watcher_marge_sous_seuil',
        'name': "Alerte marge sous seuil",
        'description': "Pousse une notification quand la marge d'un projet passe sous le seuil configuré.",
        'category': 'watchers',
        'default_value': True,
    },
    {
        'code': 'assistant_proactive.watcher_caution_expirant',
        'name': "Alerte caution expirant",
        'description': "Pousse une notification à J-30, J-15 et J-7 avant expiration d'une caution.",
        'category': 'watchers',
        'default_value': True,
    },
    {
        'code': 'assistant_proactive.watcher_pointage_manquant',
        'name': "Alerte pointage manquant",
        'description': "Pousse une notification en fin de journée pour chaque technicien affecté mais non pointé.",
        'category': 'watchers',
        'default_value': True,
    },
    # Autres watchers (inactifs par défaut, activables par l'admin)
    {
        'code': 'assistant_proactive.watcher_facture_impayee',
        'name': "Alerte facture impayée J+30",
        'description': "Notifie quand une facture client reste impayée plus de 30 jours.",
        'category': 'watchers',
        'default_value': False,
    },
    {
        'code': 'assistant_proactive.watcher_habilitation_expirant',
        'name': "Alerte habilitation expirant",
        'description': "Notifie avant expiration d'une habilitation technicien (hauteur, électrique).",
        'category': 'watchers',
        'default_value': False,
    },
    {
        'code': 'assistant_proactive.watcher_derive_marge_hebdo',
        'name': "Alerte dérive marge hebdomadaire",
        'description': "Notifie quand la marge hebdomadaire dérive au-delà du seuil configuré.",
        'category': 'watchers',
        'default_value': False,
    },
    {
        'code': 'assistant_proactive.watcher_sla_depasse',
        'name': "Alerte SLA dépassé",
        'description': "Notifie quand le délai contractuel d'intervention est dépassé.",
        'category': 'watchers',
        'default_value': False,
    },
    # Canaux de livraison
    {
        'code': 'assistant_proactive.channel_in_app',
        'name': "Canal in-app",
        'description': "Notifications affichées dans l'interface TelecomERP.",
        'category': 'channels',
        'default_value': True,
    },
    {
        'code': 'assistant_proactive.channel_email',
        'name': "Canal email",
        'description': "Envoi de notifications par email. Non activé en V1.5.",
        'category': 'channels',
        'default_value': False,
    },
    {
        'code': 'assistant_proactive.channel_whatsapp',
        'name': "Canal WhatsApp",
        'description': "Envoi de notifications par WhatsApp. Non activé en V1.5.",
        'category': 'channels',
        'default_value': False,
    },
    # Features UX
    {
        'code': 'assistant_proactive.digest_matinal',
        'name': "Digest matinal",
        'description': "Envoie un résumé des alertes en début de journée.",
        'category': 'ux',
        'default_value': False,
    },
]
