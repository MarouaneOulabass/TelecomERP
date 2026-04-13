# -*- coding: utf-8 -*-
"""
Tests for telecom_test_admin.
"""
import pytest
from pytest_bdd import scenarios, given, when, then

pytestmark = pytest.mark.test_admin

scenarios('features/')


@when('je cherche les menus racines de test_admin')
def when_search_root_menus(env, context):
    menus = env['ir.ui.menu'].search([('parent_id', '=', False)])
    test_roots = []
    for m in menus:
        xid = m.get_external_id().get(m.id, '')
        if 'telecom_test_admin' in xid:
            test_roots.append(m.name)
    context['test_root_menus'] = test_roots


@then('aucun menu racine n\'est trouvé pour telecom_test_admin')
def then_no_root_menu(context):
    menus = context.get('test_root_menus', [])
    assert len(menus) == 0, 'Root menus found: %s' % menus


@when('je crée un run de tests')
def when_create_run(env, context):
    run = env['telecom.test.run'].create({
        'module_filter': 'telecom_base',
    })
    context['run'] = run


@then('le run est à l\'état "draft"')
def then_run_draft(context):
    assert context['run'].state == 'draft'
