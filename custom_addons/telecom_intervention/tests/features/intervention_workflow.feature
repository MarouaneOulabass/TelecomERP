# language: fr
Fonctionnalité: Workflow complet du Bon d'Intervention (BI)
  En tant que chef de chantier
  Je veux gérer le cycle de vie des bons d'intervention
  Afin de tracer chaque mission terrain de la création à la clôture

  Contexte:
    Soit un site "Site TEST-BI" avec le code "TEST-BI-001" existe
    Et un employé technicien "Ahmed El Amrani" existe
    Et un employé chef de chantier "Karim Benali" avec le groupe "chef_chantier" existe

  # ── Création ─────────────────────────────────────────────────────────────

  Scénario: Création d'un BI avec numérotation automatique
    Quand je crée un bon d'intervention pour le site "Site TEST-BI" planifié le "2024-03-15 09:00:00"
    Alors le bon d'intervention est créé avec succès
    Et le numéro du BI commence par "BI/"
    Et l'état du BI est "draft"

  Scénario: Opérateur renseigné automatiquement depuis le site
    Soit le site "Site TEST-BI" a un opérateur "Inwi" rattaché
    Quand je crée un bon d'intervention pour le site "Site TEST-BI" planifié le "2024-03-15 09:00:00"
    Alors l'opérateur du BI est "Inwi"

  Scénario: Types d'intervention disponibles couvrent tous les cas terrain
    Alors les types d'intervention disponibles incluent "preventive"
    Et les types d'intervention disponibles incluent "corrective"
    Et les types d'intervention disponibles incluent "installation"
    Et les types d'intervention disponibles incluent "audit"
    Et les types d'intervention disponibles incluent "depose"

  # ── Transition Draft → Planifié ──────────────────────────────────────────

  Scénario: Planification d'un BI avec date planifiée — succès
    Soit un BI en brouillon avec la date planifiée "2024-03-20 08:00:00" existe
    Quand je planifie le BI
    Alors l'état du BI est "planifie"

  Scénario: Planification impossible sans date planifiée
    Soit un BI en brouillon sans date planifiée existe
    Quand je tente de planifier le BI
    Alors une erreur utilisateur est levée indiquant "date planifiée"

  Scénario: Planification impossible depuis un état autre que brouillon
    Soit un BI à l'état "en_cours" existe
    Quand je tente de planifier le BI
    Alors une erreur utilisateur est levée indiquant "brouillon"

  # ── Transition Planifié → En cours ──────────────────────────────────────

  Scénario: Démarrage d'un BI planifié — date de début réelle enregistrée
    Soit un BI à l'état "planifie" existe
    Quand je démarre le BI
    Alors l'état du BI est "en_cours"
    Et la date de début réelle est renseignée

  Scénario: Démarrage impossible depuis brouillon
    Soit un BI à l'état "draft" existe
    Quand je tente de démarrer le BI
    Alors une erreur utilisateur est levée indiquant "Seuls les bons planifiés"

  # ── Transition En cours → Terminé ────────────────────────────────────────

  Scénario: Terminer un BI en cours — date de fin réelle enregistrée
    Soit un BI à l'état "en_cours" existe
    Quand je termine le BI
    Alors l'état du BI est "termine"
    Et la date de fin réelle est renseignée

  Scénario: Terminer impossible depuis planifié
    Soit un BI à l'état "planifie" existe
    Quand je tente de terminer le BI
    Alors une erreur utilisateur est levée indiquant "en cours"

  # ── Calcul durée réelle ───────────────────────────────────────────────────

  Scénario: Durée réelle calculée depuis les timestamps (2h30)
    Soit un BI avec début réel "2024-03-15 09:00:00" et fin réelle "2024-03-15 11:30:00" existe
    Alors la durée réelle du BI est "2.5" heures

  Scénario: Durée réelle calculée pour une journée complète (8h)
    Soit un BI avec début réel "2024-03-15 08:00:00" et fin réelle "2024-03-15 16:00:00" existe
    Alors la durée réelle du BI est "8.0" heures

  Scénario: Durée réelle = 0 si fin réelle non renseignée
    Soit un BI à l'état "en_cours" sans fin réelle existe
    Alors la durée réelle du BI est "0.0" heures

  # ── Transition Terminé → Validé (contrôle d'accès) ───────────────────────

  Scénario: Validation par un chef de chantier autorisé — succès
    Soit un BI à l'état "termine" existe
    Et je suis connecté en tant que chef de chantier "Karim Benali"
    Quand je valide le BI
    Alors l'état du BI est "valide"

  Scénario: Validation par un responsable — succès
    Soit un BI à l'état "termine" existe
    Et je suis connecté en tant que responsable
    Quand je valide le BI
    Alors l'état du BI est "valide"

  Scénario: Validation refusée pour un technicien simple
    Soit un BI à l'état "termine" existe
    Et je suis connecté en tant que technicien sans droits de validation
    Quand je tente de valider le BI
    Alors une erreur utilisateur est levée indiquant "chef de chantier"

  Scénario: Validation impossible depuis un état non terminé
    Soit un BI à l'état "en_cours" existe
    Et je suis connecté en tant que chef de chantier "Karim Benali"
    Quand je tente de valider le BI
    Alors une erreur utilisateur est levée indiquant "Seuls les bons terminés"

  # ── Annulation ────────────────────────────────────────────────────────────

  Scénario: Annulation d'un BI planifié
    Soit un BI à l'état "planifie" existe
    Quand j'annule le BI
    Alors l'état du BI est "annule"

  Scénario: Annulation d'un BI en cours
    Soit un BI à l'état "en_cours" existe
    Quand j'annule le BI
    Alors l'état du BI est "annule"

  Scénario: Annulation impossible d'un BI déjà facturé
    Soit un BI à l'état "facture" existe
    Quand je tente d'annuler le BI
    Alors une erreur utilisateur est levée indiquant "facturé"

  # ── Remise en brouillon ───────────────────────────────────────────────────

  Scénario: Remise en brouillon depuis annulé — succès
    Soit un BI à l'état "annule" existe
    Quand je remets le BI en brouillon
    Alors l'état du BI est "draft"

  Scénario: Remise en brouillon impossible depuis terminé
    Soit un BI à l'état "termine" existe
    Quand je tente de remettre le BI en brouillon
    Alors une erreur utilisateur est levée indiquant "annulés"

  # ── Contrainte dates ──────────────────────────────────────────────────────

  Scénario: Date de fin réelle antérieure à la date de début — refusée
    Quand je crée un BI avec début réel "2024-03-15 11:00:00" et fin réelle "2024-03-15 09:00:00"
    Alors une erreur de validation est levée indiquant "fin réelle"
