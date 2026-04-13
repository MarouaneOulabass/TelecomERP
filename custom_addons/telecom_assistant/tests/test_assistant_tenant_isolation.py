# -*- coding: utf-8 -*-
"""
Test: multi-tenant isolation for the assistant.
================================================
Creates two companies (simulating tenants A and B) with distinct data,
verifies that a query in tenant A never returns data from tenant B.
"""
import pytest
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.assistant


def test_conversation_belongs_to_current_company(env):
    """A conversation is automatically tied to the current company."""
    conv = env['telecom.assistant.conversation'].create({})
    assert conv.company_id == env.company, (
        "Conversation company_id should be current company. "
        "Got %s, expected %s" % (conv.company_id.name, env.company.name)
    )


def test_conversations_filtered_by_company(env):
    """Conversations from company B are not visible in company A's scope."""
    # Create company B
    company_b = env['res.company'].create({
        'name': 'TenantB Test Company',
    })

    # Create a conversation in company A (current)
    conv_a = env['telecom.assistant.conversation'].create({})

    # Create a conversation in company B
    conv_b = env['telecom.assistant.conversation'].with_company(company_b).create({})

    # Search conversations in company A scope
    convs_in_a = env['telecom.assistant.conversation'].search([
        ('company_id', '=', env.company.id),
    ])
    conv_ids_in_a = convs_in_a.ids

    assert conv_a.id in conv_ids_in_a, "Conversation A should be visible in company A"
    assert conv_b.id not in conv_ids_in_a, (
        "Conversation B should NOT be visible in company A — tenant isolation violated"
    )


def test_tool_calls_use_user_env(env):
    """Tool calls execute in the user's env, respecting record rules."""
    from odoo.addons.telecom_assistant.models import assistant_tool_registry as registry

    # Register a test tool that checks env.company
    original_registry = dict(registry._TOOL_REGISTRY)
    captured_companies = []

    def spy_tool(env, **kwargs):
        captured_companies.append(env.company.id)
        return {'company_id': env.company.id, 'count': 0}

    registry.register_tool(
        'mock_spy_tool', spy_tool,
        'Spy tool for testing', {'type': 'object', 'properties': {}}
    )

    try:
        result = registry.call_tool('mock_spy_tool', env, {})
        assert result['company_id'] == env.company.id, (
            "Tool received wrong company in env"
        )
        assert len(captured_companies) == 1
        assert captured_companies[0] == env.company.id
    finally:
        registry._TOOL_REGISTRY.clear()
        registry._TOOL_REGISTRY.update(original_registry)


def test_messages_isolated_by_conversation(env):
    """Messages from conversation X are never mixed with conversation Y."""
    conv_x = env['telecom.assistant.conversation'].create({})
    conv_y = env['telecom.assistant.conversation'].create({})

    msg_x = env['telecom.assistant.message'].create({
        'conversation_id': conv_x.id,
        'role': 'user',
        'content': 'Question tenant X',
        'sequence': 10,
    })
    msg_y = env['telecom.assistant.message'].create({
        'conversation_id': conv_y.id,
        'role': 'user',
        'content': 'Question tenant Y',
        'sequence': 10,
    })

    assert msg_x.id not in conv_y.message_ids.ids, "Message X leaked into conversation Y"
    assert msg_y.id not in conv_x.message_ids.ids, "Message Y leaked into conversation X"
    assert len(conv_x.message_ids) == 1
    assert len(conv_y.message_ids) == 1
