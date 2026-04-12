# language: fr
Fonctionnalité: Assistant conversationnel TelecomERP
  En tant qu'utilisateur TelecomERP
  Je veux poser des questions en langage naturel
  Afin d'obtenir des réponses exactes sur mes données

  # ── Pas de menu racine ──────────────────────────────────────────

  Scénario: Aucun menu racine n'existe pour l'assistant
    Quand je cherche les menus racines de l'assistant
    Alors aucun menu racine n'est trouvé pour telecom_assistant

  # ── Registry d'outils ───────────────────────────────────────────

  Scénario: Le registry contient au moins 7 outils
    Quand je consulte le registry d'outils de l'assistant
    Alors au moins 7 outils sont enregistrés

  Scénario: L'outil list_projects est enregistré et fonctionnel
    Quand j'appelle l'outil "list_projects" sans paramètres
    Alors le résultat contient une liste de projets

  Scénario: L'outil get_sites est enregistré et fonctionnel
    Quand j'appelle l'outil "get_sites" sans paramètres
    Alors le résultat contient une liste de sites

  # ── Conversations ───────────────────────────────────────────────

  Scénario: Création d'une conversation
    Quand je crée une nouvelle conversation assistant
    Alors la conversation est créée avec succès
    Et l'utilisateur est l'utilisateur courant

  # ── Traçabilité ─────────────────────────────────────────────────

  Scénario: Les outils retournent du JSON sérialisable
    Quand j'appelle l'outil "get_expiring_habilitations" sans paramètres
    Alors le résultat est sérialisable en JSON
