# language: fr
Fonctionnalité: Avances de démarrage et situations de travaux (CCAG Maroc)
  En tant que responsable financier
  Je veux gérer les avances de démarrage et les situations de travaux
  Afin de suivre le cycle financier complet d'un marché public

  Contexte:
    Soit un projet "Déploiement FTTH Rabat" existe
    Et un contrat "CONT-AV-001" lié à ce projet existe
    Et un client "Inwi" de type "operator" existe

  # ── Avance de démarrage ──────────────────────────────────────────────────

  Plan du Scénario: Montant avance théorique = montant marché × taux
    Soit une avance de démarrage avec un montant marché de "<marche>" MAD et un taux de "<taux>%"
    Alors le montant d'avance théorique est "<avance>" MAD

    Exemples: Taux standards CCAG
      | marche    | taux | avance     | commentaire         |
      | 1000000   | 10   | 100000.00  | taux standard 10%   |
      | 1000000   | 15   | 150000.00  | taux majoré 15%     |
      | 500000    | 10   | 50000.00   | marché 500K          |

  Scénario: Workflow avance — en_attente → versée → en cours de remboursement
    Soit une avance de démarrage en attente de versement
    Et le montant versé est "100000" MAD le "2024-02-01"
    Quand je marque l'avance comme versée
    Alors l'état de l'avance est "verse"
    Quand je démarre le remboursement de l'avance
    Alors l'état de l'avance est "en_cours_remboursement"

  # ── Situation de travaux ─────────────────────────────────────────────────

  Scénario: Montant situation HT = avancement cumulé × montant marché - situations précédentes
    Soit une situation de travaux avec :
      | montant_marche_ht            | 1000000 |
      | taux_avancement_cumul        | 40      |
      | montant_situation_precedente | 200000  |
    Alors le montant situation HT est "200000.00" MAD

  Scénario: Net à payer situation = TTC - retenue garantie - avance remboursement
    Soit une situation de travaux avec :
      | montant_marche_ht            | 1000000 |
      | taux_avancement_cumul        | 30      |
      | montant_situation_precedente | 0       |
      | retenue_garantie_taux        | 10      |
      | avance_remboursement         | 20000   |
    Alors le montant situation HT est "300000.00" MAD
    Et la retenue de garantie situation est "30000.00" MAD
    Et le net à payer situation est "310000.00" MAD
