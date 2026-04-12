# Sprint Correction Assistant — Rapport

## Correction 1 : Suppression des menuitems racines

**Statut : COMPLÉTÉ**

Le fichier `custom_addons/telecom_assistant/views/menu_views.xml` a été vidé de ses 3 menuitems (`menu_assistant_root`, `menu_assistant_new`, `menu_assistant_history`). Le widget popup flottant (FAB en bas à droite) est désormais le seul mode d'accès à l'assistant. L'historique des conversations reste accessible via l'action `action_assistant_conversation` appelable depuis le widget.

Un test BDD vérifie cette règle : `Scénario: Aucun menu racine n'existe pour l'assistant`.

## Correction 2 : Tests manquants

**Statut : COMPLÉTÉ (6 BDD + 1 property-based)**

### 6 scénarios BDD (`tests/features/assistant.feature`)

1. **Aucun menu racine** — vérifie qu'aucun menuitem racine n'est créé
2. **Registry 7+ outils** — vérifie que le registry contient au moins 7 outils
3. **list_projects fonctionnel** — appelle l'outil et vérifie le résultat
4. **get_sites fonctionnel** — appelle l'outil et vérifie le résultat
5. **Création conversation** — crée une conversation et vérifie l'utilisateur
6. **JSON sérialisable** — vérifie que les résultats d'outils sont sérialisables

### Test anti-hallucination property-based (`tests/test_anti_hallucination.py`)

50 appels d'outils avec paramètres variés (randomisés). Pour chaque résultat :
- **Propriété 1** : aucun NaN ou Inf dans les nombres retournés
- **Propriété 2** : aucun nombre > 1 milliard MAD (magnitude raisonnable)
- **Propriété 3** : vérification structurelle (pas de nombres impossibles)

**Limitation honnête** : ce test vérifie l'intégrité des outils, pas la réponse de Claude. Un vrai test anti-hallucination bout-en-bout nécessiterait d'appeler l'API Claude (coût + latence incompatibles avec la CI). La garantie anti-hallucination repose sur le design : les outils retournent des chiffres exacts, et le system prompt interdit à Claude de générer des chiffres non fournis par un outil.

## Correction 3 : État de l'intégration Claude API

**Statut : VÉRIFIÉ + AMÉLIORÉ**

### Constat

L'intégration est **réelle, pas un stub**. Le flow complet :

1. `controllers/assistant_chat.py` reçoit le message via JSON-RPC
2. Crée/récupère la conversation (`telecom.assistant.conversation`)
3. Appelle `conv.action_send()` dans `models/assistant_conversation.py`
4. `action_send()` appelle `client.messages.create()` de la SDK Anthropic avec :
   - `model='claude-sonnet-4-20250514'`
   - `tools=` registry d'outils (8 outils enregistrés)
   - Boucle de tool-use (max 5 itérations)
5. Chaque appel d'outil est tracé dans `telecom.assistant.tool.call`
6. La réponse finale est stockée avec le compteur de tokens

### Améliorations apportées

- **Timeout** : ajout de `timeout=30.0` sur chaque appel API Claude
- **Budget check** : vérification du nombre total de tokens avant chaque appel, avec paramètre système `telecom.assistant_monthly_token_limit` (défaut 500 000 tokens)
- **Gestion d'erreur** : déjà en place via try/except, retourne un message d'erreur propre à l'utilisateur

### Ce qui manque encore (hors périmètre de ce sprint)

- Streaming de la réponse (l'utilisateur attend la réponse complète)
- Persistance du panneau popup à travers les navigations (dépend du framework OWL)
- Test d'isolation multi-tenant (nécessite 2 bases de test)

## Fichiers modifiés

| Fichier | Action |
|---------|--------|
| `telecom_assistant/views/menu_views.xml` | Vidé des 3 menuitems racines |
| `telecom_assistant/models/assistant_conversation.py` | Ajout timeout + budget check |
| `telecom_assistant/tests/__init__.py` | Créé |
| `telecom_assistant/tests/features/assistant.feature` | Créé — 6 scénarios |
| `telecom_assistant/tests/test_bdd_assistant.py` | Créé — step definitions |
| `telecom_assistant/tests/test_anti_hallucination.py` | Créé — property-based 50 cas |
| `docs/sprint_correction_assistant_rapport.md` | Ce rapport |

## Aucune autre modification effectuée

Conformément au brief, aucun fichier en dehors du périmètre n'a été modifié.
