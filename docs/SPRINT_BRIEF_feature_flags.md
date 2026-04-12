# SPRINT BRIEF — tc_feature_flags + tc_assistant (widget popup global) + tc_assistant_proactive

> À coller dans Claude Code en mode autonome. Ce sprint couvre trois livrables interdépendants : la capability socle de feature flags, le widget popup global de l'assistant conversationnel, et l'intégration proactive via flags. Sprint dense, à traiter avec rigueur. **Attendre validation humaine à la fin de chaque tâche avant de passer à la suivante.**

---

## Contexte

Le produit a besoin d'un mécanisme de **feature flags runtime** permettant aux administrateurs d'un tenant d'activer ou désactiver des sous-fonctionnalités à chaud, sans redéploiement et sans modifier le `tenant_profile.yaml`.

Ce besoin est distinct des capabilities du catalogue :
- Les **capabilities** (`tenant_profile.yaml`) définissent ce qui est installé → décision structurelle figée au provisioning.
- Les **feature flags** définissent ce qui est actif dans une capability installée → décision évolutive modifiable par l'admin à tout moment.

Ne jamais mélanger les deux. Ne jamais utiliser l'un pour ce qui relève de l'autre.

## Lectures obligatoires avant toute action

1. `docs/PRODUCT_VISION.md`
2. `docs/CAPABILITY_CATALOG.md`
3. `docs/ARCHITECTURE_PRINCIPLES.md`
4. `docs/TENANT_PROFILE_SCHEMA.json`
5. `docs/TEST_HARNESS_SPEC.md`
6. `docs/DEFINITION_OF_DONE.md`
7. `docs/CAPABILITY_tc_assistant.md` (fiche de la capability à créer en tâche 3)
8. `docs/CAPABILITY_tc_assistant_proactive.md` (fiche de la capability à adapter en tâches 2 et 4)

Confirme leur lecture en début de session avant toute action.

## Périmètre strict de ce sprint

**Tu es autorisé à** :
- Créer la nouvelle capability `tc_feature_flags` complète (modèles, vues, tests, documentation).
- Créer la capability `tc_assistant` complète avec son widget popup global (tâche 3).
- Créer les fichiers `assistant_tools.py` dans les capabilities hébergeant les 5 outils MVP.
- Créer `tc_assistant_proactive` ou adapter sa version existante pour la rendre conditionnelle aux flags.
- Créer un fichier `feature_flags.py` dans `tc_assistant` et `tc_assistant_proactive`.
- Ajouter les patches documentaires listés en tâche 5 (documents fondateurs).

