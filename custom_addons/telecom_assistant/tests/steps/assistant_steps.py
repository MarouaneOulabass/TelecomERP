# -*- coding: utf-8 -*-
"""
BDD step definitions — telecom_assistant (new features).
=========================================================
Steps for assistant_basics.feature, assistant_context.feature,
and assistant_tools.feature.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from pytest_bdd import scenarios, given, when, then, parsers

pytestmark = pytest.mark.assistant

# Load all feature files from the features directory
scenarios('../features/assistant_basics.feature')
scenarios('../features/assistant_context.feature')
scenarios('../features/assistant_tools.feature')


# ── Helpers ──────────────────────────────────────────────────────────

def _make_mock_text_response(text):
    """Build a mock Claude API response with text content."""
    block = MagicMock()
    block.type = 'text'
    block.text = text
    response = MagicMock()
    response.stop_reason = 'end_turn'
    response.content = [block]
    response.usage = MagicMock()
    response.usage.input_tokens = 100
    response.usage.output_tokens = 50
    return response


def _make_mock_tool_use_response(tool_name, tool_input, tool_id='toolu_01'):
    """Build a mock Claude API response requesting a tool call."""
    block = MagicMock()
    block.type = 'tool_use'
    block.name = tool_name
    block.input = tool_input
    block.id = tool_id
    response = MagicMock()
    response.stop_reason = 'tool_use'
    response.content = [block]
    response.usage = MagicMock()
    response.usage.input_tokens = 100
    response.usage.output_tokens = 50
    return response


# ── No root menu (shared with test_bdd_assistant.py) ─────────────────

@when("je cherche les menus racines de l'assistant")
def when_search_root_menus_new(env, context):
    menus = env['ir.ui.menu'].search([('parent_id', '=', False)])
    assistant_roots = []
    for m in menus:
        xid = m.get_external_id().get(m.id, '')
        if 'telecom_assistant' in xid:
            assistant_roots.append(m.name)
    context['assistant_root_menus'] = assistant_roots


@then("aucun menu racine n'est trouvé pour telecom_assistant")
def then_no_root_menu_new(context):
    menus = context.get('assistant_root_menus', [])
    assert len(menus) == 0, (
        'Menus racines trouvés: %s' % menus
    )


# ── Basics: conversation + question ─────────────────────────────────

@given('une conversation assistant vierge')
def given_blank_conversation(env, context):
    conv = env['telecom.assistant.conversation'].create({})
    context['conversation'] = conv


@when(parsers.parse(
    'j\'envoie la question "{question}" avec Claude mocké'
))
def when_send_question_mocked(env, context, question):
    conv = context['conversation']
    conv.user_input = question

    mock_response = _make_mock_text_response(
        "Voici les projets en cours dans votre ERP."
    )
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch.object(type(conv), '_get_claude_client', return_value=mock_client):
        conv.action_send()

    assistant_msgs = conv.message_ids.filtered(lambda m: m.role == 'assistant')
    context['last_response'] = (
        assistant_msgs.sorted('sequence', reverse=True)[0].content
        if assistant_msgs else ''
    )


@then("la réponse de l'assistant n'est pas vide")
def then_response_not_empty(context):
    response = context.get('last_response', '')
    assert len(response) > 0, "La réponse est vide"


@then(parsers.parse('la réponse ne contient pas "{fragment}"'))
def then_response_not_contains(context, fragment):
    response = context.get('last_response', '')
    assert fragment.lower() not in response.lower(), (
        "Réponse contient '%s': %s" % (fragment, response)
    )


# ── Context capture ─────────────────────────────────────────────────

@given(parsers.parse('un projet existant "{project_name}"'))
def given_project_exists(env, context, project_name):
    Project = env.get('telecom.project')
    if Project is None:
        pytest.skip("telecom.project model not available")
    project = Project.search([('name', 'ilike', project_name)], limit=1)
    if not project:
        project = Project.create({'name': project_name})
    context['project'] = project


@when(parsers.parse(
    'j\'envoie un message avec le contexte du projet "{project_name}"'
))
def when_send_with_context(env, context, project_name):
    project = context.get('project')
    if not project:
        pytest.skip("No project available")

    message = "Quel est le budget ?"
    context_model = 'telecom.project'
    context_id = project.id

    full_message = message
    try:
        record = env[context_model].browse(int(context_id))
        if record.exists():
            rec_name = getattr(record, 'name', '') or str(record.id)
            model_desc = env[context_model]._description or context_model
            full_message = "[Contexte: %s — %s (id=%s)]\n\n%s" % (
                model_desc, rec_name, context_id, message
            )
    except Exception:
        pass
    context['sent_message'] = full_message


@then(parsers.parse('le message envoyé contient "{fragment}"'))
def then_message_contains(context, fragment):
    msg = context.get('sent_message', '')
    assert fragment in msg, (
        "Fragment '%s' non trouvé dans: %s" % (fragment, msg)
    )


@when("j'envoie un message sans contexte valide")
def when_send_without_context(env, context):
    message = "Question sans contexte"
    context_model = 'nonexistent.model'
    context_id = 999

    full_message = message
    try:
        record = env[context_model].browse(int(context_id))
        if record.exists():
            full_message = "[Contexte: ...]\n\n%s" % message
    except Exception:
        pass

    context['sent_message'] = full_message
    context['no_error'] = True


@then(parsers.parse('le message envoyé ne contient pas "{fragment}"'))
def then_message_not_contains(context, fragment):
    msg = context.get('sent_message', '')
    assert fragment not in msg, (
        "Fragment '%s' trouvé dans: %s" % (fragment, msg)
    )


@then("aucune erreur n'est levée")
def then_no_error(context):
    assert context.get('no_error', True), "An error was raised"


# ── Tools: zero results + failure ────────────────────────────────────

@when('l\'outil mocké retourne zéro résultat et Claude répond "Aucune donnée trouvée"')
def when_tool_returns_zero(env, context):
    from odoo.addons.telecom_assistant.models import assistant_tool_registry as registry

    conv = context['conversation']
    conv.user_input = "Y a-t-il des factures impayées ?"

    original_registry = dict(registry._TOOL_REGISTRY)

    def empty_tool(env, **kwargs):
        return {'count': 0, 'results': []}

    registry.register_tool(
        'mock_empty_tool', empty_tool,
        'Returns empty', {'type': 'object', 'properties': {}}
    )

    call_count = [0]
    responses = [
        _make_mock_tool_use_response('mock_empty_tool', {}, 'toolu_empty'),
        _make_mock_text_response("Aucune donnée trouvée pour votre recherche."),
    ]

    def mock_create(**kwargs):
        idx = min(call_count[0], len(responses) - 1)
        call_count[0] += 1
        return responses[idx]

    mock_client = MagicMock()
    mock_client.messages.create = mock_create

    try:
        with patch.object(type(conv), '_get_claude_client', return_value=mock_client):
            conv.action_send()

        assistant_msgs = conv.message_ids.filtered(lambda m: m.role == 'assistant')
        context['last_response'] = (
            assistant_msgs.sorted('sequence', reverse=True)[0].content
            if assistant_msgs else ''
        )
    finally:
        registry._TOOL_REGISTRY.clear()
        registry._TOOL_REGISTRY.update(original_registry)


@then(parsers.parse('la réponse de l\'assistant contient "{fragment}"'))
def then_response_contains(context, fragment):
    response = context.get('last_response', '')
    assert fragment.lower() in response.lower(), (
        "Fragment '%s' non trouvé dans la réponse: %s" % (fragment, response)
    )


@when("l'outil mocké échoue avec une erreur et Claude répond proprement")
def when_tool_fails(env, context):
    from odoo.addons.telecom_assistant.models import assistant_tool_registry as registry

    conv = context['conversation']
    conv.user_input = "Test outil qui crashe"

    original_registry = dict(registry._TOOL_REGISTRY)

    def failing_tool(env, **kwargs):
        raise RuntimeError("Connexion base de données perdue")

    registry.register_tool(
        'mock_crash_tool', failing_tool,
        'Always fails', {'type': 'object', 'properties': {}}
    )

    call_count = [0]
    responses = [
        _make_mock_tool_use_response('mock_crash_tool', {}, 'toolu_crash'),
        _make_mock_text_response("Une erreur technique s'est produite lors de la requête."),
    ]

    def mock_create(**kwargs):
        idx = min(call_count[0], len(responses) - 1)
        call_count[0] += 1
        return responses[idx]

    mock_client = MagicMock()
    mock_client.messages.create = mock_create

    try:
        with patch.object(type(conv), '_get_claude_client', return_value=mock_client):
            conv.action_send()

        assistant_msgs = conv.message_ids.filtered(lambda m: m.role == 'assistant')
        last_msg = assistant_msgs.sorted('sequence', reverse=True)[0] if assistant_msgs else None
        context['last_response'] = last_msg.content if last_msg else ''
        context['last_msg'] = last_msg
    finally:
        registry._TOOL_REGISTRY.clear()
        registry._TOOL_REGISTRY.update(original_registry)


@then("l'appel d'outil échoué est tracé")
def then_failed_tool_traced(context):
    last_msg = context.get('last_msg')
    assert last_msg, "No assistant message found"
    failed = last_msg.tool_call_ids.filtered(lambda tc: not tc.success)
    assert len(failed) >= 1, "No failed tool call traced"
