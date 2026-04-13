# -*- coding: utf-8 -*-
"""
Test: no root menuitem created by telecom_assistant.
=====================================================
Verifies that after installation, no ir.ui.menu root entry
(parent_id = False) belongs to the telecom_assistant module.
"""
import pytest

pytestmark = pytest.mark.assistant


def test_no_root_menu_for_assistant(env):
    """No ir.ui.menu with parent_id=False should reference telecom_assistant."""
    root_menus = env['ir.ui.menu'].search([('parent_id', '=', False)])
    assistant_roots = []
    for menu in root_menus:
        xid = menu.get_external_id().get(menu.id, '')
        if 'telecom_assistant' in xid:
            assistant_roots.append({'name': menu.name, 'xmlid': xid})
    assert len(assistant_roots) == 0, (
        "Root menuitems found for telecom_assistant (violation): %s" % assistant_roots
    )


def test_no_assistant_name_in_root_menus(env):
    """No root menu should contain 'Assistant' in its name from our module."""
    root_menus = env['ir.ui.menu'].search([('parent_id', '=', False)])
    suspect = []
    for menu in root_menus:
        xid = menu.get_external_id().get(menu.id, '')
        if 'telecom_assistant' in xid and 'assistant' in (menu.name or '').lower():
            suspect.append(menu.name)
    assert not suspect, "Root menus with 'Assistant' name: %s" % suspect


def test_action_assistant_new_does_not_exist(env):
    """The action_assistant_new should have been removed (Option B)."""
    action = env.ref(
        'telecom_assistant.action_assistant_new', raise_if_not_found=False
    )
    assert not action, (
        "action_assistant_new still exists — it creates a dedicated page, "
        "violating the 'no dedicated page' rule."
    )
