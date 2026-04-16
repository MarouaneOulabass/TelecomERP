# language: fr
Fonctionnalité: Gestion des pleins carburant
  En tant que responsable logistique
  Je veux suivre les pleins carburant des véhicules terrain
  Afin de contrôler les dépenses et alimenter les coûts projet

  Contexte:
    Soit un projet "Déploiement FTTH Casablanca" existe
    Et un lot "Lot 1 - Maarif" existe pour ce projet
    Et un véhicule "Toyota Hilux" avec l'immatriculation "CARB-TEST-01" existe

  Scénario: Création d'un plein carburant
    Quand je crée un plein de 45.0 litres à 14.50 MAD/litre pour ce véhicule
    Alors le plein est créé avec succès

  Scénario: Montant calculé automatiquement
    Quand je crée un plein de 50.0 litres à 14.00 MAD/litre pour ce véhicule
    Alors le montant du plein est 700.00

  Scénario: Création automatique d'une écriture de coût
    Quand je crée un plein de 40.0 litres à 14.50 MAD/litre pour ce véhicule
    Alors une écriture de coût carburant est créée automatiquement

  Scénario: Litres négatifs refusés
    Quand je tente de créer un plein de -10.0 litres à 14.00 MAD/litre pour ce véhicule
    Alors une erreur de validation est levée indiquant "positif"

  Scénario: Plein lié au véhicule
    Quand je crée un plein de 30.0 litres à 14.50 MAD/litre pour ce véhicule
    Alors le plein est rattaché au véhicule "CARB-TEST-01"

  Scénario: L'écriture de coût contient le bon montant
    Quand je crée un plein de 60.0 litres à 15.00 MAD/litre pour ce véhicule
    Alors une écriture de coût carburant est créée automatiquement
    Et le montant de l'écriture de coût est 900.00

  Scénario: Prix à zéro est accepté
    Quand je crée un plein de 20.0 litres à 0.00 MAD/litre pour ce véhicule
    Alors le plein est créé avec succès
    Et le montant du plein est 0.00