**Tu n'es pas autorisé à** :
- Créer un menuitem racine ou une page dédiée pour `tc_assistant` (widget popup uniquement, cf. tâche 3).
- Ajouter des flags dans des capabilities autres que `tc_assistant` et `tc_assistant_proactive`.
- Créer de nouveaux watchers au-delà de ceux prévus pour `tc_assistant_proactive`.
- Implémenter le moteur de recherche vectoriel pour `search_documents` (version simple SQL pour ce sprint).
- Activer les canaux email, WhatsApp ou SMS (les flags existent mais sont à `False`, aucun code d'envoi externe ne doit tourner).
- Toucher aux autres capabilities sauf pour ajouter leur `assistant_tools.py` quand c'est nécessaire aux 5 outils MVP.

## Tâche 1 — Créer la capability `tc_feature_flags`

### Positionnement dans le catalogue

- **Famille** : 1 (Socle technique)
- **Vague** : MVP
- **Statut** : Socle obligatoire (installée automatiquement partout, non désactivable)
- **Code** : `tc_feature_flags`
- **Dépendances dures** : `tc_core`, `tc_security`

### Modèles à créer

**`feature.flag`** — définition d'un flag disponible dans le système :

| Champ | Type | Description |
|---|---|---|
| `code` | Char, unique, required | Identifiant technique, format `snake_case` avec préfixe capability (ex: `assistant_proactive.watcher_marge_sous_seuil`) |
| `name` | Char, required, translate | Nom lisible affiché dans l'UI |
| `description` | Text, translate | Explication de ce que le flag active/désactive |
| `capability` | Char, required | Nom technique de la capability qui déclare le flag |
| `category` | Selection | Catégorie pour regroupement UI (watchers, notifications, ui, experimental, etc.) |
| `default_value` | Boolean, required | Valeur par défaut à l'installation |
| `active` | Boolean, required, default=valeur de `default_value` | État actuel dans ce tenant |
| `last_changed_by` | Many2one res.users | Trace du dernier utilisateur ayant modifié le flag |
| `last_changed_at` | Datetime | Horodatage du dernier changement |

**Contraintes** :
- Le `code` respecte le pattern `^tc_[a-z_]+\.[a-z_]+$`
- Un seul enregistrement par `code` par base (unicité stricte)

**`feature.flag.history`** — audit des changements :

| Champ | Type |
|---|---|
| `flag_id` | Many2one feature.flag, required |
| `changed_by` | Many2one res.users, required |
| `changed_at` | Datetime, required |
| `old_value` | Boolean |
| `new_value` | Boolean |
| `reason` | Char, optionnel |

### Module Python `feature_flag_utils`

Dans `tc_feature_flags/utils/feature_flag.py`, exposer :

**Décorateur `@feature_flag('code')`** : décore une méthode Python. Si le flag est désactivé, la méthode retourne immédiatement `None` (ou une valeur configurable via paramètre `default_return`).

```python
@feature_flag('assistant_proactive.watcher_marge_sous_seuil')
def check_marge_sous_seuil(self):
    # corps exécuté seulement si le flag est actif
    ...
```

**Fonction `is_flag_active(code, env)`** : vérifie l'état d'un flag de façon programmatique. Renvoie `False` si le flag n'existe pas (sécurité par défaut).

**Fonction `register_flags(capability_name, flags_list, env)`** : appelée au moment de l'installation ou mise à jour d'une capability pour enregistrer ses flags dans la base. Idempotente : si un flag existe déjà, son état `active` est préservé, seuls `name`, `description`, `category` sont mis à jour.

### Mécanisme de découverte automatique

Lors de l'installation ou mise à jour d'une capability, un hook Odoo (`post_init_hook`) scanne la capability à la recherche d'un fichier `feature_flags.py` à la racine du module. Si ce fichier existe et expose une variable `FLAGS` (liste de dicts), les flags sont enregistrés automatiquement via `register_flags`.

Format attendu du fichier `feature_flags.py` dans une capability :

```python
"""
Déclaration des feature flags de la capability tc_assistant_proactive.
Format standardisé lu automatiquement au moment de l'installation.
"""

FLAGS = [
    {
        'code': 'assistant_proactive.watcher_marge_sous_seuil',
        'name': "Watcher : marge projet sous seuil",
        'description': "Génère une notification quand la marge d'un projet passe sous le seuil configuré.",
        'category': 'watchers',
        'default_value': True,
    },
    # ... autres flags
]
```

### Vues et écran d'administration

Créer :

- Une vue **liste** de `feature.flag` avec colonnes : code, name, category, active (avec widget `boolean_toggle`), capability, last_changed_by, last_changed_at.
- Une vue **kanban** groupée par `capability`, permettant de voir d'un coup d'œil les flags actifs et inactifs d'une capability donnée.
- Une vue **form** en lecture seule pour la définition, avec un switch pour `active` et un lien vers l'historique.
- Un **menu** dans "Paramètres TelecomERP" → "Configuration" → "Fonctionnalités", accessible uniquement au groupe **Administrateur TelecomERP**.
- Une **vue de filtrage** avec filtres prédéfinis : "Flags actifs", "Flags inactifs", "Par capability", "Modifiés récemment".

### Sécurité

- Lecture : groupe Responsable et Administrateur TelecomERP.
- Modification : groupe Administrateur TelecomERP uniquement.
- Aucun utilisateur en dessous du niveau Responsable ne peut voir l'écran.
- Toute modification déclenche automatiquement une entrée dans `feature.flag.history`.

### Tests

Dans `tc_feature_flags/tests/` :

- `test_flag_registration.py` : les flags d'un fichier `feature_flags.py` sont bien enregistrés à l'install.
- `test_flag_idempotence.py` : réinstaller une capability ne réinitialise pas l'état des flags existants.
- `test_flag_decorator.py` : le décorateur `@feature_flag` bloque bien l'exécution si le flag est inactif.
- `test_flag_history.py` : toute modification génère une entrée dans l'historique.
- `test_flag_security.py` : un utilisateur non-admin ne peut ni lire ni modifier les flags.
- `test_flag_code_pattern.py` : un flag avec un code malformé est refusé à la création.

Un scénario BDD minimum dans `features/feature_flags.feature` :

```gherkin
Scénario : Activation d'un flag change le comportement
  Étant donné un flag "assistant_proactive.watcher_marge_sous_seuil" désactivé
  Quand l'administrateur active ce flag via l'écran de configuration
  Alors l'entrée est historisée avec l'utilisateur et l'horodatage
  Et le watcher correspondant devient opérationnel au prochain cycle
```

## Tâche 2 — Intégrer les feature flags dans `tc_assistant_proactive`

### Créer le fichier `custom_addons/tc_assistant_proactive/feature_flags.py`

Déclarer **tous les watchers prévus dans la fiche capability** comme flags individuels. Valeurs par défaut :

- **`True` par défaut pour les 3 watchers pilotes** (marge sous seuil, caution expirant, pointage manquant).
- **`False` par défaut pour tous les autres watchers** (ils pourront être activés par l'admin du tenant au fur et à mesure).
- **`False` par défaut pour les flags de canaux** autres que in-app (puisque email/WhatsApp/SMS ne sont pas livrés dans ce sprint).

Exemple minimal de la liste attendue :

```python
FLAGS = [
    # Watchers pilotes (actifs par défaut)
    {
        'code': 'assistant_proactive.watcher_marge_sous_seuil',
        'name': "Alerte marge projet sous seuil",
        'description': "Pousse une notification quand la marge d'un projet passe sous le seuil configuré.",
        'category': 'watchers',
        'default_value': True,
    },
    {
        'code': 'assistant_proactive.watcher_caution_expirant',
        'name': "Alerte caution bancaire expirant",
        'description': "Pousse une notification à J-30, J-15 et J-7 avant expiration d'une caution.",
        'category': 'watchers',
        'default_value': True,
    },
    {
        'code': 'assistant_proactive.watcher_pointage_manquant',
        'name': "Alerte pointage manquant",
        'description': "Pousse une notification en fin de journée pour chaque technicien affecté mais non pointé.",
        'category': 'watchers',
        'default_value': True,
    },
    # Autres watchers (inactifs par défaut, activables par l'admin)
    {
        'code': 'assistant_proactive.watcher_derive_marge_hebdo',
        'category': 'watchers',
        'default_value': False,
        # ... name, description
    },
    {
        'code': 'assistant_proactive.watcher_facture_impayee_j30',
        'category': 'watchers',
        'default_value': False,
        # ...
    },
    # ... compléter selon la liste des watchers de la fiche tc_assistant_proactive
    
    # Canaux (seul in-app actif)
    {
        'code': 'assistant_proactive.channel_in_app',
        'name': "Canal notifications in-app",
        'category': 'channels',
        'default_value': True,
    },
    {
        'code': 'assistant_proactive.channel_email',
        'category': 'channels',
        'default_value': False,
    },
    {
        'code': 'assistant_proactive.channel_whatsapp',
        'category': 'channels',
        'default_value': False,
    },
    {
        'code': 'assistant_proactive.channel_sms',
        'category': 'channels',
        'default_value': False,
    },
    # Features UX
    {
        'code': 'assistant_proactive.digest_matinal',
        'name': "Digest matinal",
        'category': 'ux',
        'default_value': False,
    },
]
```

Compléter la liste pour couvrir **tous** les watchers listés dans la fiche `tc_assistant_proactive`.

### Modifier les watchers pour utiliser les flags

Chaque watcher dans `tc_assistant_proactive` doit être conditionné par son flag via le décorateur `@feature_flag`. Un watcher dont le flag est inactif retourne `None` et ne produit aucune notification.

De même, le routeur de canaux doit vérifier les flags `channel_*` avant d'envoyer sur un canal donné. Si le canal est désactivé, la notification bascule proprement vers le canal in-app.

### Tests d'intégration

Dans `tc_assistant_proactive/tests/` :

- `test_watcher_with_flag_off.py` : un watcher dont le flag est désactivé ne génère pas de notification.
- `test_watcher_with_flag_on.py` : un watcher avec flag actif génère bien la notification attendue.
- `test_channel_fallback.py` : si le canal WhatsApp est désactivé mais une notification est "critical", elle tombe sur in-app sans erreur.

## Tâche 3 — Créer tc_assistant avec son widget popup global

Cette tâche livre la capability `tc_assistant` elle-même avec son interface **en widget popup global**, conformément à la fiche `CAPABILITY_tc_assistant.md`. Lire cette fiche avant de commencer.

### Principe non-négociable : pas de page dédiée

`tc_assistant` **n'a aucune page ni menu racine**. Il est présent sous forme d'un widget OWL global monté dans la chrome de l'application Odoo, accessible depuis n'importe quel écran via un bouton flottant (FAB).

**Interdictions absolues pour cette tâche** :
- Aucun `<menuitem>` dans les fichiers XML de `tc_assistant`, sauf celui listé dans la section "exception tolérée" ci-dessous.
- Aucune `ir.actions.act_window` qui ouvre une vue racine de l'assistant.
- Aucune entrée dans la barre de navigation principale d'Odoo.

**Exception tolérée unique** : une page "Historique de mes conversations" accessible **depuis le widget lui-même** (lien dans le panneau dépliable), **pas depuis un menu principal**. Cette page sert à retrouver d'anciennes conversations, rien de plus.

### Composants techniques à livrer

**3.1 — Modèles Odoo**

- `assistant.conversation` : une conversation par utilisateur, avec titre auto-généré depuis la première question.
- `assistant.message` : un message individuel, rôle (user/assistant), contenu, horodatage, conversation parente.
- `assistant.tool.call` : trace de chaque appel d'outil (nom, paramètres JSON, résultat JSON, durée, coût en tokens).
- `assistant.tool.registry` : registry runtime des outils exposés par les capabilities actives.
- `res.users.notification` : notifications in-app destinées à un utilisateur (utilisé par `tc_assistant_proactive`, modèle créé ici car partagé).

**3.2 — Widget OWL global**

Créer un composant OWL `AssistantPopup` dans `tc_assistant/static/src/components/assistant_popup/`. Le composant est monté dans la chrome d'Odoo via un patch du template `web.layout` ou via le système d'assets.

Comportement attendu :
- Un **bouton flottant (FAB)** fixé en bas à droite de l'écran, toujours visible pour les utilisateurs autorisés.
- Le FAB affiche un **badge compteur** des notifications non lues (couleur indicative : gris = 0, bleu = >0, rouge = critique non lue).
- Clic sur le FAB → **panneau de chat persistant** qui s'ouvre en overlay en bas à droite, largeur ~400px, hauteur ~600px.
- Le panneau est **persistant à travers les navigations** : changer de page dans Odoo ne ferme pas le panneau et ne perd pas l'historique en cours.
- Le panneau contient deux onglets : "Chat" (conversation) et "Notifications" (liste des notifications in-app).
- Un bouton "Historique" dans le header du panneau ouvre la page d'historique des conversations passées.

**3.3 — Capture du contexte courant**

Exposer un outil `get_current_context()` dans le registry, qui retourne à l'agent :
- Le modèle Odoo actuellement affiché (ex : `project.project`)
- L'ID du record actif si vue form (ex : `42`)
- Les filtres actifs si vue liste
- Le nom lisible du record si disponible (ex : "Casa-Nord 5G")

Ce contexte est **automatiquement joint** à chaque requête de l'utilisateur comme métadonnée système, sans que l'utilisateur ait à le préciser.

**3.4 — Backend agent**

Un contrôleur HTTP `/assistant/chat` qui :
- Reçoit le message utilisateur + l'ID de conversation + le contexte courant.
- Appelle l'API Claude avec le registry d'outils exposé par les capabilities actives.
- Gère la boucle de tool-use (l'agent peut appeler plusieurs outils avant de répondre).
- Log chaque appel d'outil dans `assistant.tool.call`.
- Stream la réponse au widget frontend.
- Vérifie le budget LLM du tenant avant chaque appel et refuse proprement si dépassé.

**3.5 — Les 5 outils MVP**

Créer les fichiers `assistant_tools.py` dans les capabilities concernées (cf. fiche `tc_assistant`) :

1. `get_invoices` dans `telecom_finance_ma` ou `tc_facturation`
2. `get_payment_status` dans la même capability
3. `get_project_status` dans `telecom_margin` ou `tc_margin_dashboard`
4. `get_interventions` dans `telecom_intervention`
5. `search_documents` dans `tc_assistant` lui-même (pour l'instant version simple sans vectoriel, juste un filtre SQL sur les ir.attachment — la version vectorielle sera livrée en V2)

Plus l'outil transversal `get_current_context()` déjà mentionné.

**3.6 — Règle anti-hallucination**

Implémenter et tester la règle : **tout chiffre présent dans une réponse de l'agent doit correspondre exactement à une valeur retournée par un outil**. Un test de propriété dans `tests/property_based/` vérifie ce principe sur 50 conversations générées.

### Sécurité

- Le widget n'est visible que pour les utilisateurs du groupe "Utilisateur TelecomERP" (ou supérieur).
- Les outils respectent les record rules Odoo : un utilisateur ne voit via l'assistant que ce qu'il voit via l'UI.
- Test d'isolation multi-tenant : un utilisateur du tenant A ne peut jamais obtenir via l'assistant une donnée du tenant B.

### Feature flags à déclarer dans tc_assistant

Créer `custom_addons/tc_assistant/feature_flags.py` avec au minimum :

```python
FLAGS = [
    {
        'code': 'assistant.enabled',
        'name': "Assistant conversationnel activé",
        'category': 'core',
        'default_value': True,
    },
    {
        'code': 'assistant.context_capture',
        'name': "Capture automatique du contexte courant",
        'category': 'core',
        'default_value': True,
    },
    {
        'code': 'assistant.show_tool_calls',
        'name': "Afficher les appels d'outils dans l'UI (mode debug)",
        'category': 'debug',
        'default_value': False,
    },
]
```

### Tests de la tâche 3

- `test_assistant_no_root_menu.py` : vérifie qu'aucun menuitem racine n'est créé par `tc_assistant`.
- `test_assistant_context_capture.py` : une requête avec contexte implicite est correctement résolue.
- `test_assistant_tool_use_loop.py` : une question nécessitant plusieurs outils enchaîne correctement.
- `test_assistant_anti_hallucination.py` (property-based, 50 cas) : aucun chiffre hors outils.
- `test_assistant_budget_limit.py` : l'assistant refuse proprement quand le budget est dépassé.
- `test_assistant_tenant_isolation.py` : isolation multi-tenant sur les réponses.
- `test_assistant_persistence.py` : le panneau survit à une navigation simulée.
- Scénarios BDD selon la fiche `CAPABILITY_tc_assistant.md` (6 scénarios minimum).

## Tâche 4 — Suppression des artefacts WhatsApp/SMS/email du code livré

Si le code de `tc_assistant_proactive` contient déjà des ébauches pour ces canaux (classes, fichiers, imports), **les conserver mais désactivés par défaut via les flags de canaux**. Ne pas les supprimer physiquement, ils seront activés en phase C/D.

S'assurer qu'aucun appel effectif à une API externe (Meta, Twilio, etc.) ne peut être déclenché tant que les flags correspondants sont à `False`. Un test dédié doit le vérifier.

## Tâche 5 — Patches documentaires

**Attention** : cette tâche modifie les documents fondateurs. Elle est autorisée uniquement dans le cadre précis de ce sprint, pour intégrer les décisions prises ci-dessus. Tout autre changement sur ces documents reste interdit.

### Patch 5.1 — `CAPABILITY_CATALOG.md`

- Ajouter `tc_feature_flags` dans le tableau synthétique, ligne 5 (avant les capabilities applicatives), famille 1, vague MVP, socle.
- Incrémenter les numéros des capabilities suivantes en conséquence.
- Ajouter une section détaillée pour `tc_feature_flags` dans la famille 1, avec son rôle, ses modèles, ses critères d'acceptation, conformément au format des autres fiches.

### Patch 5.2 — `ARCHITECTURE_PRINCIPLES.md`

Ajouter une section `§19 — Règles sur les feature flags` :

```markdown
### §19. Règles sur les feature flags

🔴 NON-NÉGOCIABLE

1. Tout comportement optionnel ou évolutif d'une capability est contrôlé par un feature flag déclaré dans son fichier `feature_flags.py`.
2. Les feature flags remplacent tout paramètre de configuration modifiable à chaud. Jamais de paramètre en dur ni en code.
3. Chaque flag a une valeur par défaut sûre (généralement `False` pour les nouvelles features non encore éprouvées).
4. L'activation d'un flag ne nécessite jamais un redéploiement ni une modification du `tenant_profile.yaml`.
5. Tout test métier peut forcer un flag via un décorateur de test standardisé `@with_feature_flag('code', active=True/False)`.
6. Tout flag est documenté : à quoi il sert, quel comportement il active, quel est l'impact quand il est inactif.
7. Un flag jamais activé par aucun tenant pendant 12 mois doit être signalé pour décommissionnement (éviter la dette de code mort).
```

### Patch 5.3 — `PRODUCT_VISION.md`

Ajouter dans la section sur le positionnement produit une phrase sur la double adaptabilité :

> TelecomERP s'adapte à chaque entreprise à deux niveaux. Le profil d'installation définit la **structure** : quelles capabilities sont activées, quelle est l'organisation, quels sont les workflows. Les **feature flags** permettent ensuite à l'administrateur du tenant d'activer ou désactiver finement les comportements à tout moment, sans redéploiement ni intervention technique. Cette double adaptabilité est ce qui permet au produit de joindre le spécifique au général.

### Patch 5.4 — Fiche `tc_assistant_proactive`

Dans la fiche existante :

- Remplacer la section "Canaux de livraison MVP" par : *"Canaux actifs en V1.5 : in-app uniquement. Les autres canaux (email, WhatsApp, SMS) sont livrés en code mais désactivés par défaut via feature flags. Leur activation éventuelle fait l'objet d'une validation spécifique après 3 mois d'usage in-app."*
- Remplacer la section "Calendrier de livraison" par une logique de rollout via flags : tous les watchers sont livrés en code, 3 sont actifs par défaut (pilotes), les autres sont activables individuellement par l'admin selon ses besoins.
- Conserver toutes les autres sections.

### Patch 5.5 — `TEST_HARNESS_SPEC.md`

Ajouter une sous-section dans la couche 2 (tests d'architecture) :

- Test : tout module qui a un comportement conditionnel à un flag doit l'avoir enregistré dans son `feature_flags.py`.
- Test : aucun code de production ne doit référencer un flag par un `code` non déclaré.
- Test : tout flag déclaré doit avoir au moins un test qui vérifie les deux états (actif/inactif).

## Tâche 6 — Vérification des tests

Après toutes les modifications :

1. Lancer la suite Odoo sur un environnement propre :
   ```bash
   docker compose exec odoo odoo -d test_flags --init=tc_feature_flags,tc_assistant,tc_assistant_proactive --test-enable --stop-after-init
   ```
2. Lancer `pytest custom_addons/tc_feature_flags/ custom_addons/tc_assistant_proactive/ -v`.
3. Vérifier que les flags de `tc_assistant_proactive` sont bien enregistrés à l'install et que les valeurs par défaut sont correctes (3 watchers pilotes à `True`, tous les autres à `False`).
4. Vérifier manuellement via l'UI Odoo que l'écran d'administration des flags est accessible, fonctionnel, et que désactiver un flag empêche bien le watcher correspondant de générer des notifications.

## Livrable final

Rédiger `docs/sprint_feature_flags_rapport.md` contenant :

1. Récapitulatif de la capability `tc_feature_flags` créée (fichiers, modèles, vues, tests).
2. Liste des flags déclarés dans `tc_assistant_proactive` avec leur valeur par défaut.
3. Confirmation que tous les patches documentaires ont été appliqués (checklist).
4. Résultats des tests (unitaires, intégration, BDD).
5. Anomalies rencontrées et non résolues.
6. Recommandations pour les sprints suivants (ajout de flags dans d'autres capabilities ? besoin d'une API REST pour piloter les flags ?).

## Definition of Done de ce sprint

**Bloc feature flags**
- [ ] `tc_feature_flags` existe en tant que capability du socle, installée par défaut.
- [ ] Les modèles `feature.flag` et `feature.flag.history` sont créés avec leurs contraintes.
- [ ] Le décorateur `@feature_flag` fonctionne et est testé (fail-safe à `False` si flag inconnu).
- [ ] Le mécanisme de découverte automatique charge les flags depuis `feature_flags.py`.
- [ ] L'écran d'administration est accessible et fonctionnel (groupe Admin TelecomERP).

**Bloc widget popup tc_assistant**
- [ ] Le widget OWL global est monté dans la chrome Odoo, FAB visible sur toutes les pages.
- [ ] Aucun menuitem racine ni page dédiée n'est créé pour l'assistant (sauf l'exception "Historique" accessible depuis le widget).
- [ ] Le panneau de chat persiste à travers les navigations.
- [ ] La capture du contexte courant est automatique et testée.
- [ ] Les 5 outils MVP sont implémentés et testés individuellement.
- [ ] La boucle de tool-use avec l'API Claude fonctionne.
- [ ] Le test anti-hallucination property-based passe sur 50 cas.
- [ ] L'isolation multi-tenant est vérifiée.
- [ ] Le budget LLM par tenant est appliqué.
- [ ] Les 3 flags de `tc_assistant` sont déclarés et fonctionnels.

**Bloc tc_assistant_proactive**
- [ ] Le fichier `feature_flags.py` couvre tous les watchers et tous les canaux.
- [ ] Les watchers utilisent le décorateur et sont conditionnés à leurs flags.
- [ ] Les canaux email/WhatsApp/SMS sont livrés mais désactivés par défaut, sans appel externe possible.
- [ ] 3 watchers pilotes sont actifs par défaut, tous les autres inactifs.

**Bloc documentation**
- [ ] Les patches documentaires sont appliqués strictement (5 patches au total).
- [ ] Aucune modification de doc hors du périmètre autorisé.

**Bloc transverse**
- [ ] La suite de tests passe au vert (Odoo + pytest + BDD).
- [ ] Aucune capability hors périmètre n'a été modifiée.
- [ ] Le rapport de sprint est rédigé dans `docs/sprint_feature_flags_rapport.md`.

**Bloc validation humaine**
- [ ] Marouane a validé chaque tâche séparément avant passage à la suivante.
- [ ] Un test manuel du widget popup sur une instance preview a été effectué et documenté dans le rapport.

## Règles de comportement

1. **Lis les 6 documents fondateurs en début de session.** Aucune action avant.
2. **Traite les tâches dans l'ordre.** Commit à la fin de chaque tâche.
3. **Sur les patches documentaires, aucune liberté créative.** Appliquer strictement ce qui est décrit, rien de plus.
4. **Si une ambiguïté apparaît, arrête-toi et signale.** Ne devine pas.
5. **Co-author tous tes commits avec Claude** selon la convention du projet.

---

*Fin du brief.*
