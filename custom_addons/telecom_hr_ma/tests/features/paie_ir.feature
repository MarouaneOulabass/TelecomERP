# language: fr
Fonctionnalité: Calcul de l'IR sur le barème progressif marocain 2024
  En tant que gestionnaire de paie
  Je veux que l'IR soit calculé automatiquement sur le barème 2024
  Afin de garantir la conformité fiscale de chaque bulletin de paie

  # ══════════════════════════════════════════════════════════════════
  # Barème IR annuel 2024 — toutes les tranches
  # ══════════════════════════════════════════════════════════════════

  Plan du Scénario: Barème IR annuel 2024 — couverture complète de toutes les tranches
    Soit un employé sans charge de famille (1 part IR)
    Quand je calcule l'IR annuel sur "<salaire_annuel>" MAD
    Alors l'IR annuel brut est "<ir_annuel>" MAD

    Exemples: Tranche 0% (0 → 30 000 MAD)
      | salaire_annuel | ir_annuel | commentaire                   |
      | 0              | 0.00      | revenu nul                    |
      | 15000          | 0.00      | milieu tranche 0%             |
      | 30000          | 0.00      | limite haute tranche 0%       |

    Exemples: Tranche 10% (30 001 → 50 000 MAD)
      | salaire_annuel | ir_annuel | commentaire                   |
      | 30001          | 0.10      | début tranche 10%             |
      | 40000          | 1000.00   | milieu : (40000-30000)*10%    |
      | 50000          | 2000.00   | fin : (50000-30000)*10%       |

    Exemples: Tranche 20% (50 001 → 60 000 MAD)
      | salaire_annuel | ir_annuel | commentaire                          |
      | 50001          | 2000.20   | début tranche 20%                    |
      | 55000          | 3000.00   | milieu : 2000+(55000-50000)*20%      |
      | 60000          | 4000.00   | fin : 2000+(60000-50000)*20%         |

    Exemples: Tranche 30% (60 001 → 80 000 MAD)
      | salaire_annuel | ir_annuel | commentaire                                |
      | 60001          | 4000.30   | début tranche 30%                          |
      | 70000          | 7000.00   | milieu : 4000+(70000-60000)*30%            |
      | 80000          | 10000.00  | fin : 4000+2000+(80000-60000)*30%          |

    Exemples: Tranche 34% (80 001 → 180 000 MAD)
      | salaire_annuel | ir_annuel | commentaire                                      |
      | 80001          | 10000.34  | début tranche 34%                                |
      | 130000         | 27000.00  | milieu : 10000+(130000-80000)*34%                |
      | 180000         | 44000.00  | fin : 10000+(180000-80000)*34%                   |

    Exemples: Tranche 38% (> 180 000 MAD)
      | salaire_annuel | ir_annuel | commentaire                                         |
      | 180001         | 44000.38  | début tranche 38%                                   |
      | 200000         | 51600.00  | 44000+(200000-180000)*38%                           |
      | 300000         | 89600.00  | 44000+(300000-180000)*38%                           |

  # ══════════════════════════════════════════════════════════════════
  # Frais professionnels (20%, plafond 2 500 MAD/mois)
  # ══════════════════════════════════════════════════════════════════

  Plan du Scénario: Frais professionnels — 20% plafonné à 2 500 MAD/mois
    Soit un bulletin avec un salaire net imposable mensuel de "<sni>" MAD
    Alors les frais professionnels sont "<frais_pro>" MAD

    Exemples:
      | sni    | frais_pro | commentaire                          |
      | 4000   | 800.00    | 4000 × 20% = 800 (sous plafond)      |
      | 10000  | 2000.00   | 10000 × 20% = 2000 (sous plafond)    |
      | 12500  | 2500.00   | 12500 × 20% = 2500 (limite exacte)   |
      | 15000  | 2500.00   | 15000 × 20% = 3000 → plafonné 2500   |
      | 20000  | 2500.00   | toujours plafonné                    |
      | 50000  | 2500.00   | cadre supérieur : toujours 2500 max  |

  # ══════════════════════════════════════════════════════════════════
  # Déductions charges de famille (30 MAD/mois par charge hors 1ère part)
  # ══════════════════════════════════════════════════════════════════

  Plan du Scénario: Déductions IR pour charges de famille
    Soit un bulletin donnant un IR mensuel brut de "1000" MAD
    Et l'employé a "<parts_ir>" parts IR
    Alors l'IR mensuel net est "<ir_net>" MAD

    Exemples:
      | parts_ir | ir_net  | commentaire                         |
      | 1        | 1000.00 | célibataire — 0 déduction           |
      | 1.5      | 985.00  | 0.5 part → 0.5 × 30 = 15 MAD déduits (époux) |
      | 2        | 970.00  | 1 part supp → 30 MAD déduits        |
      | 3        | 940.00  | 2 parts supp → 60 MAD déduits       |
      | 4        | 910.00  | 3 parts supp → 90 MAD déduits       |
      | 5        | 880.00  | 4 parts supp → 120 MAD déduits      |

  Scénario: IR mensuel net ne peut pas être négatif (nombreuses charges)
    Soit un bulletin donnant un IR mensuel brut de "10" MAD
    Et l'employé a "20" parts IR
    Alors l'IR mensuel net est "0.00" MAD

  # ══════════════════════════════════════════════════════════════════
  # Calcul intégré du net imposable IR
  # ══════════════════════════════════════════════════════════════════

  Scénario: Salaire net imposable = brut - cotisations salariales + avantages en nature
    Soit un bulletin avec :
      | salaire_base           | 10000 |
      | cnss_salarie          | 268.80 |
      | amo_salarie           | 226.00 |
      | cimr_salarie          | 300.00 |
      | avantages_en_nature   | 500.00 |
    Alors le salaire net imposable est "9705.20" MAD

  Scénario: Salaire imposable IR = net imposable - frais pro - indemnités de déplacement
    Soit un bulletin avec :
      | salaire_net_imposable   | 9705.20 |
      | frais_pro               | 1941.04 |
      | indemnite_deplacement   | 500.00  |
    Alors le salaire imposable IR est "7264.16" MAD
