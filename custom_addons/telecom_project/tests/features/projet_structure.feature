# language: fr
Fonctionnalité: Structure hiérarchique d'un projet télécom
  En tant que chef de projet
  Je veux organiser les projets en lots et sites
  Afin de suivre l'avancement à chaque niveau de la hiérarchie

  Contexte:
    Soit un site physique "Site Casablanca Nord" avec le code "CSN-001" existe

  # ── Création projet et lot ────────────────────────────────────────────────

  Scénario: Création d'un projet avec un lot
    Quand je crée un projet "Déploiement FTTH Casablanca"
    Et j'ajoute un lot "Lot 1 — Zone Nord" avec le code "L01" à ce projet
    Alors le lot est créé avec succès
    Et le lot appartient au projet

  Scénario: Code de lot unique par projet
    Soit un projet "Déploiement Test" avec un lot "L01" existe déjà
    Quand je tente de créer un second lot avec le code "L01" dans ce même projet
    Alors une erreur d'intégrité est levée

  Scénario: Même code de lot accepté dans deux projets différents
    Soit un projet "Projet Alpha" avec un lot code "L01" existe
    Et un projet "Projet Beta" existe
    Quand j'ajoute un lot avec le code "L01" au projet "Projet Beta"
    Alors le lot est créé avec succès

  # ── Sites de projet ──────────────────────────────────────────────────────

  Scénario: Rattachement d'un site physique à un projet
    Soit un projet "Déploiement Test" existe
    Quand j'ajoute le site "Site Casablanca Nord" à ce projet
    Alors le site de projet est créé avec succès
    Et l'état du site de projet est "prospection"

  Scénario: Un site physique ne peut être rattaché qu'une fois par projet
    Soit un projet "Déploiement Test" existe
    Et le site "Site Casablanca Nord" est déjà rattaché à ce projet
    Quand je tente d'ajouter à nouveau le site "Site Casablanca Nord" à ce projet
    Alors une erreur d'intégrité est levée

  Plan du Scénario: Toutes les transitions du cycle de vie d'un site de projet
    Soit un projet "Déploiement Test" avec un site à l'état "<etat_initial>" existe
    Quand je passe le site de projet à l'état "<etat_final>"
    Alors l'état du site de projet est "<etat_final>"

    Exemples:
      | etat_initial    | etat_final        |
      | prospection     | etude             |
      | etude           | autorisation      |
      | autorisation    | travaux_en_cours  |
      | travaux_en_cours| recette           |
      | recette         | livre             |
      | livre           | suspendu          |

  # ── Calcul taux d'avancement lot ─────────────────────────────────────────

  Scénario: Taux d'avancement d'un lot à 0% sans site livré
    Soit un lot avec "3" sites tous à l'état "prospection" existe
    Alors le taux d'avancement du lot est "0.00" %

  Scénario: Taux d'avancement d'un lot avec 1 site livré sur 2
    Soit un lot avec "2" sites dont "1" à l'état "livre" et "1" à l'état "prospection" existe
    Alors le taux d'avancement du lot est "50.00" %

  Scénario: Taux d'avancement d'un lot à 100% avec tous les sites livrés
    Soit un lot avec "2" sites tous à l'état "livre" existe
    Alors le taux d'avancement du lot est "100.00" %

  # ── États du lot ─────────────────────────────────────────────────────────

  Scénario: Passage d'un lot à l'état "livré"
    Soit un lot à l'état "en_cours" existe
    Quand je marque le lot comme livré
    Alors l'état du lot est "livre"

  Scénario: Suspension d'un lot en cours
    Soit un lot à l'état "en_cours" existe
    Quand je suspends le lot
    Alors l'état du lot est "suspendu"

  Scénario: Reprise d'un lot suspendu
    Soit un lot à l'état "suspendu" existe
    Quand je reprends le lot
    Alors l'état du lot est "en_cours"
