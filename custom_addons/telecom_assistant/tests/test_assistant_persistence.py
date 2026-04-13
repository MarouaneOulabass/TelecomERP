# -*- coding: utf-8 -*-
"""
Test: conversation persistence.
================================
Verifies that a conversation remains persisted in DB and is recoverable
after a simulated disconnection/reconnection (new env with same user).
"""
import pytest
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.assistant


def test_conversation_persisted_in_db(env):
    """A conversation with messages is recoverable by ID."""
    conv = env['telecom.assistant.conversation'].create({})
    conv_id = conv.id

    # Add a user message
    env['telecom.assistant.message'].create({
        'conversation_id': conv_id,
        'role': 'user',
        'content': 'Ma question importante',
        'sequence': 10,
    })

    # Simulate reconnection: browse the same conversation by ID
    recovered = env['telecom.assistant.conversation'].browse(conv_id)
    assert recovered.exists(), "Conversation not found after reconnection"
    assert len(recovered.message_ids) == 1
    assert recovered.message_ids[0].content == 'Ma question importante'


def test_conversation_belongs_to_user(env):
    """A conversation is tied to the creating user."""
    conv = env['telecom.assistant.conversation'].create({})
    assert conv.user_id.id == env.user.id, (
        "Conversation user should be current user"
    )


def test_multiple_messages_ordered(env):
    """Messages in a conversation are ordered by sequence."""
    conv = env['telecom.assistant.conversation'].create({})

    env['telecom.assistant.message'].create({
        'conversation_id': conv.id,
        'role': 'user',
        'content': 'Première question',
        'sequence': 10,
    })
    env['telecom.assistant.message'].create({
        'conversation_id': conv.id,
        'role': 'assistant',
        'content': 'Première réponse',
        'sequence': 15,
    })
    env['telecom.assistant.message'].create({
        'conversation_id': conv.id,
        'role': 'user',
        'content': 'Deuxième question',
        'sequence': 20,
    })

    messages = conv.message_ids.sorted('sequence')
    assert len(messages) == 3
    assert messages[0].content == 'Première question'
    assert messages[1].content == 'Première réponse'
    assert messages[2].content == 'Deuxième question'


def test_conversation_token_count(env):
    """total_tokens is computed from all messages."""
    conv = env['telecom.assistant.conversation'].create({})

    env['telecom.assistant.message'].create({
        'conversation_id': conv.id,
        'role': 'user',
        'content': 'Q1',
        'sequence': 10,
        'tokens_used': 50,
    })
    env['telecom.assistant.message'].create({
        'conversation_id': conv.id,
        'role': 'assistant',
        'content': 'R1',
        'sequence': 15,
        'tokens_used': 150,
    })

    assert conv.total_tokens == 200, (
        "Expected 200 tokens, got %d" % conv.total_tokens
    )


def test_conversation_list_for_user(env):
    """User can retrieve their conversation list (simulates /assistant/conversations)."""
    # Create 3 conversations
    for i in range(3):
        c = env['telecom.assistant.conversation'].create({})
        env['telecom.assistant.message'].create({
            'conversation_id': c.id,
            'role': 'user',
            'content': 'Question %d' % i,
            'sequence': 10,
        })

    convs = env['telecom.assistant.conversation'].search(
        [('user_id', '=', env.user.id)],
        order='create_date desc',
    )
    assert len(convs) >= 3, "Should find at least 3 conversations"
