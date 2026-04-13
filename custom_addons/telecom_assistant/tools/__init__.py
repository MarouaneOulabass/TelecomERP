# -*- coding: utf-8 -*-
"""
Tool registration — conditional imports.
Each tool module registers itself only if its source models are available.
This allows telecom_assistant to work without hard-depending on every module.
"""
import logging

_logger = logging.getLogger(__name__)

# Each tool module handles its own import errors gracefully
try:
    from . import tool_projects
except Exception as e:
    _logger.debug("Assistant tools for projects not loaded: %s", e)

try:
    from . import tool_interventions
except Exception as e:
    _logger.debug("Assistant tools for interventions not loaded: %s", e)

try:
    from . import tool_costs
except Exception as e:
    _logger.debug("Assistant tools for costs not loaded: %s", e)

try:
    from . import tool_sites
except Exception as e:
    _logger.debug("Assistant tools for sites not loaded: %s", e)

try:
    from . import tool_hr
except Exception as e:
    _logger.debug("Assistant tools for HR not loaded: %s", e)
