# language: fr
Fonctionnalité: Gestion du parc véhicules terrain
  En tant que responsable logistique
  Je veux suivre les véhicules de terrain avec leurs échéances réglementaires
  Afin d'éviter les infractions et garantir la sécurité des équipes

  Contexte:
    Soit un employé technicien "Hamza El Fassi" existe

  # ── Création véhicule ────────────────────────────────────────────────────

  Scénario: Création d'un véhicule avec immatriculation unique
    Quand je crée un véhicule "Toyota Hilux" avec l'immatriculation "TEST-Z-999"
    Alors le véhicule est créé avec succès

  Scénario: Immatriculation unique — doublon refusé
    Soit un véhicule avec l'immatriculation "TEST-Z-888" existe déjà
    Quand je tente de créer un véhicule avec la même immatriculation "TEST-Z-888"
    Alors une erreur d'intégrité est levée

  # ── Alertes réglementaires ───────────────────────────────────────────────

  Scénario: Alerte contrôle technique expirant dans moins de 30 jours
    Soit la date du jour est "2024-03-01"
    Et un véhicule avec contrôle technique expirant le "2024-03-25" existe
    Alors l'alerte contrôle technique est active

  Scénario: Pas d'alerte contrôle technique si expiration dans plus de 30 jours
    Soit la date du jour est "2024-03-01"
    Et un véhicule avec contrôle technique expirant le "2024-05-01" existe
    Alors l'alerte contrôle technique est inactive

  Scénario: Alerte assurance expirant dans moins de 30 jours
    Soit la date du jour est "2024-03-01"
    Et un véhicule avec assurance expirant le "2024-03-20" existe
    Alors l'alerte assurance est active

  # ── Cycle de vie véhicule ─────────────────────────────────────────────

  Scénario: Transition disponible → en mission → retour disponible
    Soit un véhicule "Toyota Hilux" avec l'immatriculation "77777-C-33" existe
    Quand je mets le véhicule en mission
    Alors l'état du véhicule est "en_mission"
    Quand je retourne le véhicule
    Alors l'état du véhicule est "disponible"

  # ── Alerte kilométrique entretien ────────────────────────────────────────

  Scénario: Alerte entretien km — kilométrage proche du prochain entretien
    Soit un véhicule avec km dernier entretien "50000" et intervalle "10000"
    Et le kilométrage actuel est "59600"
    Alors l'alerte entretien km est active

  # ── Entretiens ───────────────────────────────────────────────────────────

  Scénario: Création d'un entretien lié à un véhicule
    Soit un véhicule "Ford Transit" avec l'immatriculation "99999-B-45" existe
    Quand je crée un entretien "Vidange" du "2024-03-01" pour ce véhicule
    Alors l'entretien est enregistré pour le véhicule
