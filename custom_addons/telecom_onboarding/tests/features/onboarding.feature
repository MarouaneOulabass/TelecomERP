# language: fr
Fonctionnalité: Onboarding IA — session de configuration client
  En tant qu'administrateur TelecomERP
  Je veux créer une session d'onboarding assistée par IA
  Afin de configurer un nouveau tenant rapidement

  Scénario: Création d'une session d'onboarding
    Quand je crée une session d'onboarding
    Alors la session est à l'état "upload"
    Et la session appartient à l'utilisateur courant

  Scénario: Extraction sans documents échoue proprement
    Quand je crée une session d'onboarding
    Et j'essaie d'extraire sans documents
    Alors une erreur utilisateur est levée

  Scénario: Nom de session reflète la raison sociale
    Quand je crée une session d'onboarding
    Et je renseigne la raison sociale "Atlas Telecom"
    Alors le nom de session contient "Atlas Telecom"
