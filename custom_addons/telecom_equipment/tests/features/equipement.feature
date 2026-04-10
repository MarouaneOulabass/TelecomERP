# language: fr
Fonctionnalité: Gestion du cycle de vie des équipements télécom
  En tant que responsable logistique
  Je veux tracer chaque équipement de la réception à la mise au rebut
  Afin de maintenir un inventaire fiable de l'infrastructure déployée

  Contexte:
    Soit une catégorie d'équipement "Antenne 4G" existe
    Et un site "Site Équipement Test" avec le code "EQ-SITE-001" existe

  # ── Cycle de vie équipement ──────────────────────────────────────────────

  Scénario: Création d'un équipement avec numéro de série unique
    Quand je crée un équipement "Antenne Huawei AAU5614" avec le N° série "SN-2024-001"
    Alors l'équipement est créé avec succès
    Et l'état de l'équipement est "en_stock"

  Scénario: Numéro de série unique par équipement — doublon refusé
    Soit un équipement avec le N° série "SN-UNIQUE-001" existe déjà
    Quand je tente de créer un équipement avec le même N° série "SN-UNIQUE-001"
    Alors une erreur d'intégrité est levée

  Plan du Scénario: Toutes les transitions du cycle de vie sont possibles
    Soit un équipement à l'état "<etat_initial>" existe
    Quand je passe l'équipement à l'état "<etat_final>"
    Alors l'état de l'équipement est "<etat_final>"

    Exemples:
      | etat_initial  | etat_final    |
      | en_stock      | installe      |
      | installe      | en_panne      |
      | en_panne      | en_reparation |
      | en_reparation | installe      |
      | installe      | retire        |
      | retire        | mis_au_rebut  |

  # ── Garantie ──────────────────────────────────────────────────────────────

  Scénario: Alerte garantie expirant dans moins de 60 jours
    Soit la date du jour est "2024-03-01"
    Et un équipement avec une date de fin de garantie "2024-04-15" existe
    Alors l'alerte de fin de garantie est active

  Scénario: Pas d'alerte garantie si expiration dans plus de 90 jours
    Soit la date du jour est "2024-03-01"
    Et un équipement avec une date de fin de garantie "2025-01-01" existe
    Alors l'alerte de fin de garantie est inactive

  # ── Outillages ───────────────────────────────────────────────────────────

  Scénario: Création d'un outillage avec date d'étalonnage
    Quand je crée un outillage "OTDR Yokogawa AQ7280" avec numéro "OTDR-001"
    Et la prochaine date d'étalonnage est "2024-12-31"
    Alors l'outillage est créé avec succès

  Scénario: Alerte étalonnage — outillage non étalonné depuis plus d'un an
    Soit la date du jour est "2025-01-15"
    Et un outillage avec dernière date d'étalonnage "2024-01-01" existe
    Alors l'alerte d'étalonnage est active
