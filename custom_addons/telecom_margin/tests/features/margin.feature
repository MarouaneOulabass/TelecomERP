# language: fr
Fonctionnalité: Cockpit de rentabilité projet
  En tant que responsable financier
  Je veux visualiser la marge par projet et par lot
  Afin de piloter la rentabilité des chantiers en temps réel

  Scénario: La vue marge projet existe dans le système
    Alors le modèle "telecom.project.margin" est accessible

  Scénario: Un projet avec des coûts affiche la marge
    Soit un projet "Déploiement FTTH Casa" existe avec des coûts de 50000.00 MAD
    Alors la marge du projet reflète les coûts saisis

  Scénario: L'indicateur de santé est calculé
    Alors le champ "health" existe sur le modèle marge avec les valeurs "green", "yellow", "red", "unknown"

  Scénario: Un projet sans coûts affiche une marge nulle
    Soit un projet "Projet Vide" existe sans aucun coût
    Alors la marge du projet est nulle ou inexistante

  Scénario: Le cockpit affiche les coûts par catégorie
    Alors les champs de ventilation existent : cout_main_oeuvre, cout_materiel, cout_sous_traitance, cout_carburant, cout_autres

  Scénario: Le compteur de coûts sans tâche est présent
    Alors le champ "nb_task_missing" existe sur le modèle marge

  Scénario: La marge est en lecture seule
    Alors le modèle marge est en lecture seule avec _auto=False

  Scénario: Le drill-down vers les coûts est disponible
    Alors la méthode "action_open_costs" existe sur le modèle marge

  Scénario: Les champs projet et lot sont présents
    Alors le champ "project_id" existe sur le modèle marge
    Et le champ "lot_id" existe sur le modèle marge
    Et le champ "partner_id" existe sur le modèle marge
