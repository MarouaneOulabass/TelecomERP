# language: fr
Fonctionnalité: Procès-Verbal de Réception télécom
  En tant que chef de chantier
  Je veux formaliser la réception des travaux par un PV signé par les deux parties
  Afin de déclencher la livraison officielle et le décompte financier

  Contexte:
    Soit un projet "Déploiement 5G Nord" existe
    Et un site de projet à l'état "recette" existe dans ce projet

  # ── Création PV ──────────────────────────────────────────────────────────

  Scénario: Création d'un PV de réception partielle
    Quand je crée un PV partiel pour ce site de projet
    Alors le PV est créé avec succès
    Et l'état du PV est "draft"

  Scénario: Création d'un PV de réception définitive
    Quand je crée un PV définitif pour ce site de projet
    Alors le PV est créé avec succès
    Et le numéro de PV est généré automatiquement

  # ── Workflow PV ──────────────────────────────────────────────────────────

  Scénario: Signature d'un PV avec les deux signatures électroniques
    Soit un PV en brouillon avec les deux signatures présentes existe
    Quand je signe le PV
    Alors l'état du PV est "signe"
    Et la date de signature est renseignée

  Scénario: Impossible de signer un PV sans signature de l'entreprise
    Soit un PV en brouillon sans signature entreprise existe
    Quand je tente de signer le PV
    Alors une erreur de signature est levée

  Scénario: Impossible de signer un PV sans signature du client
    Soit un PV en brouillon sans signature client existe
    Quand je tente de signer le PV
    Alors une erreur de signature est levée

  Scénario: Approbation d'un PV signé
    Soit un PV à l'état "signe" existe
    Quand j'approuve le PV
    Alors l'état du PV est "approuve"

  Scénario: Impossible d'approuver un PV encore en brouillon
    Soit un PV en brouillon avec les deux signatures présentes existe
    Quand j'approuve le PV directement sans signer
    Alors une erreur de workflow PV est levée

  # ── Effet du PV définitif sur le site de projet ──────────────────────────

  Scénario: PV définitif approuvé déclenche la livraison du site de projet
    Soit un PV définitif à l'état "signe" lié à ce site de projet existe
    Quand j'approuve le PV
    Alors l'état du site de projet est "livre"
    Et la date de livraison réelle est renseignée

  Scénario: PV partiel approuvé ne passe pas le site de projet à "livre"
    Soit un PV partiel à l'état "signe" lié à ce site de projet existe
    Quand j'approuve le PV
    Alors l'état du site de projet n'est pas "livre"

  # ── Enchaînement complet ─────────────────────────────────────────────────

  Scénario: Workflow complet PV définitif — brouillon → signé → approuvé → site livré
    Quand je crée un PV définitif avec les deux signatures pour ce site de projet
    Et je signe le PV
    Et j'approuve le PV
    Alors l'état du PV est "approuve"
    Et l'état du site de projet est "livre"
