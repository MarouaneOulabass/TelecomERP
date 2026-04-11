# language: fr
Fonctionnalité: Gestion des tenants multi-entreprise
  En tant qu'administrateur TelecomERP
  Je veux gérer les tenants clients
  Afin de provisionner et configurer chaque entreprise cliente

  Scénario: Création d'un tenant
    Quand je crée un tenant "Fibratech Maroc" avec le sous-domaine "fibratech"
    Alors le tenant est créé avec succès
    Et l'état du tenant est "draft"

  Scénario: Sous-domaine unique
    Soit un tenant "Entreprise A" avec le sous-domaine "entreprise-a" existe
    Quand je tente de créer un tenant "Entreprise B" avec le sous-domaine "entreprise-a"
    Alors une erreur d'intégrité est levée

  Scénario: Validation du format de sous-domaine
    Quand je tente de créer un tenant "Test" avec le sous-domaine "AB"
    Alors une erreur de validation est levée indiquant "sous-domaine"

  Scénario: Génération du profil YAML
    Soit un tenant "Telco Services" avec le sous-domaine "telco-services" existe
    Quand je génère le profil YAML du tenant
    Alors le profil YAML contient la clé "tenant"
    Et le profil YAML contient la clé "capabilities"
