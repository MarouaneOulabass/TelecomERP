# language: fr
Fonctionnalité: Gestion des habilitations sécurité des techniciens
  En tant que responsable HSE
  Je veux suivre les habilitations de chaque technicien avec alertes d'expiration
  Afin de garantir que seuls des techniciens qualifiés interviennent sur le terrain

  Contexte:
    Soit un type d'habilitation "Travail en hauteur" avec le code "TRAV_HAUTEUR" et une périodicité de "36" mois existe
    Et un type d'habilitation "Habilitation électrique B2" avec le code "ELEC_B2" et une périodicité de "12" mois existe
    Et un type d'habilitation "Habilitation électrique B1" avec le code "ELEC_B1" et une périodicité de "24" mois existe
    Et un employé technicien "Ali Mansouri" existe

  # ── Calcul de la date d'expiration ──────────────────────────────────────

  Scénario: Date d'expiration calculée automatiquement — habilitation 36 mois
    Quand l'employé obtient l'habilitation "Travail en hauteur" le "2024-01-15"
    Alors la date d'expiration calculée est "2027-01-15"

  Scénario: Date d'expiration calculée pour habilitation annuelle (12 mois)
    Quand l'employé obtient l'habilitation "Habilitation électrique B2" le "2024-06-01"
    Alors la date d'expiration calculée est "2025-06-01"

  Scénario: Date d'expiration calculée pour habilitation 24 mois
    Quand l'employé obtient l'habilitation "Habilitation électrique B1" le "2023-09-01"
    Alors la date d'expiration calculée est "2025-09-01"

  # ── Statut de l'habilitation ─────────────────────────────────────────────

  Scénario: Habilitation valide — statut "valid"
    Soit la date du jour est "2024-03-01"
    Et une habilitation avec date d'expiration "2026-01-01" existe pour l'employé
    Alors le statut de l'habilitation est "valid"

  Scénario: Habilitation valide à 61 jours de l'expiration — statut "valid"
    Soit la date du jour est "2024-03-01"
    Et une habilitation avec date d'expiration "2024-05-01" existe pour l'employé
    Alors le statut de l'habilitation est "valid"

  Scénario: Habilitation expirant dans exactement 60 jours — statut "expiring_soon"
    Soit la date du jour est "2024-03-01"
    Et une habilitation avec date d'expiration "2024-04-30" existe pour l'employé
    Alors le statut de l'habilitation est "expiring_soon"

  Scénario: Habilitation expirant dans 30 jours — statut "expiring_soon"
    Soit la date du jour est "2024-03-01"
    Et une habilitation avec date d'expiration "2024-03-31" existe pour l'employé
    Alors le statut de l'habilitation est "expiring_soon"

  Scénario: Habilitation expirant demain — statut "expiring_soon"
    Soit la date du jour est "2024-03-01"
    Et une habilitation avec date d'expiration "2024-03-02" existe pour l'employé
    Alors le statut de l'habilitation est "expiring_soon"

  Scénario: Habilitation expirée hier — statut "expired"
    Soit la date du jour est "2024-03-01"
    Et une habilitation avec date d'expiration "2024-02-29" existe pour l'employé
    Alors le statut de l'habilitation est "expired"

  Scénario: Habilitation expirée depuis 6 mois — statut "expired"
    Soit la date du jour est "2024-06-01"
    Et une habilitation avec date d'expiration "2023-12-01" existe pour l'employé
    Alors le statut de l'habilitation est "expired"

  # ── Contraintes de validation ────────────────────────────────────────────

  Scénario: Date d'expiration antérieure à la date d'obtention — refusée
    Quand je tente de créer une habilitation avec date d'obtention "2024-03-01" et date d'expiration "2024-01-01"
    Alors une erreur de validation est levée indiquant "expiration"

  Scénario: Code de type d'habilitation unique — doublon refusé
    Quand je tente de créer un type d'habilitation avec le code "TRAV_HAUTEUR" existant
    Alors une erreur d'intégrité est levée

  Scénario: Nom de type d'habilitation unique — doublon refusé
    Quand je tente de créer un type d'habilitation avec le nom "Travail en hauteur" existant
    Alors une erreur d'intégrité est levée
