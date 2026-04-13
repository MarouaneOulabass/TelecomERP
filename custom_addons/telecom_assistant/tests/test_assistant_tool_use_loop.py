# -*- coding: utf-8 -*-
"""
Test: multi-turn tool-use loop.
================================
Mocks the Claude API to simulate a response that requests 2 different tools
before producing a final text response.  Verifies both tool calls are traced
in assistant.tool.call.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.assistant


def _make_tool_use_response(tool_name, tool_input, tool_id='toolu_01'):
    """Build a mock Claude response that requests a tool call."""
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


def _make_text_response(text):
    """Build a mock Claude response with final text."""
    block = MagicMock()
    block.type = 'text'
    block.text = text

    response = MagicMock()
    response.stop_reason = 'end_turn'
    response.content = [block]
    response.usage = MagicMock()
    response.usage.input_tokens = 200
    response.usage.output_tokens = 80
    return response


def test_two_tool_calls_before_final_response(env):
    """Simulate Claude requesting 2 tools sequentially, then giving final answer."""
    from odoo.addons.telecom_assistant.models import assistant_tool_registry as registry

    # Register mock tools if not already present
    original_registry = dict(registry._TOOL_REGISTRY)

    mock_tool_a_result = {'count': 3, 'projects': [{'name': 'FTTH Casa'}]}
    mock_tool_b_result = {'total_mad': 50000.0, 'entries': []}

    def mock_tool_a(env, **kwargs):
        return mock_tool_a_result

    def mock_tool_b(env, **kwargs):
        return mock_tool_b_result

    registry.register_tool(
        'mock_list_projects', mock_tool_a,
        'List projects', {'type': 'object', 'properties': {}}
    )
    registry.register_tool(
        'mock_get_costs', mock_tool_b,
        'Get costs', {'type': 'object', 'properties': {}}
    )

    try:
        # Create conversation
        conv = env['telecom.assistant.conversation'].create({})
        conv.user_input = "Combien coûte le projet FTTH Casa ?"

        # Mock Claude to return: tool_call_1 -> tool_call_2 -> final text
        call_count = [0]
        responses = [
            _make_tool_use_response('mock_list_projects', {}, 'toolu_01'),
            _make_tool_use_response('mock_get_costs', {'project_name': 'FTTH Casa'}, 'toolu_02'),
            _make_text_response("Le projet FTTH Casa a coûté 50 000 MAD."),
        ]

        def mock_create(**kwargs):
            idx = min(call_count[0], len(responses) - 1)
            call_count[0] += 1
            return responses[idx]

        mock_client = MagicMock()
        mock_client.messages.create = mock_create

        with patch.object(
            type(conv), '_get_claude_client', return_value=mock_client
        ):
            conv.action_send()

        # Verify: assistant message was created
        assistant_msgs = conv.message_ids.filtered(lambda m: m.role == 'assistant')
        assert len(assistant_msgs) >= 1, "No assistant message created"

        last_assistant = assistant_msgs.sorted('sequence', reverse=True)[0]
        assert '50 000' in last_assistant.content or '50000' in last_assistant.content, (
            "Final response should contain the cost figure. Got: %s" % last_assistant.content
        )

        # Verify: both tool calls are traced
        tool_calls = last_assistant.tool_call_ids
        tool_names = [tc.tool_name for tc in tool_calls]
        assert 'mock_list_projects' in tool_names, (
            "mock_list_projects not found in tool calls: %s" % tool_names
        )
        assert 'mock_get_costs' in tool_names, (
            "mock_get_costs not found in tool calls: %s" % tool_names
        )

        # Verify: tool calls were successful
        for tc in tool_calls:
            assert tc.success, "Tool call %s failed: %s" % (tc.tool_name, tc.error_message)
            assert tc.duration_ms >= 0

    finally:
        # Restore original registry
        registry._TOOL_REGISTRY.clear()
        registry._TOOL_REGISTRY.update(original_registry)


def test_tool_failure_handled_gracefully(env):
    """If a tool raises an exception, the loop continues and traces the error."""
    from odoo.addons.telecom_assistant.models import assistant_tool_registry as registry

    original_registry = dict(registry._TOOL_REGISTRY)

    def failing_tool(env, **kwargs):
        raise ValueError("Database connection lost")

    registry.register_tool(
        'mock_failing_tool', failing_tool,
        'A tool that always fails', {'type': 'object', 'properties': {}}
    )

    try:
        conv = env['telecom.assistant.conversation'].create({})
        conv.user_input = "Test outil défaillant"

        responses = [
            _make_tool_use_response('mock_failing_tool', {}, 'toolu_err'),
            _make_text_response("Désolé, l'outil a rencontré une erreur."),
        ]
        call_count = [0]

        def mock_create(**kwargs):
            idx = min(call_count[0], len(responses) - 1)
            call_count[0] += 1
            return responses[idx]

        mock_client = MagicMock()
        mock_client.messages.create = mock_create

        with patch.object(
            type(conv), '_get_claude_client', return_value=mock_client
        ):
            conv.action_send()

        assistant_msgs = conv.message_ids.filtered(lambda m: m.role == 'assistant')
        assert len(assistant_msgs) >= 1, "No assistant message after tool failure"

        # Check the failed tool call is traced
        last_msg = assistant_msgs.sorted('sequence', reverse=True)[0]
        failed_calls = last_msg.tool_call_ids.filtered(lambda tc: not tc.success)
        assert len(failed_calls) >= 1, "Failed tool call not traced"
        assert 'Database connection lost' in (failed_calls[0].error_message or '')

    finally:
        registry._TOOL_REGISTRY.clear()
        registry._TOOL_REGISTRY.update(original_registry)
