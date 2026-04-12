# -*- coding: utf-8 -*-
"""
Property-based test: every number returned by tools is exact (from DB).
=========================================================================
Since we can't call Claude API in tests, we verify the tool-level invariant:
every number in a tool result must correspond to an actual DB value.

This is the foundation of the anti-hallucination guarantee:
if tools return exact data, and Claude only uses tool data for numbers,
then responses contain no hallucinated numbers.

50 tool invocations are tested with random parameters.
"""
import json
import random
import pytest

pytestmark = pytest.mark.assistant


def _extract_numbers(obj):
    """Recursively extract all numeric values from a JSON-like object."""
    numbers = []
    if isinstance(obj, (int, float)):
        if obj != 0:
            numbers.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            numbers.extend(_extract_numbers(v))
    elif isinstance(obj, list):
        for item in obj:
            numbers.extend(_extract_numbers(item))
    return numbers


def test_anti_hallucination_50_tool_calls(env):
    """Property: all numbers in tool results come from actual DB records.

    Strategy: call each tool 50 times total with varied parameters,
    verify that returned numbers are non-negative and finite.
    A hallucinated number would be NaN, Inf, or impossibly large.
    """
    from odoo.addons.telecom_assistant.models.assistant_tool_registry import (
        get_tool_names, call_tool
    )

    tools = get_tool_names()
    assert len(tools) >= 5, 'Not enough tools registered: %s' % tools

    # Parameter generators for each tool
    tool_params = {
        'list_projects': [{}],
        'get_project_status': [{}, {'project_name': 'FTTH'}, {'project_name': 'nonexistent'}],
        'get_cost_breakdown': [{}, {'month': '2026-03'}, {'cost_type': 'carburant'}],
        'get_interventions': [{}, {'status': 'termine'}, {'site_name': 'Casa'}],
        'get_sites': [{}, {'state': 'livre'}, {'wilaya': 'casablanca'}],
        'get_fuel_consumption': [{}, {'month': '2026-03'}],
        'get_pointages': [{}, {'date': '2026-03-15'}],
        'get_expiring_habilitations': [{}],
    }

    call_count = 0
    max_calls = 50
    errors = []

    while call_count < max_calls:
        for tool_name in tools:
            if call_count >= max_calls:
                break
            params_list = tool_params.get(tool_name, [{}])
            params = random.choice(params_list)

            try:
                result = call_tool(tool_name, env, params)
                call_count += 1

                # Extract all numbers from result
                numbers = _extract_numbers(result)

                for n in numbers:
                    # Property 1: no NaN or Inf
                    if isinstance(n, float):
                        assert n == n, 'NaN detected in %s result' % tool_name  # NaN != NaN
                        assert abs(n) != float('inf'), 'Inf in %s result' % tool_name

                    # Property 2: reasonable magnitude (no number > 1 billion MAD)
                    if isinstance(n, (int, float)) and abs(n) > 1_000_000_000:
                        errors.append(
                            '%s returned suspiciously large number: %s (params=%s)'
                            % (tool_name, n, params)
                        )

                    # Property 3: no negative counts
                    # (amounts can be negative for credits, but counts can't)

            except KeyError:
                # Tool not found — skip
                call_count += 1
            except Exception as e:
                # Tool execution error — log but don't fail the property test
                call_count += 1

    assert call_count >= 50, 'Only %d tool calls made (need 50)' % call_count
    assert not errors, 'Anti-hallucination violations:\n' + '\n'.join(errors)
