# language: fr
Fonctionnalité: Prime d'ancienneté selon le droit du travail marocain
  En tant que gestionnaire RH
  Je veux calculer la prime d'ancienneté selon les paliers légaux marocains
  Afin d'appliquer les taux corrects en fonction de l'ancienneté réelle

  # ══════════════════════════════════════════════════════════════════
  # Barème légal marocain d'ancienneté
  # ══════════════════════════════════════════════════════════════════

  Plan du Scénario: Barème d'ancienneté — tous les paliers légaux
    Soit un employé embauché il y a "<anciennete_annees>" années
    Et un bulletin avec un salaire de base de "10000" MAD
    Quand je calcule la prime d'ancienneté
    Alors la prime d'ancienneté est "<prime>" MAD

    Exemples: Palier 0% — Moins de 2 ans
      | anciennete_annees | prime   | taux | règle_légale            |
      | 0                 | 0.00    | 0%   | moins de 2 ans : 0%     |
      | 0.5               | 0.00    | 0%   | 6 mois : 0%             |
      | 1                 | 0.00    | 0%   | 1 an : 0%               |
      | 1.99              | 0.00    | 0%   | juste sous 2 ans : 0%   |

    Exemples: Palier 5% — De 2 à 5 ans
      | anciennete_annees | prime   | taux | règle_légale            |
      | 2                 | 500.00  | 5%   | exactement 2 ans : 5%   |
      | 3                 | 500.00  | 5%   | 3 ans : 5%              |
      | 4.5               | 500.00  | 5%   | 4.5 ans : 5%            |
      | 4.99              | 500.00  | 5%   | juste sous 5 ans : 5%   |

    Exemples: Palier 10% — De 5 à 12 ans
      | anciennete_annees | prime    | taux  | règle_légale            |
      | 5                 | 1000.00  | 10%   | exactement 5 ans : 10%  |
      | 8                 | 1000.00  | 10%   | 8 ans : 10%             |
      | 11                | 1000.00  | 10%   | 11 ans : 10%            |
      | 11.99             | 1000.00  | 10%   | juste sous 12 ans : 10% |

    Exemples: Palier 15% — De 12 à 20 ans
      | anciennete_annees | prime    | taux  | règle_légale            |
      | 12                | 1500.00  | 15%   | exactement 12 ans : 15% |
      | 15                | 1500.00  | 15%   | 15 ans : 15%            |
      | 19                | 1500.00  | 15%   | 19 ans : 15%            |
      | 19.99             | 1500.00  | 15%   | juste sous 20 ans : 15% |

    Exemples: Palier 20% — Plus de 20 ans
      | anciennete_annees | prime    | taux  | règle_légale            |
      | 20                | 2000.00  | 20%   | exactement 20 ans : 20% |
      | 25                | 2000.00  | 20%   | 25 ans : 20%            |
      | 35                | 2000.00  | 20%   | 35 ans : 20%            |

  # ══════════════════════════════════════════════════════════════════
  # Cas particuliers
  # ══════════════════════════════════════════════════════════════════

  Scénario: Prime calculée proportionnellement au salaire de base
    Soit un employé avec "10" ans d'ancienneté (taux 10%)
    Et un bulletin avec un salaire de base de "15000" MAD
    Alors la prime d'ancienneté est "1500.00" MAD

  Scénario: Prime = 0 si employé sans date d'embauche
    Soit un employé sans date d'embauche renseignée
    Et un bulletin avec un salaire de base de "10000" MAD
    Quand je calcule la prime d'ancienneté
    Alors la prime d'ancienneté est "0.00" MAD

  Scénario: Prime non calculée si bulletin sans employé
    Soit un bulletin sans employé rattaché
    Quand je calcule la prime d'ancienneté
    Alors la prime d'ancienneté est "0.00" MAD
