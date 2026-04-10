# language: fr
Fonctionnalité: Actions métier et traçabilité des équipements télécom
  En tant que responsable logistique
  Je veux que les transitions d'état respectent les règles métier
  Et que chaque changement soit historisé automatiquement
  Afin de garantir la traçabilité complète du parc équipement

  Contexte:
    Soit une catégorie d'équipement "BTS Nokia" existe
    Et un site "Site Actions Test" avec le code "EQ-ACT-001" existe

  # ── Installation — site obligatoire ──────────────────────────────────────

  Scénario: Installation impossible sans site renseigné
    Soit un équipement "eNodeB Nokia" en stock sans site assigné
    Quand je tente d'installer l'équipement via l'action métier
    Alors une erreur utilisateur est levée indiquant "site"

  Scénario: Installation réussie avec site renseigné
    Soit un équipement "eNodeB Nokia" en stock avec un site assigné
    Quand j'installe l'équipement via l'action métier
    Alors l'état de l'équipement est "installe"
    Et la date d'installation est renseignée

  # ── Panne — uniquement depuis installé ───────────────────────────────────

  Scénario: Déclaration de panne depuis un équipement installé — succès
    Soit un équipement installé sur le site
    Quand je déclare l'équipement en panne
    Alors l'état de l'équipement est "en_panne"

  Scénario: Déclaration de panne impossible depuis l'état en stock
    Soit un équipement "Antenne" en stock sans site assigné
    Quand je tente de déclarer l'équipement en panne
    Alors une erreur utilisateur est levée indiquant "installé"

  # ── Historique automatique ───────────────────────────────────────────────

  Scénario: Un événement historique est créé à chaque changement d'état
    Soit un équipement à l'état "en_stock" existe
    Et le compteur d'historique est à 0
    Quand je passe l'équipement à l'état "installe"
    Alors le compteur d'historique est à 1
    Et le dernier événement contient "En stock" et "Installé"

  # ── Contrainte dates ─────────────────────────────────────────────────────

  Scénario: Date d'installation antérieure à la date d'achat — refusée
    Quand je tente de créer un équipement acheté le "2024-06-01" installé le "2024-01-01"
    Alors une erreur de validation est levée indiquant "antérieure"
