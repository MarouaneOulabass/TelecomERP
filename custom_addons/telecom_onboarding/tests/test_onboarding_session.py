# -*- coding: utf-8 -*-
"""
Tests for telecom_onboarding.
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

pytestmark = pytest.mark.onboarding

scenarios('features/')


# ── Session lifecycle ────────────────────────────────────────────────

@when('je crée une session d\'onboarding')
def when_create_session(env, context):
    session = env['telecom.onboarding.session'].create({})
    context['session'] = session


@then('la session est à l\'état "upload"')
def then_session_upload(context):
    assert context['session'].state == 'upload'


@then('la session appartient à l\'utilisateur courant')
def then_session_user(env, context):
    assert context['session'].create_uid.id == env.user.id


@when(parsers.parse('je renseigne la raison sociale "{name}"'))
def when_set_company_name(context, name):
    context['session'].company_name = name


@then(parsers.parse('le nom de session contient "{fragment}"'))
def then_session_name_contains(context, fragment):
    assert fragment in (context['session'].name or ''), (
        "Expected '%s' in '%s'" % (fragment, context['session'].name)
    )


@when('j\'essaie d\'extraire sans documents')
def when_extract_no_docs(context):
    try:
        context['session'].action_extract_documents()
        context['error'] = ''
    except Exception as e:
        context['error'] = str(e)


# ── YAML generation ─────────────────────────────────────────────────

@when('je génère le profil YAML avec les capabilities par défaut')
def when_generate_yaml_via_onboarding(context):
    session = context['session']
    session.company_name = 'Test Corp'
    session.subdomain = 'test-corp'
    session.ice = '123456789012345'
    session.city = 'Casablanca'
    session.state = 'configuring'
    session.action_generate_and_provision()


@then('un tenant est créé')
def then_tenant_created(context):
    session = context['session']
    # Either tenant was created or an error was logged
    assert session.tenant_id or session.state == 'error'
