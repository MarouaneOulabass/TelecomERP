# language: fr
Fonctionnalité: Calcul des cotisations CNSS et AMO (législation marocaine 2024)
  En tant que gestionnaire de paie
  Je veux que CNSS et AMO soient calculés automatiquement et exactement
  Afin de garantir la conformité des bulletins avec la législation marocaine

  Contexte:
    Soit un employé "Mohammed Alami" avec un taux CIMR salarié de "3%" et patronal de "3.5%" existe

  # ══════════════════════════════════════════════════════════════════
  # CNSS — Plafond mensuel 6 000 MAD — Taux 4,48% salarié / 10,64% patronal
  # ══════════════════════════════════════════════════════════════════

  Plan du Scénario: CNSS salarié selon salaire — plafond 6 000 MAD
    Soit un bulletin de paie avec un salaire de base de "<salaire>" MAD
    Alors la base CNSS est "<base_cnss>" MAD
    Et le CNSS salarié est "<cnss_sal>" MAD

    Exemples: Cas CNSS salarié
      | salaire | base_cnss | cnss_sal | note                              |
      | 3000    | 3000.00   | 134.40   | sous plafond : 3000 × 4.48%       |
      | 4000    | 4000.00   | 179.20   | sous plafond : 4000 × 4.48%       |
      | 6000    | 6000.00   | 268.80   | au plafond exact : 6000 × 4.48%   |
      | 8000    | 6000.00   | 268.80   | au-delà : base plafonnée à 6000   |
      | 12000   | 6000.00   | 268.80   | très au-delà : toujours 6000 max  |
      | 25000   | 6000.00   | 268.80   | salaire cadre : base = 6000       |

  Plan du Scénario: CNSS patronal selon salaire — plafond 6 000 MAD
    Soit un bulletin de paie avec un salaire de base de "<salaire>" MAD
    Alors le CNSS patronal est "<cnss_pat>" MAD

    Exemples: Cas CNSS patronal
      | salaire | cnss_pat | note                              |
      | 3000    | 319.20   | 3000 × 10.64%                     |
      | 6000    | 638.40   | 6000 × 10.64%                     |
      | 10000   | 638.40   | plafond : toujours 6000 × 10.64%  |

  # ══════════════════════════════════════════════════════════════════
  # AMO — Sans plafond — Taux 2,26% salarié / 3,96% patronal
  # ══════════════════════════════════════════════════════════════════

  Plan du Scénario: AMO salarié calculé sur salaire brut sans plafond
    Soit un bulletin de paie avec un salaire de base de "<salaire>" MAD
    Alors l'AMO salarié est "<amo_sal>" MAD

    Exemples: Cas AMO salarié
      | salaire | amo_sal  | note                         |
      | 4000    | 90.40    | 4000 × 2.26%                 |
      | 6000    | 135.60   | 6000 × 2.26% (pas de plafond)|
      | 10000   | 226.00   | 10000 × 2.26%                |
      | 15000   | 339.00   | 15000 × 2.26%                |
      | 20000   | 452.00   | 20000 × 2.26%                |
      | 50000   | 1130.00  | 50000 × 2.26% — cadre supérieur |

  Plan du Scénario: AMO patronal calculé sur salaire brut sans plafond
    Soit un bulletin de paie avec un salaire de base de "<salaire>" MAD
    Alors l'AMO patronal est "<amo_pat>" MAD

    Exemples: Cas AMO patronal
      | salaire | amo_pat  | note          |
      | 4000    | 158.40   | 4000 × 3.96%  |
      | 10000   | 396.00   | 10000 × 3.96% |
      | 20000   | 792.00   | 20000 × 3.96% |

  Scénario: AMO calculé sur le salaire total y compris au-delà du plafond CNSS
    Soit un bulletin de paie avec un salaire de base de "20000" MAD
    Alors la base CNSS est "6000.00" MAD
    Et l'AMO salarié est "452.00" MAD
    Et l'AMO patronal est "792.00" MAD

  # ══════════════════════════════════════════════════════════════════
  # CIMR — Taux variable par employé
  # ══════════════════════════════════════════════════════════════════

  Scénario: CIMR salarié calculé sur salaire brut au taux de l'employé
    Soit un bulletin de paie avec un salaire de base de "10000" MAD
    Et l'employé a un taux CIMR salarié de "3%"
    Alors le CIMR salarié est "300.00" MAD

  Scénario: CIMR patronal calculé sur salaire brut au taux patronal
    Soit un bulletin de paie avec un salaire de base de "10000" MAD
    Et l'employé a un taux CIMR patronal de "3.5%"
    Alors le CIMR patronal est "350.00" MAD

  Scénario: CIMR = 0 si taux non défini
    Soit un bulletin de paie avec un salaire de base de "10000" MAD
    Et l'employé n'a pas de taux CIMR défini
    Alors le CIMR salarié est "0.00" MAD
    Et le CIMR patronal est "0.00" MAD

  # ══════════════════════════════════════════════════════════════════
  # Net à payer — formule complète
  # ══════════════════════════════════════════════════════════════════

  Scénario: Net à payer ne peut pas être négatif
    Soit un bulletin de paie avec un salaire de base de "1" MAD
    Alors le net à payer est "0.94" MAD

  Scénario: Workflow bulletin — draft → confirmé → validé → payé
    Soit un bulletin de paie en brouillon avec un salaire de base de "5000" MAD
    Quand je confirme le bulletin
    Alors l'état du bulletin est "confirme"
    Et le numéro de séquence est renseigné
    Quand je valide le bulletin
    Alors l'état du bulletin est "valide"
    Quand je marque le bulletin comme payé
    Alors l'état du bulletin est "paye"

  Scénario: Un seul bulletin par employé par mois — doublon refusé
    Soit un bulletin confirmé pour "Mohammed Alami" pour la période de "2024-03-01"
    Quand je tente de créer un second bulletin pour "Mohammed Alami" pour la période de "2024-03-01"
    Alors une erreur d'intégrité est levée

  Scénario: Salaire de base négatif refusé
    Quand je tente de créer un bulletin avec un salaire de "-100" MAD
    Alors une erreur de validation est levée indiquant "négatif"
