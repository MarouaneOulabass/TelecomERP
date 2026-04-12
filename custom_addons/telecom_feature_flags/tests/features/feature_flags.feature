# language: fr
Fonctionnalité: Gestion des feature flags
  En tant qu'administrateur TelecomERP
  Je veux activer ou désactiver des fonctionnalités à chaud
  Afin de contrôler le comportement du système sans redéploiement

  Contexte:
    Soit un environnement TelecomERP avec le module feature_flags installé

  Scénario: Activation d'un flag change le comportement
    Soit un flag "assistant_proactive.watcher_marge" désactivé
    Quand l'administrateur active ce flag via l'écran de configuration
    Alors l'entrée est historisée avec l'utilisateur et l'horodatage
    Et le flag est marqué comme actif

  Scénario: Enregistrement idempotent des flags
    Soit un flag "test_module.test_flag" actif manuellement
    Quand le module est réinstallé avec le même flag déclaré
    Alors l'état actif du flag est préservé
    Et seuls le nom et la description sont mis à jour

  Scénario: Refus d'un code de flag malformé
    Quand on tente de créer un flag avec le code "INVALID-CODE!"
    Alors la création est refusée avec une erreur de validation

  Scénario: Le décorateur feature_flag bloque si inactif
    Soit un flag "test_module.decorated_func" désactivé
    Quand une méthode décorée avec ce flag est appelée
    Alors la méthode retourne None sans exécuter le corps
