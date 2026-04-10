# language: fr
Fonctionnalité: KPI commerciaux — cohérence des vues d'analyse AO et contrats
  En tant que directeur commercial
  Je veux des KPI fiables sur le pipeline AO et les contrats actifs
  Afin de piloter l'activité commerciale et les encours financiers

  # ── Cohérence pipeline AO ────────────────────────────────────────────────

  Scénario: Compter les AO par état
    Soit "2" AO à l'état "detecte" existent
    Et "3" AO à l'état "soumis" existent
    Et "1" AO à l'état "gagne" existe
    Alors le nombre d'AO détectés est "2"
    Et le nombre d'AO soumis est "3"
    Et le nombre d'AO gagnés est "1"

  Scénario: Taux de succès AO — gagné / (gagné + perdu) hors en-cours
    Soit "4" AO à l'état "gagne" existent
    Et "1" AO à l'état "perdu" existe
    Alors le taux de succès AO est de "80" %

  Scénario: Un AO abandonné n'est pas comptabilisé dans le taux de succès
    Soit "3" AO à l'état "gagne" existent
    Et "1" AO à l'état "perdu" existe
    Et "5" AO à l'état "abandonne" existent
    Alors le taux de succès AO est de "75" %

  # ── Cohérence contrats ────────────────────────────────────────────────────

  Scénario: Compter les contrats actifs par type
    Soit "2" contrats actifs de type "maintenance" existent
    Et "1" contrat actif de type "deploiement" existe
    Alors le nombre de contrats actifs est "3"

  Scénario: Un contrat résilié n'est pas comptabilisé parmi les actifs
    Soit "2" contrats actifs de type "maintenance" existent
    Et "1" contrat de type "maintenance" à l'état "resilie" existe
    Alors le nombre de contrats actifs est "2"

  Scénario: Montant total sous contrat actif
    Soit un contrat actif de type "cadre_operateur" avec un montant de "500000" MAD existe
    Et un contrat actif de type "maintenance" avec un montant de "200000" MAD existe
    Alors le montant total des contrats actifs est d'au moins "700000" MAD

  # ── Alertes à horizon ────────────────────────────────────────────────────

  Scénario: Détection des contrats actifs expirant dans les 90 jours
    Soit la date du jour est "2024-03-01"
    Et un contrat actif avec date de fin "2024-05-15" existe
    Et un contrat actif avec date de fin "2025-06-01" existe
    Alors le nombre de contrats avec alerte d'expiration est "1"

  Scénario: Les contrats sans date de fin ne génèrent pas d'alerte
    Soit la date du jour est "2024-03-01"
    Et un contrat actif sans date de fin existe
    Alors le nombre de contrats avec alerte d'expiration est "0"
