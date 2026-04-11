# language: fr
Fonctionnalité: Gestion des écritures de coût projet
  En tant que chef de chantier
  Je veux saisir et suivre les couts rattaches aux projets et lots
  Afin de piloter la rentabilité des chantiers

  # -- Creation avec projet + lot --

  Scénario: Creation d'un coût avec projet et lot
    Soit un projet "Déploiement FTTH Casablanca" existe
    Et un lot "Lot 1 - Maarif" existe pour ce projet
    Et un type de coût "Main d'oeuvre directe" de catégorie "main_oeuvre" existe
    Quand je créé un coût de 15000.00 MAD pour ce projet et ce lot
    Alors le coût est créé avec succès
    Et le montant du coût est 15000.00

  # -- Creation sans projet -> refusee --

  Scénario: Creation d'un coût sans projet est refusee
    Soit un lot orphelin "Lot X" existe
    Et un type de coût "Materiel" de catégorie "materiel" existe
    Quand je tente de creer un coût de 5000.00 MAD sans projet
    Alors une erreur est levée

  # -- Creation sans lot -> refusee --

  Scénario: Creation d'un coût sans lot est refusee
    Soit un projet "Rollout 4G Rabat" existe
    Et un type de coût "Sous-traitance" de catégorie "sous_traitance" existe
    Quand je tente de creer un coût de 8000.00 MAD sans lot
    Alors une erreur est levée

  # -- Montant negatif -> refuse --

  Scénario: Creation d'un coût avec montant negatif est refusee
    Soit un projet "Maintenance Tanger" existe
    Et un lot "Lot Maintenance" existe pour ce projet
    Et un type de coût "Carburant" de catégorie "carburant" existe
    Quand je tente de creer un coût de -500.00 MAD pour ce projet et ce lot
    Alors une erreur de validation est levée indiquant "positif"

  # -- Tache manquante --

  Scénario: Un coût sans tache a le flag task_missing a True
    Soit un projet "Projet Alpha" existe
    Et un lot "Lot Alpha" existe pour ce projet
    Et un type de coût "Frais generaux" de catégorie "frais_generaux" existe
    Quand je créé un coût de 3000.00 MAD pour ce projet et ce lot sans tache
    Alors le coût est créé avec succès
    Et le flag task_missing est True

  # -- Tache presente --

  Scénario: Un coût avec tache a le flag task_missing a False
    Soit un projet "Projet Beta" existe
    Et un lot "Lot Beta" existe pour ce projet
    Et une tache "Installation OLT" existe pour ce projet
    Et un type de coût "Materiel" de catégorie "materiel" existe
    Quand je créé un coût de 25000.00 MAD pour ce projet et ce lot avec cette tache
    Alors le coût est créé avec succès
    Et le flag task_missing est False

  # -- Workflow draft -> confirmed -> validated --

  Scénario: Workflow de validation d'un cout
    Soit un projet "Projet Gamma" existe
    Et un lot "Lot Gamma" existe pour ce projet
    Et un type de coût "Location engins" de catégorie "location" existe
    Et un coût de 12000.00 MAD existe en brouillon pour ce projet et ce lot
    Quand je confirme le cout
    Alors l'etat du coût est "confirmed"
    Quand je valide le cout
    Alors l'etat du coût est "validated"

  # -- Types de couts pre-charges --

  Scénario: Les types de couts sont pre-charges (10 types)
    Alors au moins 10 types de couts existent dans le systeme
