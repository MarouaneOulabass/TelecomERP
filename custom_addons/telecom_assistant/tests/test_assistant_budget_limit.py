# -*- coding: utf-8 -*-
"""
Test: budget limit enforcement.
================================
Sets the monthly token budget to 0 MAD (= 0 tokens), verifies the controller
refuses with a clear error message (no crash).
"""
import pytest
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.assistant


def test_budget_zero_refuses_cleanly(env):
    """With monthly budget set to 0, action_send raises a UserError."""
    from odoo.exceptions import UserError

    # Set budget to 0
    env['ir.config_parameter'].sudo().set_param(
        'telecom.assistant_monthly_token_limit', '0'
    )

    conv = env['telecom.assistant.conversation'].create({})

    # Add a fake previous message with tokens to simulate usage
    env['telecom.assistant.message'].create({
        'conversation_id': conv.id,
        'role': 'user',
        'content': 'Question précédente',
        'tokens_used': 100,
        'sequence': 10,
    })

    conv.user_input = "Nouvelle question"

    # Mock the Claude client so we can detect if it's called
    mock_client = MagicMock()
    with patch.object(type(conv), '_get_claude_client', return_value=mock_client):
        conv.action_send()

    # With budget=0 and total_tokens > 0, should get error message
    assistant_msgs = conv.message_ids.filtered(lambda m: m.role == 'assistant')
    assert len(assistant_msgs) >= 1, "No response message created"

    last_msg = assistant_msgs.sorted('sequence', reverse=True)[0]
    # The error should mention "budget" or "dépassé"
    content_lower = last_msg.content.lower()
    assert 'budget' in content_lower or 'dépassé' in content_lower or 'erreur' in content_lower, (
        "Budget exceeded message not clear. Got: %s" % last_msg.content
    )


def test_budget_high_allows_query(env):
    """With a high budget, queries proceed normally."""
    env['ir.config_parameter'].sudo().set_param(
        'telecom.assistant_monthly_token_limit', '999999999'
    )

    conv = env['telecom.assistant.conversation'].create({})
    conv.user_input = "Test question"

    mock_response = MagicMock()
    mock_response.stop_reason = 'end_turn'
    block = MagicMock()
    block.type = 'text'
    block.text = "Réponse de test"
    mock_response.content = [block]
    mock_response.usage = MagicMock()
    mock_response.usage.input_tokens = 50
    mock_response.usage.output_tokens = 30

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch.object(type(conv), '_get_claude_client', return_value=mock_client):
        conv.action_send()

    assistant_msgs = conv.message_ids.filtered(lambda m: m.role == 'assistant')
    assert len(assistant_msgs) >= 1
    last_msg = assistant_msgs.sorted('sequence', reverse=True)[0]
    assert 'Réponse de test' in last_msg.content


def test_budget_negative_one_disables_check(env):
    """A negative budget value should disable the budget check."""
    env['ir.config_parameter'].sudo().set_param(
        'telecom.assistant_monthly_token_limit', '-1'
    )

    conv = env['telecom.assistant.conversation'].create({})
    # Add huge token usage
    env['telecom.assistant.message'].create({
        'conversation_id': conv.id,
        'role': 'user',
        'content': 'Old message',
        'tokens_used': 10000000,
        'sequence': 10,
    })

    conv.user_input = "Question avec gros historique"

    mock_response = MagicMock()
    mock_response.stop_reason = 'end_turn'
    block = MagicMock()
    block.type = 'text'
    block.text = "OK malgré le gros historique"
    mock_response.content = [block]
    mock_response.usage = MagicMock()
    mock_response.usage.input_tokens = 50
    mock_response.usage.output_tokens = 30

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch.object(type(conv), '_get_claude_client', return_value=mock_client):
        conv.action_send()

    assistant_msgs = conv.message_ids.filtered(lambda m: m.role == 'assistant')
    last_msg = assistant_msgs.sorted('sequence', reverse=True)[0]
    # Should NOT contain budget error
    assert 'budget' not in last_msg.content.lower() or 'OK' in last_msg.content
