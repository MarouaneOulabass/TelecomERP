# -*- coding: utf-8 -*-
"""
Assistant Tool Registry
========================
Central registry where each capability module registers its tools.
The assistant NEVER accesses Odoo models directly — only via registered tools.

Each tool is a Python function that:
- Takes typed parameters
- Returns JSON-serializable data
- Respects Odoo record rules (runs in the user's env)
- Is fully documented for the LLM
"""
import json
import logging

_logger = logging.getLogger(__name__)

# Global tool registry — populated at module load time
_TOOL_REGISTRY = {}


def register_tool(name, func, description, parameters):
    """Register a tool for the assistant.

    Args:
        name: Unique tool name (e.g. 'get_interventions')
        func: Callable(env, **kwargs) -> dict/list
        description: Human-readable description for the LLM
        parameters: JSON Schema dict describing the parameters
    """
    _TOOL_REGISTRY[name] = {
        'name': name,
        'function': func,
        'description': description,
        'parameters': parameters,
    }
    _logger.info('Assistant tool registered: %s', name)


def get_all_tools():
    """Return all registered tools as Claude API tool definitions."""
    tools = []
    for name, tool in _TOOL_REGISTRY.items():
        tools.append({
            'name': tool['name'],
            'description': tool['description'],
            'input_schema': tool['parameters'],
        })
    return tools


def call_tool(name, env, kwargs):
    """Call a registered tool with the user's Odoo environment.

    Returns JSON-serializable result.
    Raises KeyError if tool not found.
    """
    if name not in _TOOL_REGISTRY:
        raise KeyError('Tool not found: %s' % name)
    func = _TOOL_REGISTRY[name]['function']
    return func(env, **kwargs)


def get_tool_names():
    return list(_TOOL_REGISTRY.keys())
