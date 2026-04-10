# language: fr
Fonctionnalité: Vérification que toutes les vues se chargent sans erreur
  En tant que testeur
  Je veux que chaque écran de l'ERP se charge correctement
  Afin de garantir qu'aucune page n'est cassée en production

  Scénario: Toutes les vues form des modules telecom sont valides
    Quand je valide toutes les vues de type "form" des modules telecom
    Alors aucune vue form n'est cassée

  Scénario: Toutes les vues tree des modules telecom sont valides
    Quand je valide toutes les vues de type "tree" des modules telecom
    Alors aucune vue tree n'est cassée

  Scénario: Toutes les vues kanban des modules telecom sont valides
    Quand je valide toutes les vues de type "kanban" des modules telecom
    Alors aucune vue kanban n'est cassée

  Scénario: Toutes les vues search des modules telecom sont valides
    Quand je valide toutes les vues de type "search" des modules telecom
    Alors aucune vue search n'est cassée

  Scénario: Toutes les actions window des modules telecom sont valides
    Quand je charge toutes les actions des modules telecom
    Alors aucune action ne référence un modèle inexistant

  Scénario: Tous les menus des modules telecom pointent vers des actions valides
    Quand je vérifie tous les menus des modules telecom
    Alors aucun menu ne pointe vers une action inexistante

  Scénario: Tous les champs référencés dans les vues existent sur les modèles
    Quand je vérifie les champs de toutes les vues des modules telecom
    Alors aucune vue ne référence un champ inexistant

  Scénario: Toutes les vues XML respectent la syntaxe Odoo 17
    Quand je scanne les fichiers XML des modules telecom
    Alors aucun fichier ne contient de syntaxe dépréciée
