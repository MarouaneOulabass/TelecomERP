# language: fr
Fonctionnalite: Facturation telecom et relances
  En tant que charge d'affaires
  Je veux gerer les factures clients avec suivi des paiements et relances
  Afin de garantir le recouvrement et le respect de la loi 69-21

  Contexte:
    Soit la societe courante est initialisee
    Et un partenaire client "Maroc Telecom" avec ICE "001234567890123" existe
    Et un partenaire client "Client Sans ICE" sans ICE existe
    Et un projet telecom "Projet Fibre Casa" existe

  # -- Creation de factures ---------------------------------------------------

  Scenario: Creation d'une facture standard liee a un projet
    Quand je cree une facture client pour "Maroc Telecom" de type "standard" liee au projet "Projet Fibre Casa"
    Alors la facture est creee avec succes
    Et le type telecom de la facture est "standard"
    Et le projet telecom est "Projet Fibre Casa"

  Scenario: Creation d'une facture de type situation de travaux
    Quand je cree une facture client pour "Maroc Telecom" de type "situation"
    Alors la facture est creee avec succes
    Et le type telecom de la facture est "situation"

  Scenario: Facture sans projet est autorisee (ad-hoc)
    Quand je cree une facture client pour "Maroc Telecom" de type "standard" sans projet
    Alors la facture est creee avec succes
    Et le projet telecom est vide

  # -- Delai de paiement ------------------------------------------------------

  Scenario: Calcul du retard de paiement en jours
    Soit une facture postee pour "Maroc Telecom" avec echeance il y a 30 jours
    Quand je recalcule le delai de paiement
    Alors le retard de paiement est de 30 jours
    Et l'alerte delai paiement est desactivee

  Scenario: Alerte delai paiement declenchee a plus de 60 jours (loi 69-21)
    Soit une facture postee pour "Maroc Telecom" avec echeance il y a 61 jours
    Quand je recalcule le delai de paiement
    Alors le retard de paiement est de 61 jours
    Et l'alerte delai paiement est activee

  # -- Relances ---------------------------------------------------------------

  Scenario: Creation d'une relance niveau 1
    Soit une facture postee pour "Maroc Telecom" avec echeance il y a 30 jours
    Quand je cree une relance de niveau "relance_1" par "email"
    Et j'envoie la relance
    Alors la relance est en etat "sent"
    Et le compteur de relances de la facture est 1

  Scenario: Le compteur de relances s'incremente
    Soit une facture postee pour "Maroc Telecom" avec echeance il y a 45 jours
    Quand je cree une relance de niveau "relance_1" par "email"
    Et j'envoie la relance
    Et je cree une relance de niveau "relance_2" par "courrier"
    Et j'envoie la relance
    Alors le compteur de relances de la facture est 2

  # -- Validation ICE ----------------------------------------------------------

  Scenario: Le champ ICE du partenaire est reporte sur la facture
    Quand je cree une facture client pour "Maroc Telecom" de type "standard"
    Alors le champ ICE client de la facture est "001234567890123"
