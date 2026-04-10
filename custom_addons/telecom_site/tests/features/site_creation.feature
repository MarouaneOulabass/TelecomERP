# language: fr
Fonctionnalité: Création et gestion d'un site télécom
  En tant que chargé de déploiement
  Je veux pouvoir créer et gérer des fiches de sites télécom
  Afin de centraliser toutes les informations sur l'infrastructure déployée

  Contexte:
    Soit la société courante est initialisée
    Et un partenaire opérateur "Maroc Telecom" de type "operator" existe
    Et un partenaire bailleur "Propriétaire Foncier SA" de type "lessor" existe

  # ── Création nominale ────────────────────────────────────────────────────

  Scénario: Création d'un site avec les champs obligatoires minimum
    Quand je crée un site avec le code "TLM-001", le nom "Site Casablanca Centre" et le type "pylone_greenfield"
    Alors le site est créé avec succès
    Et l'état du site est "prospection"
    Et la société rattachée est l'entreprise courante

  Scénario: Tous les types de sites télécom sont disponibles
    Alors les types de sites disponibles incluent "pylone_greenfield"
    Et les types de sites disponibles incluent "rooftop"
    Et les types de sites disponibles incluent "shelter"
    Et les types de sites disponibles incluent "indoor_das"
    Et les types de sites disponibles incluent "datacenter"
    Et les types de sites disponibles incluent "cabinet_ftth"
    Et les types de sites disponibles incluent "chambre_tirage"

  Scénario: Les 12 régions du Maroc sont couvertes
    Alors les wilayas disponibles incluent "casablanca_settat"
    Et les wilayas disponibles incluent "rabat_sale_kenitra"
    Et les wilayas disponibles incluent "tanger_tetouan_alhoceima"
    Et les wilayas disponibles incluent "souss_massa"
    Et les wilayas disponibles incluent "fes_meknes"
    Et les wilayas disponibles incluent "oriental"
    Et les wilayas disponibles incluent "marrakech_safi"
    Et les wilayas disponibles incluent "draa_tafilalet"
    Et les wilayas disponibles incluent "beni_mellal_khenifra"
    Et les wilayas disponibles incluent "guelmim_oued_noun"
    Et les wilayas disponibles incluent "laayoune_sakia_el_hamra"
    Et les wilayas disponibles incluent "dakhla_oued_ed_dahab"

  # ── Unicité du code interne ──────────────────────────────────────────────

  Scénario: Code interne unique par société — doublon refusé
    Soit un site avec le code interne "TLM-001" existe déjà dans la société courante
    Quand je tente de créer un second site avec le même code "TLM-001"
    Alors une erreur d'intégrité est levée

  Scénario: Même code interne accepté dans deux sociétés différentes
    Soit la société courante possède déjà un site avec le code "TLM-001"
    Quand je crée un site avec le code "TLM-001" dans une autre société
    Alors le site est créé avec succès

  # ── Validation GPS ───────────────────────────────────────────────────────

  Scénario: Latitude invalide supérieure à 90 — refusée
    Quand je crée un site avec la latitude GPS "91.0"
    Alors une erreur de validation est levée indiquant "Latitude GPS"

  Scénario: Latitude invalide inférieure à -90 — refusée
    Quand je crée un site avec la latitude GPS "-91.0"
    Alors une erreur de validation est levée indiquant "Latitude GPS"

  Scénario: Longitude invalide supérieure à 180 — refusée
    Quand je crée un site avec la longitude GPS "181.0"
    Alors une erreur de validation est levée indiquant "Longitude GPS"

  Scénario: Longitude invalide inférieure à -180 — refusée
    Quand je crée un site avec la longitude GPS "-181.0"
    Alors une erreur de validation est levée indiquant "Longitude GPS"

  Scénario: Coordonnées GPS aux limites exactes — acceptées
    Quand je crée un site avec la latitude GPS "90.0" et la longitude GPS "180.0"
    Alors le site est créé avec succès

  Scénario: Coordonnées GPS typiques Maroc — acceptées
    Quand je crée un site avec la latitude GPS "33.589886" et la longitude GPS "-7.603869"
    Alors le site est créé avec succès

  # ── Validation dates de bail ─────────────────────────────────────────────

  Scénario: Date fin de bail antérieure à la date de début — refusée
    Quand je crée un site avec la date début de bail "2024-01-01" et la date fin de bail "2023-12-31"
    Alors une erreur de validation est levée indiquant "fin de bail"

  Scénario: Date fin de bail égale à la date de début — acceptée
    Quand je crée un site avec la date début de bail "2024-01-01" et la date fin de bail "2024-01-01"
    Alors le site est créé avec succès

  Scénario: Dates de bail cohérentes (fin > début) — acceptées
    Quand je crée un site avec la date début de bail "2024-01-01" et la date fin de bail "2027-12-31"
    Alors le site est créé avec succès

  # ── Action Google Maps ───────────────────────────────────────────────────

  Scénario: Ouverture dans Google Maps avec coordonnées GPS valides
    Soit un site avec latitude "33.589886" et longitude "-7.603869" existe
    Quand je demande l'ouverture dans Google Maps
    Alors une action URL contenant "maps.google.com" et "33.589886" est retournée

  Scénario: Ouverture dans Google Maps sans coordonnées — erreur descriptive
    Soit un site sans coordonnées GPS existe
    Quand je demande l'ouverture dans Google Maps
    Alors une erreur de validation est levée indiquant "coordonnées GPS"
