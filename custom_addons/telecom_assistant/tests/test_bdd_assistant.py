# -*- coding: utf-8 -*-
"""
BDD step definitions — telecom_assistant
==========================================
"""
import json
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

pytestmark = pytest.mark.assistant

scenarios('features/')


# ── No root menu ──────────────────────────────────────────────────

@when('je cherche les menus racines de l\'assistant')
def when_search_root_menus(env, context):
    menus = env['ir.ui.menu'].search([
        ('parent_id', '=', False),
    ])
    assistant_roots = []
    for m in menus:
        xid = m.get_external_id().get(m.id, '')
        if 'telecom_assistant' in xid:
            assistant_roots.append(m.name)
    context['assistant_root_menus'] = assistant_roots


@then('aucun menu racine n\'est trouvé pour telecom_assistant')
def then_no_root_menu(context):
    menus = context.get('assistant_root_menus', [])
    assert len(menus) == 0, (
        'Menus racines trouvés pour telecom_assistant: %s' % menus
    )


# ── Tool registry ────────────────────────────────────────────────

@when('je consulte le registry d\'outils de l\'assistant')
def when_check_registry(env, context):
    from odoo.addons.telecom_assistant.models.assistant_tool_registry import get_tool_names
    context['tool_names'] = get_tool_names()


@then(parsers.parse('au moins {n:d} outils sont enregistrés'))
def then_tools_count(context, n):
    names = context.get('tool_names', [])
    assert len(names) >= n, (
        'Outils enregistrés: %d (attendu >= %d). Outils: %s' % (len(names), n, names)
    )


@when(parsers.parse('j\'appelle l\'outil "{tool_name}" sans paramètres'))
def when_call_tool(env, tool_name, context):
    from odoo.addons.telecom_assistant.models.assistant_tool_registry import call_tool
    try:
        result = call_tool(tool_name, env, {})
        context['tool_result'] = result
        context['tool_error'] = None
    except Exception as e:
        context['tool_result'] = None
        context['tool_error'] = str(e)


@then('le résultat contient une liste de projets')
def then_result_has_projects(context):
    result = context.get('tool_result')
    assert result is not None, 'Erreur: %s' % context.get('tool_error')
    assert 'projects' in result or 'count' in result, (
        'Résultat inattendu: %s' % str(result)[:200]
    )


@then('le résultat contient une liste de sites')
def then_result_has_sites(context):
    result = context.get('tool_result')
    assert result is not None, 'Erreur: %s' % context.get('tool_error')
    assert 'sites' in result or 'count' in result, (
        'Résultat inattendu: %s' % str(result)[:200]
    )


@then('le résultat est sérialisable en JSON')
def then_result_json_serializable(context):
    result = context.get('tool_result')
    assert result is not None, 'Erreur: %s' % context.get('tool_error')
    serialized = json.dumps(result, ensure_ascii=False, default=str)
    assert len(serialized) > 2, 'Résultat vide'


# ── Conversations ────────────────────────────────────────────────

@when('je crée une nouvelle conversation assistant')
def when_create_conversation(env, context):
    conv = env['telecom.assistant.conversation'].create({})
    context['conversation'] = conv


@then('la conversation est créée avec succès')
def then_conversation_created(context):
    conv = context.get('conversation')
    assert conv and conv.id, 'Conversation non créée'


@then('l\'utilisateur est l\'utilisateur courant')
def then_user_is_current(env, context):
    conv = context['conversation']
    assert conv.user_id.id == env.user.id
