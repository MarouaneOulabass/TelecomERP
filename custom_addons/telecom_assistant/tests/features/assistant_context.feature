# language: fr
Fonctionnalité: Assistant — capture de contexte implicite
  En tant qu'utilisateur TelecomERP
  Je veux que l'assistant détecte mon contexte courant
  Afin de répondre sans que je répète le nom du projet ou du site

  Scénario: Question avec contexte implicite est enrichie
    Étant donné un projet existant "FTTH Casablanca"
    Quand j'envoie un message avec le contexte du projet "FTTH Casablanca"
    Alors le message envoyé contient "[Contexte:"
    Et le message envoyé contient "FTTH Casablanca"

  Scénario: Question sans contexte ne crash pas
    Quand j'envoie un message sans contexte valide
    Alors le message envoyé ne contient pas "[Contexte:"
    Et aucune erreur n'est levée
