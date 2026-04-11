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
