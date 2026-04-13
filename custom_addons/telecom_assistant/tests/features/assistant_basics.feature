# language: fr
Fonctionnalité: Assistant — bases et widget popup
  En tant qu'utilisateur TelecomERP
  Je veux accéder à l'assistant via le widget popup
  Afin de poser des questions sans quitter mon écran courant

  Scénario: Le widget popup est disponible (pas de menu racine)
    Quand je cherche les menus racines de l'assistant
    Alors aucun menu racine n'est trouvé pour telecom_assistant

  Scénario: Une question simple reçoit une réponse de l'agent
    Étant donné une conversation assistant vierge
    Quand j'envoie la question "Bonjour, quels projets sont en cours ?" avec Claude mocké
    Alors la réponse de l'assistant n'est pas vide
    Et la réponse ne contient pas "Erreur"
