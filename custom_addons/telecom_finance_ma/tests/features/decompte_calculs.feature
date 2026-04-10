# language: fr
Fonctionnalité: Calculs financiers du décompte CCAG Travaux (Maroc)
  En tant que responsable financier
  Je veux que les décomptes soient calculés automatiquement selon le CCAG Travaux marocain
  Afin de garantir l'exactitude de chaque règlement de marché public

  Contexte:
    Soit un projet "Déploiement 4G Grand Casablanca" existe
    Et un contrat "CONT-2024-001" lié à ce projet existe
    Et un client "Maroc Telecom" de type "operator" existe

  # ── Total HT cumulé ──────────────────────────────────────────────────────

  Plan du Scénario: Total HT cumulé = travaux + supplémentaires + révisions de prix
    Soit un décompte avec :
      | travaux_ht                    | <travaux>      |
      | travaux_supplementaires       | <supplementaires> |
      | montant_revisions_prix        | <revisions>    |
    Alors le total HT cumulé est "<total>" MAD

    Exemples:
      | travaux    | supplementaires | revisions | total      |
      | 500000     | 0               | 0         | 500000.00  |
      | 500000     | 50000           | 0         | 550000.00  |
      | 500000     | 50000           | 10000     | 560000.00  |
      | 400000     | 0               | 0         | 400000.00  |

  # ── Retenue de garantie ──────────────────────────────────────────────────

  Plan du Scénario: Retenue de garantie cumulée selon le taux contractuel
    Soit un décompte avec un total HT cumulé de "<total_ht>" MAD
    Et un taux de retenue de garantie de "<taux_rg>%"
    Alors la retenue de garantie cumulée est "<rg>" MAD

    Exemples: Taux standard CCAG 10%
      | total_ht  | taux_rg | rg       | commentaire    |
      | 500000    | 10      | 50000.00 | standard CCAG  |
      | 1000000   | 10      | 100000.00| 1M × 10%       |
      | 200000    | 10      | 20000.00 | 200K × 10%     |

    Exemples: Taux réduit contractuel 5%
      | total_ht  | taux_rg | rg       | commentaire         |
      | 500000    | 5       | 25000.00 | contrat spécifique  |
      | 1000000   | 5       | 50000.00 | 1M × 5%             |

  # ── Base TVA ─────────────────────────────────────────────────────────────

  Scénario: Base TVA = total HT - RG - avance - situations antérieures
    Soit un décompte avec :
      | total_ht_cumul           | 500000 |
      | retenue_garantie_cumul   | 50000  |
      | avance_periode           | 30000  |
      | situations_anterieures   | 100000 |
    Alors la base TVA est "320000.00" MAD

  Scénario: Base TVA sans déductions = total HT cumulé
    Soit un décompte avec un total HT cumulé de "300000" MAD sans déductions
    Alors la base TVA est "300000.00" MAD

  # ── TVA ──────────────────────────────────────────────────────────────────

  Plan du Scénario: TVA calculée sur la base TVA
    Soit un décompte avec une base TVA de "<base>" MAD et un taux TVA de "<taux>%"
    Alors la TVA est "<tva>" MAD

    Exemples:
      | base    | taux | tva      |
      | 90000   | 20   | 18000.00 |
      | 100000  | 14   | 14000.00 |
      | 80000   | 10   | 8000.00  |

  # ── RAS ──────────────────────────────────────────────────────────────────

  Plan du Scénario: RAS 10% calculée sur la base HT (pratique marocaine)
    Soit un décompte avec une base TVA de "<base>" MAD
    Alors la RAS est "<ras>" MAD
    Et le net après RAS est "<net_ras>" MAD

    Exemples:
      | base    | ras      | net_ras   | commentaire            |
      | 90000   | 9000.00  | 99000.00  | 90000+TVA-RAS          |
      | 100000  | 10000.00 | 110000.00 | base large             |
      | 50000   | 5000.00  | 55000.00  | base médiane           |

  # ── Net à régler ─────────────────────────────────────────────────────────

  Scénario: Net à régler = base TVA + TVA
    Soit un décompte avec une base TVA de "90000" MAD et TVA de "18000" MAD
    Alors le net à régler est "108000.00" MAD

  Scénario: Net après RAS = net à régler - RAS
    Soit un décompte avec un net à régler de "108000" MAD et une RAS de "9000" MAD
    Alors le net après RAS est "99000.00" MAD
