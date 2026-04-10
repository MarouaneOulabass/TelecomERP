# language: fr
Fonctionnalité: Localisation fiscale marocaine — TVA et Retenue à la Source
  En tant que comptable
  Je veux que les taux TVA marocains et la RAS soient correctement paramétrés
  Afin de garantir la conformité fiscale des factures

  # ══════════════════════════════════════════════════════════════════
  # TVA — Taux marocains
  # ══════════════════════════════════════════════════════════════════

  Scénario: Les 5 taux de TVA marocains sont disponibles
    Alors les taux de TVA disponibles incluent "20%"
    Et les taux de TVA disponibles incluent "14%"
    Et les taux de TVA disponibles incluent "10%"
    Et les taux de TVA disponibles incluent "7%"
    Et les taux de TVA disponibles incluent "0%"

  Scénario: TVA standard 20% applicable aux prestations de services télécom
    Soit une taxe TVA à "20%" existe dans le système
    Quand je l'applique sur un montant HT de "10000" MAD
    Alors le montant de TVA est "2000.00" MAD
    Et le montant TTC est "12000.00" MAD

  Scénario: TVA 14% applicable au transport
    Soit une taxe TVA à "14%" existe dans le système
    Quand je l'applique sur un montant HT de "5000" MAD
    Alors le montant de TVA est "700.00" MAD
    Et le montant TTC est "5700.00" MAD

  Scénario: TVA 10% applicable à certains travaux
    Soit une taxe TVA à "10%" existe dans le système
    Quand je l'applique sur un montant HT de "8000" MAD
    Alors le montant de TVA est "800.00" MAD
    Et le montant TTC est "8800.00" MAD

  Scénario: TVA 7% applicable à l'eau et l'électricité
    Soit une taxe TVA à "7%" existe dans le système
    Quand je l'applique sur un montant HT de "12000" MAD
    Alors le montant de TVA est "840.00" MAD
    Et le montant TTC est "12840.00" MAD

  Scénario: TVA 0% pour opérations exonérées (export)
    Soit une taxe TVA à "0%" existe dans le système
    Quand je l'applique sur un montant HT de "50000" MAD
    Alors le montant de TVA est "0.00" MAD
    Et le montant TTC est "50000.00" MAD

  # ══════════════════════════════════════════════════════════════════
  # Retenue à la Source (RAS) — 10% sur prestations de services
  # ══════════════════════════════════════════════════════════════════

  Scénario: RAS 10% appliquée sur une facture fournisseur prestation de services
    Soit une facture fournisseur HT de "10000" MAD avec RAS 10%
    Alors la RAS est "1000.00" MAD
    Et le net à payer au fournisseur est "9000.00" MAD (avant TVA)

  Scénario: RAS calculée sur la base HT (avant TVA)
    Soit une facture fournisseur HT de "20000" MAD TVA 20% avec RAS 10%
    Alors la RAS est calculée sur "20000" MAD (base HT)
    Et la RAS est "2000.00" MAD

  # ══════════════════════════════════════════════════════════════════
  # Mentions obligatoires factures
  # ══════════════════════════════════════════════════════════════════

  Scénario: Vérification des mentions légales marocaines obligatoires sur facture
    Soit une facture client créée avec tous les champs légaux
    Alors la facture contient l'ICE de l'émetteur
    Et la facture contient l'ICE du client
    Et la facture contient l'Identifiant Fiscal (IF)
    Et la facture contient le numéro RC

  # ══════════════════════════════════════════════════════════════════
  # Devise MAD par défaut
  # ══════════════════════════════════════════════════════════════════

  Scénario: La devise MAD est définie dans le système
    Alors la devise "MAD" existe dans le système
    Et la devise "MAD" est définie comme "Dirham Marocain"
