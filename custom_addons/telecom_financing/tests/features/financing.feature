# language: fr
Fonctionnalité: Gestion des coûts financiers projet
  En tant que chargé d'affaires
  Je veux saisir les coûts financiers liés aux projets
  Afin de calculer la rentabilité réelle incluant les frais financiers

  Contexte:
    Soit un projet "Rollout 4G Rabat" existe
    Et un lot "Lot Nord" existe pour ce projet

  Scénario: Création d'un coût financier
    Quand je crée un coût financier de 100000.00 MAD de type "credit_bancaire" pour ce projet
    Alors le coût financier est créé avec succès

  Scénario: Calcul des intérêts sur la durée
    Quand je crée un coût financier de 200000.00 MAD à 5.5% du "2026-01-01" au "2026-12-31" pour ce projet
    Alors le montant des intérêts est d'environ 11000.00 MAD

  Scénario: Création automatique d'une écriture de coût
    Quand je crée un coût financier de 50000.00 MAD de type "leasing" pour ce projet
    Alors une écriture de coût financier est créée automatiquement

  Scénario: Montant négatif refusé
    Quand je tente de créer un coût financier de -10000.00 MAD de type "credit_bancaire" pour ce projet
    Alors une erreur de validation est levée indiquant "positif"

  Scénario: Types de financement disponibles
    Alors les types de financement suivants sont disponibles
      | type                 |
      | credit_bancaire      |
      | leasing              |
      | caution_provisoire   |
      | caution_definitive   |
      | avance_client        |
      | escompte             |
      | autre                |

  Scénario: L'écriture de coût contient le principal plus les intérêts
    Quand je crée un coût financier de 100000.00 MAD à 6.0% du "2026-01-01" au "2026-12-31" pour ce projet
    Alors une écriture de coût financier est créée automatiquement
    Et le montant de l'écriture de coût inclut les intérêts

  Scénario: Taux d'intérêt à zéro donne zéro intérêts
    Quand je crée un coût financier de 50000.00 MAD à 0.0% du "2026-01-01" au "2026-06-30" pour ce projet
    Alors le montant des intérêts est d'environ 0.00 MAD
