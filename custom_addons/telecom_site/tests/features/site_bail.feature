# language: fr
Fonctionnalité: Alertes d'expiration du bail d'un site télécom
  En tant que gestionnaire de sites
  Je veux être alerté 90 jours avant l'expiration d'un bail
  Afin d'anticiper les renouvellements et éviter les coupures d'accès

  # ── Alerte active (fenêtre 0-90 jours) ──────────────────────────────────

  Scénario: Bail expirant dans 1 jour — alerte activée
    Soit la date du jour est "2024-05-29"
    Et un site avec une date de fin de bail "2024-05-30" existe
    Quand je recalcule l'alerte d'expiration du bail
    Alors le champ "bail_expiration_warning" est True

  Scénario: Bail expirant dans 89 jours — alerte activée
    Soit la date du jour est "2024-03-01"
    Et un site avec une date de fin de bail "2024-05-29" existe
    Quand je recalcule l'alerte d'expiration du bail
    Alors le champ "bail_expiration_warning" est True

  Scénario: Bail expirant exactement dans 90 jours — alerte activée (limite incluse)
    Soit la date du jour est "2024-03-01"
    Et un site avec une date de fin de bail "2024-05-30" existe
    Quand je recalcule l'alerte d'expiration du bail
    Alors le champ "bail_expiration_warning" est True

  # ── Pas d'alerte (hors fenêtre) ──────────────────────────────────────────

  Scénario: Bail expirant dans 91 jours — pas d'alerte
    Soit la date du jour est "2024-03-01"
    Et un site avec une date de fin de bail "2024-05-31" existe
    Quand je recalcule l'alerte d'expiration du bail
    Alors le champ "bail_expiration_warning" est False

  Scénario: Bail expirant dans 1 an — pas d'alerte
    Soit la date du jour est "2024-01-01"
    Et un site avec une date de fin de bail "2025-01-01" existe
    Quand je recalcule l'alerte d'expiration du bail
    Alors le champ "bail_expiration_warning" est False

  Scénario: Bail déjà expiré hier — pas d'alerte (gestion séparée)
    Soit la date du jour est "2024-03-01"
    Et un site avec une date de fin de bail "2024-02-29" existe
    Quand je recalcule l'alerte d'expiration du bail
    Alors le champ "bail_expiration_warning" est False

  Scénario: Bail expiré depuis 6 mois — pas d'alerte
    Soit la date du jour est "2024-06-01"
    Et un site avec une date de fin de bail "2023-12-01" existe
    Quand je recalcule l'alerte d'expiration du bail
    Alors le champ "bail_expiration_warning" est False

  # ── Cas particuliers ──────────────────────────────────────────────────────

  Scénario: Site sans date de fin de bail — pas d'alerte
    Soit un site sans date de fin de bail existe
    Quand je recalcule l'alerte d'expiration du bail
    Alors le champ "bail_expiration_warning" est False

  Scénario: Bail expirant exactement aujourd'hui — alerte activée
    Soit la date du jour est "2024-04-15"
    Et un site avec une date de fin de bail "2024-04-15" existe
    Quand je recalcule l'alerte d'expiration du bail
    Alors le champ "bail_expiration_warning" est True
