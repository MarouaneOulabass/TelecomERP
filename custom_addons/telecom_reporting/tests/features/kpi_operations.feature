# language: fr
Fonctionnalité: KPI opérationnels — cohérence des vues d'analyse
  En tant que directeur des opérations
  Je veux consulter des KPI fiables sur les interventions et les sites
  Afin de piloter la performance terrain et identifier les zones à risque

  Contexte:
    Soit un site "Site KPI Test" avec le code "KPI-001" dans la wilaya "casablanca_settat" existe

  # ── Vue intervention analysis ─────────────────────────────────────────────

  Scénario: La vue d'analyse interventions reflète le nombre réel d'interventions
    Soit "3" interventions terminées existent sur le site "KPI-001"
    Alors la vue d'analyse interventions retourne "3" lignes pour le site "KPI-001"

  Scénario: Une intervention annulée n'est pas comptabilisée dans la vue
    Soit "2" interventions terminées et "1" annulée existent sur le site "KPI-001"
    Alors la vue d'analyse interventions retourne "2" lignes pour le site "KPI-001"

  Scénario: Le champ sla_depasse est correctement agrégé dans la vue
    Soit "3" interventions dont "1" avec SLA dépassé existent sur le site "KPI-001"
    Alors la vue d'analyse retourne "1" SLA dépassé pour le site "KPI-001"

  Scénario: La durée réelle est exposée dans la vue d'analyse
    Soit une intervention avec "4.5" heures de durée réelle existe sur le site "KPI-001"
    Alors la vue d'analyse expose une durée de "4.5" heures pour cette intervention

  # ── Vue site analysis ─────────────────────────────────────────────────────

  Scénario: La vue d'analyse sites reflète le nombre total d'interventions
    Soit "2" interventions existent sur le site "KPI-001"
    Alors la vue d'analyse sites indique "2" interventions totales pour "KPI-001"

  Scénario: Un site sans intervention a un compteur à 0
    Soit le site "KPI-001" n'a aucune intervention
    Alors la vue d'analyse sites indique "0" interventions totales pour "KPI-001"

  Scénario: Le type de site est exposé dans la vue d'analyse sites
    Alors la vue d'analyse sites expose le type du site "KPI-001"

  Scénario: La wilaya est correctement exposée dans la vue d'analyse sites
    Alors la vue d'analyse sites expose la wilaya "casablanca_settat" pour "KPI-001"

  # ── Cohérence multi-sites ─────────────────────────────────────────────────

  Scénario: Les interventions de deux sites distincts sont séparées dans la vue
    Soit un second site "Site KPI Test 2" avec le code "KPI-002" existe
    Et "2" interventions existent sur le site "KPI-001"
    Et "3" interventions existent sur le site "KPI-002"
    Alors la vue d'analyse sites indique "2" interventions totales pour "KPI-001"
    Et la vue d'analyse sites indique "3" interventions totales pour "KPI-002"
