# language: fr
Fonctionnalité: Pipeline des Appels d'Offres (AO)
  En tant que chargé d'affaires
  Je veux suivre chaque AO de la détection à la transformation en contrat
  Afin de piloter le taux de succès commercial

  Contexte:
    Soit un organisme public "ONEE" de type "public_org" existe
    Et un opérateur "Orange Maroc" de type "operator" existe

  # ── Création ─────────────────────────────────────────────────────────────

  Scénario: Création d'un AO avec numérotation automatique
    Quand je crée un AO "Déploiement Fibre Oujda 2024" pour l'organisme "ONEE"
    Alors l'AO est créé avec succès
    Et le numéro AO est généré automatiquement
    Et l'état de l'AO est "detecte"

  Scénario: Numéro AO unique — doublon refusé
    Soit un AO avec le numéro "AO/2024/001" existe déjà
    Quand je tente de créer un AO avec le même numéro "AO/2024/001"
    Alors une erreur d'intégrité est levée

  # ── Pipeline ─────────────────────────────────────────────────────────────

  Scénario: Transition Détecté → En étude
    Soit un AO à l'état "detecte" existe
    Quand je passe l'AO à l'état "etude"
    Alors l'état de l'AO est "etude"

  Scénario: Transition En étude → Soumis avec date limite obligatoire
    Soit un AO à l'état "etude" avec date limite de remise "2024-06-30" existe
    Quand je soumets l'AO
    Alors l'état de l'AO est "soumis"

  Scénario: Impossible de soumettre sans date limite de remise
    Soit un AO à l'état "etude" sans date limite de remise existe
    Quand je tente de soumettre l'AO
    Alors une erreur utilisateur est levée indiquant "date limite de remise"

  Scénario: Transition Soumis → Gagné
    Soit un AO à l'état "soumis" existe
    Quand je marque l'AO comme gagné
    Alors l'état de l'AO est "gagne"

  Scénario: Transition Soumis → Perdu
    Soit un AO à l'état "soumis" existe
    Quand je marque l'AO comme perdu
    Alors l'état de l'AO est "perdu"

  Scénario: Transition Gagné → Transformé en projet
    Soit un AO à l'état "gagne" existe
    Quand je transforme l'AO en projet
    Alors l'état de l'AO est "projet"

  Scénario: Impossible de transformer en projet si non gagné
    Soit un AO à l'état "soumis" existe
    Quand je tente de transformer l'AO en projet
    Alors une erreur utilisateur est levée indiquant "Seul un AO gagné"

  Scénario: Abandon possible depuis tout état actif
    Soit un AO à l'état "etude" existe
    Quand j'abandonne l'AO
    Alors l'état de l'AO est "abandonne"

  Scénario: Transition invalide — Détecté → Soumis refusée
    Soit un AO à l'état "detecte" existe
    Quand je tente de passer directement à l'état "soumis"
    Alors une erreur utilisateur est levée

  # ── Jours avant remise ───────────────────────────────────────────────────

  Scénario: Calcul jours avant remise
    Soit la date du jour est "2024-03-01"
    Et un AO avec date limite de remise "2024-03-15" existe
    Alors le champ "jours_avant_remise" de l'AO est "14"

  Scénario: Jours avant remise = 0 si date non renseignée
    Soit un AO sans date limite de remise existe
    Alors le champ "jours_avant_remise" de l'AO est "0"
