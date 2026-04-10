# language: fr
Fonctionnalité: Suivi SLA des interventions terrain
  En tant que responsable opérations
  Je veux suivre le respect des délais contractuels SLA
  Afin d'alerter les équipes avant tout dépassement de délai

  Contexte:
    Soit un site "Site SLA Test" existe
    Et un BI planifié le "2024-03-15 08:00:00" avec un SLA de "48" heures existe

  # ── Calcul échéance SLA ──────────────────────────────────────────────────

  Scénario: Échéance SLA = date planifiée + délai contractuel en heures
    Alors l'échéance SLA du BI est "2024-03-17 08:00:00"

  Scénario: Échéance SLA avec délai 24h
    Soit un BI planifié le "2024-06-01 10:00:00" avec un SLA de "24" heures existe
    Alors l'échéance SLA du BI est "2024-06-02 10:00:00"

  Scénario: Échéance SLA nulle si délai SLA non défini
    Soit un BI planifié le "2024-03-15 08:00:00" sans délai SLA existe
    Alors l'échéance SLA du BI est nulle

  # ── Dépassement SLA ──────────────────────────────────────────────────────

  Scénario: SLA respecté — BI en cours dans les 48h
    Soit la date/heure courante est "2024-03-16 10:00:00"
    Et le BI est à l'état "en_cours"
    Alors le champ "sla_depasse" est False

  Scénario: SLA dépassé — BI encore en cours après l'échéance
    Soit la date/heure courante est "2024-03-17 09:00:00"
    Et le BI est à l'état "en_cours"
    Alors le champ "sla_depasse" est True

  Scénario: SLA non applicable — BI validé même après l'échéance
    Soit la date/heure courante est "2024-03-18 10:00:00"
    Et le BI est à l'état "valide"
    Alors le champ "sla_depasse" est False

  Scénario: SLA non applicable — BI facturé après l'échéance
    Soit la date/heure courante est "2024-03-18 10:00:00"
    Et le BI est à l'état "facture"
    Alors le champ "sla_depasse" est False

  Scénario: SLA non applicable — BI annulé
    Soit la date/heure courante est "2024-03-18 10:00:00"
    Et le BI est à l'état "annule"
    Alors le champ "sla_depasse" est False

  # ── Couleur SLA (indicateur kanban) ─────────────────────────────────────

  Scénario: Couleur SLA verte si plus de 24h avant l'échéance
    Soit la date/heure courante est "2024-03-16 06:00:00"
    Et le BI est à l'état "en_cours"
    Alors la couleur SLA du BI est "0"

  Scénario: Couleur SLA orange si moins de 24h avant l'échéance
    Soit la date/heure courante est "2024-03-17 07:00:00"
    Et le BI est à l'état "en_cours"
    Alors la couleur SLA du BI est "1"

  Scénario: Couleur SLA rouge si SLA dépassé
    Soit la date/heure courante est "2024-03-18 10:00:00"
    Et le BI est à l'état "en_cours"
    Alors la couleur SLA du BI est "2"

  Scénario: Couleur SLA verte sur BI validé quelle que soit la date
    Soit la date/heure courante est "2024-03-20 10:00:00"
    Et le BI est à l'état "valide"
    Alors la couleur SLA du BI est "0"

  Scénario: Couleur SLA verte sur BI annulé
    Soit la date/heure courante est "2024-03-20 10:00:00"
    Et le BI est à l'état "annule"
    Alors la couleur SLA du BI est "0"

  # ── Priorités ─────────────────────────────────────────────────────────────

  Scénario: Les niveaux de priorité sont disponibles
    Alors les priorités disponibles incluent "0"
    Et les priorités disponibles incluent "1"
    Et les priorités disponibles incluent "2"
