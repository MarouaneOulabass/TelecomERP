# language: fr
Fonctionnalité: Gestion du cycle de vie des contrats télécom
  En tant que chargé d'affaires
  Je veux gérer les contrats opérateurs avec leurs SLA et cautions bancaires
  Afin de respecter les engagements contractuels et suivre les échéances

  Contexte:
    Soit un partenaire opérateur "IAM Mobile" de type "operator" existe

  # ── Création contrat ─────────────────────────────────────────────────────

  Scénario: Création d'un contrat avec référence auto-générée
    Quand je crée un contrat "Contrat Maintenance IAM" de type "maintenance" pour "IAM Mobile"
    Alors le contrat est créé avec succès
    Et la référence contrat est générée automatiquement

  Scénario: Un contrat maintenance en brouillon a l'état "brouillon" par défaut
    Quand je crée un contrat "Contrat Déploiement" de type "deploiement" pour "IAM Mobile"
    Alors l'état du contrat est "brouillon"

  # ── Transitions d'état ───────────────────────────────────────────────────

  Scénario: Activation d'un contrat en brouillon
    Soit un contrat "Contrat Test" à l'état "brouillon" existe
    Quand j'active le contrat
    Alors l'état du contrat est "actif"

  Scénario: Suspension d'un contrat actif
    Soit un contrat "Contrat Test" à l'état "actif" existe
    Quand je suspends le contrat
    Alors l'état du contrat est "suspendu"

  Scénario: Réactivation d'un contrat suspendu
    Soit un contrat "Contrat Test" à l'état "suspendu" existe
    Quand je réactive le contrat
    Alors l'état du contrat est "actif"

  Scénario: Résiliation d'un contrat actif
    Soit un contrat "Contrat Test" à l'état "actif" existe
    Quand je résilie le contrat
    Alors l'état du contrat est "resilie"

  Scénario: Résiliation d'un contrat suspendu
    Soit un contrat "Contrat Test" à l'état "suspendu" existe
    Quand je résilie le contrat
    Alors l'état du contrat est "resilie"

  # ── Transitions invalides ────────────────────────────────────────────────

  Scénario: Impossible de résilier un contrat en brouillon
    Soit un contrat "Contrat Test" à l'état "brouillon" existe
    Quand je tente de résilier le contrat
    Alors une erreur de workflow est levée

  Scénario: Impossible de suspendre un contrat en brouillon
    Soit un contrat "Contrat Test" à l'état "brouillon" existe
    Quand je tente de suspendre le contrat
    Alors une erreur de workflow est levée

  Scénario: Impossible de réactiver un contrat actif
    Soit un contrat "Contrat Test" à l'état "actif" existe
    Quand je tente de réactiver le contrat
    Alors une erreur de workflow est levée

  Plan du Scénario: Tous les types de contrat sont acceptés
    Quand je crée un contrat "Test <type>" de type "<type>" pour "IAM Mobile"
    Alors le contrat est créé avec succès

    Exemples:
      | type              |
      | cadre_operateur   |
      | maintenance       |
      | deploiement       |
      | sous_traitance    |
      | bail_site         |

  # ── Alerte expiration ────────────────────────────────────────────────────

  Scénario: Alerte expiration — contrat actif expirant dans moins de 90 jours
    Soit la date du jour est "2024-03-01"
    Et un contrat actif avec date de fin "2024-05-15" existe
    Alors l'alerte d'expiration du contrat est active

  Scénario: Pas d'alerte expiration — date de fin dans plus de 90 jours
    Soit la date du jour est "2024-03-01"
    Et un contrat actif avec date de fin "2025-01-01" existe
    Alors l'alerte d'expiration du contrat est inactive

  Scénario: Pas d'alerte expiration pour un contrat en brouillon même si proche
    Soit la date du jour est "2024-03-01"
    Et un contrat en brouillon avec date de fin "2024-03-15" existe
    Alors l'alerte d'expiration du contrat est inactive

  Scénario: Pas d'alerte pour un contrat à durée indéterminée (sans date de fin)
    Soit un contrat actif sans date de fin existe
    Alors l'alerte d'expiration du contrat est inactive

  # ── SLA contractuel ──────────────────────────────────────────────────────

  Scénario: Un contrat maintenance avec SLA 48h d'intervention et 72h de réparation
    Quand je crée un contrat "SLA Test" de type "maintenance" pour "IAM Mobile" avec SLA "48" h intervention et "72" h réparation
    Alors le contrat est créé avec succès
    Et le SLA d'intervention est de "48" heures
    Et le SLA de réparation est de "72" heures

  # ── Cautions bancaires ───────────────────────────────────────────────────

  Scénario: Création d'une caution provisoire liée à un contrat
    Soit un contrat actif "Contrat Caution" existe
    Quand j'ajoute une caution "provisoire" de "15000" MAD émise par "Attijariwafa Bank"
    Alors le contrat possède "1" caution(s) bancaire(s)

  Scénario: État d'une caution dont l'expiration est dans plus de 60 jours
    Soit la date du jour est "2024-03-01"
    Et une caution avec date d'expiration "2024-06-01" existe
    Alors l'état de la caution est "active"

  Scénario: État d'une caution expirant dans moins de 60 jours
    Soit la date du jour est "2024-03-01"
    Et une caution avec date d'expiration "2024-04-15" existe
    Alors l'état de la caution est "expiring_soon"

  Scénario: État d'une caution dont la date est dépassée
    Soit la date du jour est "2024-03-01"
    Et une caution avec date d'expiration "2024-02-15" existe
    Alors l'état de la caution est "expired"

  Scénario: Une caution libérée a l'état "liberee" quelle que soit la date
    Soit une caution libérée existe
    Alors l'état de la caution est "liberee"
