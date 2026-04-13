# language: fr
Fonctionnalité: Administration des tests BDD
  En tant qu'administrateur TelecomERP
  Je veux gérer les tests BDD depuis l'interface Odoo
  Afin de suivre la qualité du produit

  Scénario: Aucun menu racine pour telecom_test_admin
    Quand je cherche les menus racines de test_admin
    Alors aucun menu racine n'est trouvé pour telecom_test_admin

  Scénario: Création d'un run de tests
    Quand je crée un run de tests
    Alors le run est à l'état "draft"
