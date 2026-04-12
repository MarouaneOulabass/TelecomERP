# Sprint Feature Flags — Rapport

> Date : 2026-04-10
> Auteur : Claude Code (autonome)
> Statut : Livrable complet, en attente de validation humaine

---

## 1. Recap de la capability telecom_feature_flags

### Fichiers crees

```
custom_addons/telecom_feature_flags/
    __init__.py
    __manifest__.py
    hooks.py                          # post_init_hook pour decouverte automatique
    models/
        __init__.py
        feature_flag.py               # Modele feature.flag
        feature_flag_history.py       # Modele feature.flag.history (audit)
    utils/
        __init__.py
        feature_flag.py               # is_flag_active(), register_flags(), @feature_flag
    views/
        feature_flag_views.xml        # Tree, Kanban, Form, Search views
        menu_views.xml                # Menu sous Configuration
    security/
        telecom_security.xml          # Record rules (Responsable read, Admin full)
        ir.model.access.csv           # ACLs
    tests/
        __init__.py
        features/
            feature_flags.feature     # 4 scenarios BDD en francais
        test_bdd_feature_flags.py     # Step definitions
```

### Modeles

| Modele | Champs cles |
|---|---|
| `feature.flag` | code (unique, pattern valide), name, description, capability, category (selection), default_value, active, last_changed_by, last_changed_at, history_ids |
| `feature.flag.history` | flag_id (cascade), changed_by, changed_at, old_value, new_value, reason |

### Utilitaires Python

- `is_flag_active(code, env)` : retourne True/False, False si flag inconnu
- `register_flags(capability_name, flags_list, env)` : enregistrement idempotent
- `@feature_flag('code')` : decorateur qui skip la methode si flag inactif

### Mecanisme de decouverte

Le `post_init_hook` scanne tous les modules `telecom_*` installes a la recherche d'un fichier `feature_flags.py` exposant une variable `FLAGS`.

---

## 2. Liste des flags declares dans telecom_assistant_proactive

| Code | Nom | Categorie | Valeur par defaut |
|---|---|---|---|
| `assistant_proactive.watcher_marge_sous_seuil` | Alerte marge sous seuil | watchers | **True** |
| `assistant_proactive.watcher_caution_expirant` | Alerte caution expirant | watchers | **True** |
| `assistant_proactive.watcher_pointage_manquant` | Alerte pointage manquant | watchers | **True** |
| `assistant_proactive.watcher_facture_impayee` | Alerte facture impayee J+30 | watchers | False |
| `assistant_proactive.watcher_habilitation_expirant` | Alerte habilitation expirant | watchers | False |
| `assistant_proactive.watcher_derive_marge_hebdo` | Alerte derive marge hebdo | watchers | False |
| `assistant_proactive.watcher_sla_depasse` | Alerte SLA depasse | watchers | False |
| `assistant_proactive.channel_in_app` | Canal in-app | channels | **True** |
| `assistant_proactive.channel_email` | Canal email | channels | False |
| `assistant_proactive.channel_whatsapp` | Canal WhatsApp | channels | False |
| `assistant_proactive.digest_matinal` | Digest matinal | ux | False |

### Flags declares dans telecom_assistant

| Code | Nom | Categorie | Valeur par defaut |
|---|---|---|---|
| `assistant.enabled` | Assistant active | core | **True** |
| `assistant.context_capture` | Capture contexte | core | **True** |
| `assistant.show_tool_calls` | Afficher appels outils (debug) | debug | False |

---

## 3. Patches documentaires appliques

- [x] **ARCHITECTURE_PRINCIPLES.md** : Section 17 ajoutee — Regles sur les feature flags (7 regles non-negociables)
- [x] **CAPABILITY_CATALOG.md** : telecom_feature_flags ajoute en ligne 5 du tableau synthetique + section detaillee dans Famille 1
- [x] **PRODUCT_VISION.md** : Paragraphe sur la double adaptabilite ajoute dans la section positionnement
- [x] **TEST_HARNESS_SPEC.md** : 3 tests d'architecture ajoutes dans la couche 2 (flags declares, references valides, deux etats testes)

---

## 4. Resultats des tests

### Tests BDD telecom_feature_flags (4 scenarios)

| Scenario | Statut |
|---|---|
| Activation d'un flag change le comportement | Implemente |
| Enregistrement idempotent des flags | Implemente |
| Refus d'un code de flag malforme | Implemente |
| Le decorateur feature_flag bloque si inactif | Implemente |

### Tests BDD telecom_assistant_proactive (4 scenarios)

| Scenario | Statut |
|---|---|
| Watcher avec flag desactive ne genere pas de notification | Implemente |
| Watcher avec flag actif genere des notifications | Implemente |
| Fallback canal si WhatsApp desactive | Implemente |
| Notification marquee comme lue | Implemente |

Note : Les tests sont ecrits pour execution avec pytest + pytest-bdd en mode mock (sans instance Odoo). L'execution complete sur instance Docker n'a pas ete realisee (interdit par les regles du sprint).

---

## 5. Anomalies rencontrees et non resolues

1. **Pas de CAPABILITY_tc_assistant_proactive.md existant** : Le sprint brief referençait ce document mais il n'existe pas. Le module telecom_assistant_proactive a ete cree from scratch conformement aux specifications du brief.

2. **Dependances telecom_cost et telecom_margin** : Le module telecom_assistant_proactive declare des dependances vers ces modules. Les watchers correspondants utilisent des `env.get()` defensifs pour eviter les crashs si les modeles ne sont pas disponibles.

3. **Widget OWL et controleur HTTP** (Tache 3 du sprint brief original) : Le brief original incluait une tache 3 complete pour tc_assistant (widget popup global, backend agent, 5 outils MVP, anti-hallucination). Cette tache est **hors perimetre** de l'instruction utilisateur qui se concentrait sur les feature flags. Le module telecom_assistant existant a ete enrichi uniquement avec `feature_flags.py` et la dependance ajoutee.

---

## 6. Recommandations pour les sprints suivants

1. **Ajout de flags dans d'autres capabilities** : Les modules telecom_site, telecom_intervention, telecom_hr_ma pourraient beneficier de flags pour des fonctionnalites optionnelles (ex: GPS obligatoire, signature electronique, pointage geolocalise).

2. **API REST pour piloter les flags** : Pour l'automatisation et le control plane, exposer les flags via un endpoint JSON-RPC ou REST permettrait le pilotage programmatique.

3. **Dashboard de monitoring des flags** : Un tableau de bord montrant l'utilisation reelle des flags (combien de tenants activent chaque flag) aiderait au decommissionnement des flags inutilises (regle des 12 mois).

4. **Tests d'integration complets** : Executer les tests sur une instance Odoo reelle avec Docker pour valider le cycle complet : installation, decouverte automatique, toggle via UI, verification du comportement conditionnel.

5. **Canaux email/WhatsApp/SMS** : Le code est livre mais desactive par defaut. Un sprint dedie pourra activer ces canaux apres 3 mois d'usage in-app, conformement au plan de rollout.

---

*Fin du rapport.*
