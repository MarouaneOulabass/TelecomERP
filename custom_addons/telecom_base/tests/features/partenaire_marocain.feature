# language: fr
Fonctionnalité: Gestion des partenaires avec champs légaux marocains
  En tant qu'administrateur
  Je veux gérer les tiers avec les identifiants légaux marocains
  Afin de respecter les obligations fiscales et administratives

  # ── Types de partenaires télécom ─────────────────────────────────────────

  Scénario: Les types de partenaires télécom sont disponibles
    Alors les types de partenaires disponibles incluent "operator"
    Et les types de partenaires disponibles incluent "lessor"
    Et les types de partenaires disponibles incluent "public_org"
    Et les types de partenaires disponibles incluent "subcontractor"

  Scénario: Création d'un partenaire opérateur télécom
    Quand je crée un partenaire "Orange Maroc" de type "operator" avec l'ICE "001234567890123"
    Alors le partenaire est créé avec succès
    Et l'ICE du partenaire est "001234567890123"

  Scénario: Création d'un partenaire bailleur de site
    Quand je crée un partenaire "Propriétaire Immo SA" de type "lessor"
    Alors le partenaire est créé avec succès
    Et le type de partenaire est "lessor"

  # ── Validation ICE ───────────────────────────────────────────────────────

  Plan du Scénario: ICE doit contenir exactement 15 chiffres
    Quand je tente de créer un partenaire avec l'ICE "<ice>"
    Alors <resultat>

    Exemples: ICE valides
      | ice             | resultat                         |
      | 001234567890123 | le partenaire est créé avec succès |
      | 999999999999999 | le partenaire est créé avec succès |

    Exemples: ICE invalides — trop court
      | ice            | resultat                                              |
      | 12345          | une erreur de validation est levée indiquant "ICE"    |
      | 00123456789012 | une erreur de validation est levée indiquant "ICE"    |

    Exemples: ICE invalides — trop long
      | ice              | resultat                                              |
      | 0012345678901234 | une erreur de validation est levée indiquant "ICE"    |

    Exemples: ICE invalides — lettres
      | ice             | resultat                                              |
      | 00123456789012A | une erreur de validation est levée indiquant "ICE"    |

  # ── Certifications partenaires ───────────────────────────────────────────

  Scénario: Suivi des certifications et agréments d'un partenaire
    Soit un partenaire "Prestataire Technique SARL" existe
    Quand j'ajoute la certification "Agrément ANRT" avec date d'expiration "2025-12-31" au partenaire
    Alors la certification est enregistrée
    Et la date d'expiration est "2025-12-31"

  Scénario: Alerte certification expirée
    Soit la date du jour est "2026-01-01"
    Et un partenaire avec une certification expirée le "2025-12-31" existe
    Alors la certification est à l'état "expired"

  # ── Champs légaux IF / RC / Patente ──────────────────────────────────────

  Scénario: Enregistrement des identifiants fiscaux marocains complets
    Quand je crée un partenaire "Prestataire Test SARL" avec les champs légaux :
      | ice     | 001234567890123 |
      | if      | 12345678        |
      | rc      | RC-CASA-12345   |
      | patente | 87654321        |
    Alors le partenaire est créé avec succès
    Et l'IF du partenaire est "12345678"
    Et le RC du partenaire est "RC-CASA-12345"

  # ── Sous-traitants et spécialités ───────────────────────────────────────

  Scénario: Création d'un sous-traitant avec spécialités techniques
    Soit une spécialité "Fibre optique" existe
    Et une spécialité "Courant faible" existe
    Quand je crée un partenaire sous-traitant "ElecTech SARL" avec ces spécialités
    Alors le partenaire a 2 spécialités

  # ── Groupes de sécurité ──────────────────────────────────────────────────

  Scénario: Les groupes de sécurité TelecomERP sont définis
    Alors le groupe "Technicien Terrain" existe dans telecom_base
    Et le groupe "Chef de Chantier" existe dans telecom_base
    Et le groupe "Chargé d'Affaires" existe dans telecom_base
    Et le groupe "Responsable" existe dans telecom_base
    Et le groupe "Administrateur TelecomERP" existe dans telecom_base
