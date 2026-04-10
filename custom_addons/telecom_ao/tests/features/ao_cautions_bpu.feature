# language: fr
Fonctionnalité: Cautions bancaires et Bordereau de Prix Unitaires (BPU)
  En tant que chargé d'affaires
  Je veux calculer automatiquement les cautions réglementaires et le total BPU
  Afin de respecter les exigences CCAG des marchés publics marocains

  # ── Cautions bancaires ───────────────────────────────────────────────────

  Plan du Scénario: Caution provisoire = 1,5% du montant soumissionné
    Soit un AO avec un montant soumissionné de "<montant>" MAD
    Alors la caution provisoire calculée est "<caution>" MAD

    Exemples:
      | montant   | caution   | commentaire               |
      | 100000    | 1500.00   | 100000 × 1.5%             |
      | 500000    | 7500.00   | 500000 × 1.5%             |
      | 1000000   | 15000.00  | 1 million × 1.5%          |
      | 3000000   | 45000.00  | 3 millions × 1.5%         |
      | 0         | 0.00      | montant nul → caution nulle |

  Plan du Scénario: Caution définitive = 3% du montant soumissionné
    Soit un AO avec un montant soumissionné de "<montant>" MAD
    Alors la caution définitive calculée est "<caution>" MAD

    Exemples:
      | montant   | caution  | commentaire               |
      | 100000    | 3000.00  | 100000 × 3%               |
      | 500000    | 15000.00 | 500000 × 3%               |
      | 1000000   | 30000.00 | 1 million × 3%            |
      | 0         | 0.00     | montant nul → caution nulle |

  Scénario: Les deux cautions cohérentes — définitive = 2 × provisoire
    Soit un AO avec un montant soumissionné de "2000000" MAD
    Alors la caution provisoire calculée est "30000.00" MAD
    Et la caution définitive calculée est "60000.00" MAD

  Scénario: Cautions recalculées automatiquement à la modification du montant
    Soit un AO avec un montant soumissionné de "500000" MAD
    Quand je modifie le montant soumissionné à "800000" MAD
    Alors la caution provisoire calculée est "12000.00" MAD
    Et la caution définitive calculée est "24000.00" MAD

  # ── BPU ──────────────────────────────────────────────────────────────────

  Scénario: Total BPU = somme de toutes les lignes
    Soit un AO avec 3 lignes BPU de montants "10000", "25000" et "15000" MAD
    Alors le total BPU HT est "50000.00" MAD

  Scénario: Total BPU mis à jour à l'ajout d'une ligne
    Soit un AO avec un total BPU de "50000" MAD
    Quand j'ajoute une ligne BPU de "20000" MAD
    Alors le total BPU HT est "70000.00" MAD

  Scénario: Total BPU = 0 si aucune ligne BPU
    Soit un AO sans lignes BPU
    Alors le total BPU HT est "0.00" MAD

  Scénario: Compteur lignes BPU correct
    Soit un AO avec 3 lignes BPU de montants "10000", "25000" et "15000" MAD
    Alors le nombre de lignes BPU est "3"
