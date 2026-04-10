# language: fr
Fonctionnalité: Workflow du décompte CCAG et délai légal de paiement (Loi 69-21)
  En tant que responsable facturation
  Je veux gérer le cycle d'approbation d'un décompte jusqu'au paiement
  Et être alerté en cas de dépassement du délai légal de 60 jours

  Contexte:
    Soit un projet "Projet CCAG Test" et un contrat "CONT-TEST-001" existent
    Et un client "Opérateur Test" existe
    Et un décompte provisoire en brouillon est créé

  # ── Séquençage ───────────────────────────────────────────────────────────

  Scénario: Séquence décompte provisoire format DC/YYYY/NNN
    Alors le nom du décompte commence par "DC/"

  Scénario: Séquence décompte définitif format DDF/YYYY/NNN
    Soit un décompte définitif est créé
    Alors le nom du décompte commence par "DDF/"

  # ── Workflow ─────────────────────────────────────────────────────────────

  Scénario: Transition brouillon → soumis — date de soumission enregistrée
    Quand je soumets le décompte
    Alors l'état du décompte est "soumis"
    Et la date de soumission est renseignée

  Scénario: Transition soumis → approuvé
    Soit le décompte est à l'état "soumis"
    Quand j'approuve le décompte
    Alors l'état du décompte est "approuve"

  Scénario: Transition approuvé → phase contradictoire
    Soit le décompte est à l'état "approuve"
    Quand je passe le décompte en phase contradictoire
    Alors l'état du décompte est "contradictoire"

  Scénario: Transition approuvé → signé (sans phase contradictoire)
    Soit le décompte est à l'état "approuve"
    Quand je signe le décompte
    Alors l'état du décompte est "signe"

  Scénario: Transition contradictoire → signé
    Soit le décompte est à l'état "contradictoire"
    Quand je signe le décompte
    Alors l'état du décompte est "signe"

  Scénario: Création d'une facture client depuis décompte signé
    Soit le décompte est à l'état "signe"
    Quand je crée la facture depuis le décompte
    Alors une facture client est créée et liée au décompte

  Scénario: Impossible de créer une deuxième facture pour le même décompte
    Soit le décompte est à l'état "signe"
    Et une facture est déjà liée au décompte
    Quand je tente de créer une nouvelle facture
    Alors une erreur utilisateur est levée indiquant "facture existe déjà"

  Scénario: Seul un administrateur peut remettre un décompte en brouillon
    Soit le décompte est à l'état "soumis"
    Et je suis connecté en tant qu'utilisateur non-administrateur
    Quand je tente de remettre le décompte en brouillon
    Alors une erreur utilisateur est levée indiquant "administrateur"

  Scénario: Impossible de soumettre un décompte déjà soumis
    Soit le décompte est à l'état "soumis"
    Quand je tente de soumettre à nouveau le décompte
    Alors une erreur utilisateur est levée indiquant "brouillon"

  # ── Loi 69-21 — Délai paiement 60 jours ────────────────────────────────

  Scénario: Date limite paiement = date soumission + 60 jours
    Soit un décompte soumis le "2024-01-01"
    Alors la date limite de paiement est "2024-03-01"

  Scénario: Alerte délai dépassé si non payé après 60 jours
    Soit un décompte soumis le "2024-01-01"
    Et la date du jour est "2024-03-02"
    Et le décompte n'est pas à l'état "paye"
    Alors le champ "delai_depasse" est True

  Scénario: Pas d'alerte délai si décompte payé
    Soit un décompte soumis le "2024-01-01" et payé
    Et la date du jour est "2024-03-02"
    Alors le champ "delai_depasse" est False

  Scénario: Pas d'alerte si dans le délai légal
    Soit un décompte soumis le "2024-01-01"
    Et la date du jour est "2024-02-15"
    Et le décompte n'est pas à l'état "paye"
    Alors le champ "delai_depasse" est False

  Scénario: Exactement au jour 60 — pas encore en dépassement
    Soit un décompte soumis le "2024-01-01"
    Et la date du jour est "2024-03-01"
    Et le décompte n'est pas à l'état "paye"
    Alors le champ "delai_depasse" est False

  Scénario: Décompte sans date de soumission — pas d'alerte
    Soit un décompte sans date de soumission
    Alors le champ "delai_depasse" est False
