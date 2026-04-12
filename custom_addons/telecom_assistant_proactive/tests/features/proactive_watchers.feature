# language: fr
Fonctionnalité: Watchers proactifs et notifications
  En tant que responsable TelecomERP
  Je veux recevoir des alertes automatiques sur les événements critiques
  Afin d'anticiper les problèmes avant qu'ils ne deviennent bloquants

  Contexte:
    Soit un environnement TelecomERP avec les modules proactifs installés

  Scénario: Un watcher avec flag désactivé ne génère pas de notification
    Soit un watcher "marge_sous_seuil" configuré
    Et le flag "assistant_proactive.watcher_marge_sous_seuil" est désactivé
    Quand le cron des watchers est exécuté
    Alors aucune notification n'est générée pour ce watcher

  Scénario: Un watcher avec flag actif génère des notifications
    Soit un watcher "marge_sous_seuil" configuré
    Et le flag "assistant_proactive.watcher_marge_sous_seuil" est actif
    Quand le cron des watchers est exécuté
    Alors des notifications sont générées si les conditions sont remplies

  Scénario: Fallback canal si WhatsApp désactivé
    Soit le flag "assistant_proactive.channel_whatsapp" désactivé
    Et le flag "assistant_proactive.channel_in_app" actif
    Quand une notification critique est créée
    Alors elle est livrée via le canal in-app sans erreur

  Scénario: Notification marquée comme lue
    Soit une notification non lue pour l'utilisateur courant
    Quand l'utilisateur marque la notification comme lue
    Alors la notification est marquée comme lue
