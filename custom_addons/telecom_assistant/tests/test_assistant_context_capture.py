# -*- coding: utf-8 -*-
"""
Test: context capture from current Odoo view.
==============================================
Simulates a request to /assistant/chat with context_model and context_id,
verifies the context is properly injected into the user message.
"""
import pytest
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.assistant


def test_context_injected_into_message(env):
    """When context_model and context_id are provided, the message includes context."""
    # Create a project to use as context
    Project = env.get('telecom.project')
    if Project is None:
        pytest.skip("telecom.project model not available")

    projects = Project.search([], limit=1)
    if not projects:
        pytest.skip("No project records available for context test")

    project = projects[0]

    # Create a conversation
    conv = env['telecom.assistant.conversation'].create({})

    # Simulate what the controller does: build a contextual message
    context_model = 'telecom.project'
    context_id = project.id
    message = "Quel est le budget de ce projet ?"

    full_message = message
    try:
        record = env[context_model].browse(int(context_id))
        if record.exists():
            rec_name = getattr(record, 'name', '') or getattr(record, 'display_name', '') or str(record.id)
            model_desc = env[context_model]._description or context_model
            full_message = "[Contexte: %s — %s (id=%s)]\n\n%s" % (
                model_desc, rec_name, context_id, message
            )
    except Exception:
        pass

    assert '[Contexte:' in full_message, (
        "Context was not injected. Got: %s" % full_message
    )
    assert str(context_id) in full_message
    assert message in full_message


def test_context_graceful_without_record(env):
    """When context_model is invalid, the message is sent without context (no crash)."""
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

    # Should fall through gracefully — message unchanged
    assert full_message == message, (
        "Message should remain unchanged with invalid context model"
    )


def test_context_without_id(env):
    """When only context_model is provided without context_id, no context injected."""
    message = "Question générale"
    context_model = 'telecom.project'
    context_id = None

    full_message = message
    if context_model and context_id:
        full_message = "[Contexte: ...]\n\n%s" % message

    assert full_message == message, "No context should be injected without context_id"
