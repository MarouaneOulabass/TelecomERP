# language: fr
Fonctionnalité: Suivi EPI et pointage chantier
  En tant que responsable HSE et chef de chantier
  Je veux suivre les dotations EPI des techniciens et le pointage terrain
  Afin de garantir la sécurité et le suivi de la présence sur site

  # ── EPI — Dotation et alertes ────────────────────────────────────────────

  Scénario: Dotation EPI avec date d'expiration calculée automatiquement
    Soit un type EPI "Casque de chantier" avec une périodicité de "24" mois
    Et un employé "Rachid Bennani" existe
    Quand je crée une dotation EPI pour cet employé le "2024-01-15"
    Alors la date d'expiration de la dotation est "2026-01-15"

  Scénario: EPI expiré — statut "expired"
    Soit la date du jour est "2025-02-01"
    Et un type EPI "Harnais antichute" avec une périodicité de "12" mois
    Et un employé "Youssef Tazi" existe
    Et une dotation EPI datée du "2024-01-01" existe pour cet employé
    Alors le statut de la dotation est "expired"

  # ── Pointage chantier ────────────────────────────────────────────────────

  Scénario: Pointage avec heures supplémentaires calculées automatiquement
    Soit un employé "Karim Idrissi" existe
    Et un site "Site Pointage Test" avec le code "PT-001" existe
    Quand je crée un pointage pour cet employé sur ce site le "2024-03-15" de 7h00 à 18h00
    Alors la durée est de "11.0" heures
    Et les heures supplémentaires sont de "3.0" heures
