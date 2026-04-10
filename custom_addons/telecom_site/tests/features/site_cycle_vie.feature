# language: fr
Fonctionnalité: Cycle de vie d'un site télécom
  En tant que chef de projet
  Je veux pouvoir faire évoluer l'état d'un site tout au long de son déploiement
  Afin de refléter l'avancement réel sur le terrain

  Contexte:
    Soit un site "Site Test BDD" avec le code "BDD-001" à l'état "prospection" existe

  # ── Transitions nominales dans l'ordre ──────────────────────────────────

  Scénario: Transition Prospection → Étude technique
    Quand je passe le site à l'état "etude"
    Alors l'état du site est "etude"

  Scénario: Transition Étude → En cours d'autorisation
    Soit le site est à l'état "etude"
    Quand je passe le site à l'état "autorisation"
    Alors l'état du site est "autorisation"

  Scénario: Transition Autorisation → Déploiement
    Soit le site est à l'état "autorisation"
    Quand je passe le site à l'état "deploiement"
    Alors l'état du site est "deploiement"

  Scénario: Transition Déploiement → Livré / Opérationnel
    Soit le site est à l'état "deploiement"
    Quand je passe le site à l'état "livre"
    Alors l'état du site est "livre"

  Scénario: Transition Livré → En maintenance
    Soit le site est à l'état "livre"
    Quand je passe le site à l'état "maintenance"
    Alors l'état du site est "maintenance"

  Scénario: Désactivation d'un site en maintenance
    Soit le site est à l'état "maintenance"
    Quand je passe le site à l'état "desactive"
    Alors l'état du site est "desactive"

  # ── Transitions en raccourci (sauts d'état permis) ──────────────────────

  Scénario: Passage direct Prospection → Déploiement (urgence terrain)
    Quand je passe le site à l'état "deploiement"
    Alors l'état du site est "deploiement"

  Scénario: Un site livré peut être désactivé directement
    Soit le site est à l'état "livre"
    Quand je passe le site à l'état "desactive"
    Alors l'état du site est "desactive"

  # ── Compteur documents ────────────────────────────────────────────────────

  Scénario: Compteur documents = 0 sur un site sans document
    Alors le nombre de documents du site est "0"

  Scénario: Compteur documents incrémenté à l'ajout d'un document
    Quand j'ajoute un document "Plan d'implantation" de type "plan" au site
    Alors le nombre de documents du site est "1"

  Scénario: Compteur interventions = 0 sur un nouveau site
    Alors le nombre d'interventions du site est "0"
