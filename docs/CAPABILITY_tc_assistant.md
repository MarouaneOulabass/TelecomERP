# Fiche capability — tc_assistant

> À insérer dans `CAPABILITY_CATALOG.md`, famille 2 (Pilotage projet et rentabilité) ou nouvelle famille 6 (Intelligence transverse), vague V1.5.
>
> Modifications associées requises :
> - Mise à jour du tableau synthétique du catalogue (capability #27)
> - Ajout d'une section dans `ARCHITECTURE_PRINCIPLES.md` (voir fin de ce fichier)
> - Ajout d'une section dans `TENANT_PROFILE_SCHEMA.json` (voir fin de ce fichier)

---

## 27. tc_assistant — Assistant conversationnel contextuel

**Vague** : V1.5 — **Statut** : Optionnelle

**Famille** : 6 (nouvelle — Intelligence transverse) ou 2 (pilotage)

### Rôle

Permet à un utilisateur autorisé de poser en langage naturel (français, darija, arabe) des questions sur les données de son tenant et d'obtenir des réponses précises, traçables, et formulées dans son vocabulaire métier.

L'assistant ne lit jamais directement la base. Il utilise un **agent LLM avec accès à un catalogue d'outils typés** (function calling). Chaque capability métier est responsable d'exposer ses propres outils au registry de l'assistant via un fichier `assistant_tools.py` standardisé.

### Principe architectural fondamental

**L'assistant est un agent à tool-use, pas un RAG vectoriel central.**

Cette distinction est non-négociable et structure tout le reste :

- Les questions structurées (montants, listes, statuts, agrégats) passent par des **outils SQL typés** qui retournent des données exactes.
- Les questions sémantiques sur du contenu non structuré (PV, photos, emails, contrats) passent par un **outil de recherche vectorielle** parmi les autres outils du catalogue, pas comme architecture centrale.
- L'agent LLM (Claude via API) reçoit la question, choisit le ou les bons outils, les appelle, et formule une réponse en langage naturel à partir des résultats exacts.

### Pourquoi ce design

1. **Réponses chiffrées exactes** : pas d'hallucination de montants, parce qu'ils viennent de requêtes SQL réelles. Critique pour un ERP — une seule erreur de chiffre détruit la confiance.
2. **Multi-tenant naturel** : chaque appel d'outil passe par le contexte tenant, aucune fuite cross-tenant possible.
3. **Modulaire** : chaque capability reste responsable d'exposer ses propres outils. L'assistant agrège, il n'invente pas.
4. **Traçable** : pour chaque réponse, on logge la question, les outils appelés, leurs paramètres, leurs résultats, et la réponse finale. Audit complet.
5. **Permissions** : un utilisateur ne voit via l'assistant que ce qu'il a le droit de voir via l'UI standard. Les outils respectent les `record rules` Odoo.

### Exemples de questions cibles

| Question utilisateur | Outil(s) appelé(s) | Type |
|---|---|---|
| "Donne-moi les 3 dernières factures du client Atlas" | `get_invoices(partner="Atlas", limit=3, order="date_desc")` | Structurée simple |
| "On a reçu le paiement de la facture de la tâche déploiement du chantier Casa-Nord ?" | `find_task` → `get_invoices_for_task` → `get_payments_for_invoice` | Relationnelle multi-tables |
| "Pourquoi la marge du chantier Rabat-Sud a baissé cette semaine ?" | `get_margin_history` + `get_cost_breakdown` + raisonnement LLM | Analyse |
| "Trouve-moi le PV qui mentionne le problème de raccordement à Aïn Sebaâ" | `search_documents(query, doc_type="pv_reception")` | Sémantique |
| "Quels techniciens ont pointé sur le site Tour-Marrakech-12 cette semaine ?" | `get_pointages(site, week)` | Structurée multi-filtres |
| "Combien on a dépensé en carburant sur le projet 5G-Fès en mars ?" | `get_costs(project, type="carburant", month="2026-03")` | Agrégation |

### Modèle de données

- `AssistantConversation` : conversation utilisateur, historique
- `AssistantMessage` : message individuel (user ou assistant), horodaté
- `AssistantToolCall` : trace de chaque appel d'outil (outil, params, résultat, durée)
- `AssistantToolRegistry` : enregistrement runtime des outils exposés par les capabilities actives

### Dépendances dures (TelecomERP only)

- `tc_core`
- `tc_security`

### Dépendances souples (chacune ajoute des outils au registry)

- `tc_project` → `get_project`, `get_projects_for_partner`, `find_project`, `find_lot`, `find_task`
- `tc_cost_tracking` → `get_costs`, `get_cost_breakdown`, `get_costs_for_project`
- `tc_margin_dashboard` → `get_margin`, `get_margin_history`, `get_margin_alerts`
- `tc_facturation` → `get_invoices`, `get_invoices_for_task`, `get_payment_status`
- `tc_intervention` → `get_interventions`, `find_intervention`
- `tc_site` → `get_sites`, `find_site`
- `tc_hr_core` → `get_employees_on_project`, `find_employee`
- `tc_pointage_gps` → `get_pointages`
- `tc_carburant` → `get_fuel_consumption_for_project`
- `tc_situation_travaux` → `get_situations`, `get_decompte_status`
- `tc_cautions` → `get_cautions_status`, `get_cautions_expiring_soon`

### Outils MVP de l'assistant (5 outils minimum pour livrer la capability)

Avant de coder de nouveaux outils, ces 5 doivent être livrés et testés. Ils couvrent ~80% des questions attendues.

1. **`get_invoices(partner_id?, project_id?, status?, date_range?, limit?)`** — exposé par `tc_facturation`
2. **`get_payment_status(invoice_id?, task_id?, project_id?)`** — exposé par `tc_facturation`
3. **`get_project_status(project_id_or_name)`** — exposé par `tc_margin_dashboard` (retourne marge, avancement, alertes, derniers coûts)
4. **`get_interventions(site_id?, technician_id?, date_range?, status?)`** — exposé par `tc_intervention`
5. **`search_documents(query, doc_type?, project_id?)`** — exposé par `tc_assistant` lui-même (utilise un index vectoriel sur les pièces jointes)

### Critères d'acceptation

- L'assistant ne contient **aucune référence directe à un modèle Odoo**. Il n'utilise que les outils déclarés dans le registry.
- Toute capability optionnelle peut ajouter ses outils sans modifier `tc_assistant`.
- Les réponses chiffrées proviennent **exclusivement** des outils, jamais générées par le LLM.
- Toute conversation est tracée (question, outils appelés, paramètres, résultats, réponse finale).
- L'assistant respecte les record rules : un user ne voit via chat que ce qu'il voit via l'UI.
- L'assistant fonctionne en français, darija (transcrit) et arabe.
- En cas d'absence d'outil pertinent, l'assistant le dit explicitement au lieu d'inventer une réponse.
- Limite de coût configurable par tenant (max d'appels LLM par jour, alerte au seuil).

### Scénarios BDD clés

```gherkin
Scénario : Question sur des factures existantes
  Étant donné un client "Atlas Telecom" avec 5 factures
  Quand un utilisateur demande "donne-moi les 3 dernières factures d'Atlas Telecom"
  Alors l'assistant appelle l'outil get_invoices avec partner="Atlas Telecom" et limit=3
  Et la réponse contient exactement 3 factures
  Et les montants correspondent exactement aux montants en base

Scénario : Question multi-tables relationnelle
  Étant donné un projet "Casa-Nord" avec une tâche "Déploiement fibre"
  Et une facture émise pour cette tâche, encore impayée
  Quand un utilisateur demande "on a reçu le paiement de la facture de la tâche Déploiement fibre du chantier Casa-Nord ?"
  Alors l'assistant répond clairement "Non, facture en attente"
  Et il précise la date d'émission et le montant exact

Scénario : Question hors périmètre
  Étant donné qu'aucun outil ne couvre la météo
  Quand un utilisateur demande "quel temps fera-t-il demain à Rabat ?"
  Alors l'assistant répond qu'il n'a pas d'outil pour cette question
  Et il propose des questions qu'il peut traiter

Scénario : Isolation multi-tenant
  Étant donné deux tenants A et B avec des données distinctes
  Quand un utilisateur du tenant A pose une question
  Alors aucun appel d'outil ne retourne de donnée du tenant B
  Et les logs confirment l'isolation

Scénario : Hallucination interdite
  Étant donné une question dont l'outil retourne 0 résultat
  Quand l'assistant formule sa réponse
  Alors la réponse indique explicitement qu'aucune donnée n'a été trouvée
  Et aucun chiffre n'est inventé
```

### Limites et budget

- **Coût LLM par tenant** : configuré dans le tenant_profile (`assistant.monthly_budget_mad`). Au-delà, l'assistant est désactivé jusqu'au mois suivant ou jusqu'au paiement d'un dépassement.
- **Modèle LLM par défaut** : Claude Sonnet (équilibre coût/qualité). Configurable au niveau tenant pour les clients qui veulent Haiku (moins cher) ou Opus (plus précis).
- **Latence cible** : <5 secondes pour une question simple, <15 secondes pour une question multi-outils.

---

## Modifications à apporter aux autres documents

### Modification de `ARCHITECTURE_PRINCIPLES.md`

Ajouter une nouvelle section §17 :

> **17. Règles sur l'assistant conversationnel**
>
> 🔴 NON-NÉGOCIABLE
>
> 1. **L'assistant n'accède jamais directement aux modèles Odoo.** Il utilise exclusivement les outils déclarés dans le `AssistantToolRegistry`.
> 2. **Toute capability qui veut exposer des données à l'assistant le fait via un fichier `assistant_tools.py`** à la racine du module, qui déclare des fonctions Python typées et documentées.
> 3. **Les outils retournent du JSON sérialisable**, jamais des objets Odoo bruts.
> 4. **Les chiffres présents dans une réponse de l'assistant proviennent exclusivement des outils.** Aucun nombre ne peut être généré par le LLM lui-même. Vérifié par un test de propriété.
> 5. **Tout appel d'outil respecte les record rules Odoo.** Un user n'obtient jamais via l'assistant ce qu'il ne pourrait pas obtenir via l'UI.
> 6. **Toute conversation est intégralement loggée** : question, outils appelés, paramètres, résultats, réponse, durée, coût en tokens.
> 7. **Le budget LLM par tenant est plafonné** par configuration. Au-delà, l'assistant est désactivé proprement (pas de plantage silencieux).

### Modification de `TENANT_PROFILE_SCHEMA.json`

Ajouter dans `properties` :

```json
"assistant": {
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean",
      "default": false,
      "description": "Active la capability tc_assistant"
    },
    "model": {
      "type": "string",
      "enum": ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-6"],
      "default": "claude-sonnet-4-6"
    },
    "monthly_budget_mad": {
      "type": "integer",
      "minimum": 50,
      "maximum": 10000,
      "default": 300,
      "description": "Budget mensuel maximum pour les appels LLM en MAD"
    },
    "languages": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["fr", "ar", "darija"]
      },
      "default": ["fr"]
    }
  }
}
```

### Modification du tableau synthétique de `CAPABILITY_CATALOG.md`

Ajouter une ligne :

```
| 27 | tc_assistant | Assistant conversationnel | 6 | V1.5 | Optionnelle |
```

Et créer la famille 6 dans le préambule :
> **Famille 6 — Intelligence transverse** : capabilities qui s'appuient sur les données produites par toutes les autres familles pour offrir une couche d'usage transversale (assistant conversationnel, futurs agents d'analyse, prévisionnels).

---

## Pourquoi V1.5 et pas MVP

Cette capability est ajoutée en V1.5 et non en MVP pour 3 raisons :

1. **Elle a besoin de données structurées pour avoir de la valeur.** Avant que `tc_cost_tracking`, `tc_margin_dashboard`, `tc_facturation` et `tc_intervention` soient stables et alimentés par le design partner, l'assistant aurait un placard vide et fournirait une démo creuse qui dégraderait sa propre crédibilité.

2. **L'avantage data réelle (via la société de l'associé) joue dès qu'il y a des données saisies**, pas avant l'écriture des modèles. Donc cet avantage se matérialise pendant la phase MVP, et l'assistant peut être codé immédiatement après.

3. **Le périmètre des outils utiles ne sera connu qu'après observation** des questions réellement posées par l'associé pendant 4-6 semaines d'usage du MVP. Coder 30 outils en mode spéculatif est garanti d'en produire 25 inutiles.

### Calendrier indicatif

- **Mois 1-2** : MVP (sans assistant). Le design partner saisit ses données réelles.
- **Mois 3** : observation des questions naturelles posées par l'associé sur ses propres données. Carnet de questions tenu par Marouane.
- **Mois 4** : codage de `tc_assistant` avec les 5 outils MVP, basés sur le carnet de questions.
- **Mois 5-6** : enrichissement progressif du catalogue d'outils en fonction des usages réels.

---

*Fin de la fiche.*
