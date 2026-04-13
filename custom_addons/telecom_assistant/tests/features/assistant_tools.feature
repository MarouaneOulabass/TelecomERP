# language: fr
Fonctionnalité: Assistant — gestion des outils et cas limites
  En tant qu'utilisateur TelecomERP
  Je veux que l'assistant gère proprement les cas limites des outils
  Afin de ne jamais recevoir de données inventées ou de crash

  Scénario: Un outil retournant zéro résultat donne une réponse honnête
    Étant donné une conversation assistant vierge
    Quand l'outil mocké retourne zéro résultat et Claude répond "Aucune donnée trouvée"
    Alors la réponse de l'assistant contient "aucune"

  Scénario: Un appel d'outil échoué ne crash pas l'assistant
    Étant donné une conversation assistant vierge
    Quand l'outil mocké échoue avec une erreur et Claude répond proprement
    Alors la réponse de l'assistant n'est pas vide
    Et l'appel d'outil échoué est tracé
