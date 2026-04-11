# -*- coding: utf-8 -*-
"""
BDD step definitions -- telecom_tenant
========================================
Feature files: tests/features/tenant.feature

Run:
    pytest custom_addons/telecom_tenant/tests/ -v --tb=short
"""
import yaml
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError, UserError

pytestmark = pytest.mark.tenant

scenarios('features/')


def _catch(fn, context):
    """Execute fn, capture errors into context['error']."""
    try:
        result = fn()
        context['error'] = None
        return result
    except (ValidationError, UserError) as exc:
        context['error'] = str(exc)
    except Exception as exc:
        context['error'] = str(exc)


# -------------------------------------------------------------------------
# Given
# -------------------------------------------------------------------------

@given(parsers.parse(
    'un tenant "{name}" avec le sous-domaine "{subdomain}" existe'
))
def given_tenant_exists(env, name, subdomain, context):
    tenant = env['telecom.tenant'].create({
        'name': name,
        'subdomain': subdomain,
    })
    context['tenant'] = tenant
    return tenant


# -------------------------------------------------------------------------
# When
# -------------------------------------------------------------------------

@when(parsers.parse(
    'je crée un tenant "{name}" avec le sous-domaine "{subdomain}"'
))
def when_create_tenant(env, name, subdomain, context):
    context['tenant'] = _catch(lambda: env['telecom.tenant'].create({
        'name': name,
        'subdomain': subdomain,
    }), context)


@when(parsers.parse(
    'je tente de créer un tenant "{name}" avec le sous-domaine "{subdomain}"'
))
def when_create_tenant_fail(env, name, subdomain, context):
    _catch(lambda: env['telecom.tenant'].create({
        'name': name,
        'subdomain': subdomain,
    }), context)


@when('je génère le profil YAML du tenant')
def when_generate_yaml(context):
    tenant = context['tenant']
    tenant.action_generate_yaml()


# -------------------------------------------------------------------------
# Then
# -------------------------------------------------------------------------

@then('le tenant est créé avec succès')
def then_tenant_created(context):
    assert context.get('error') is None, f"Erreur: {context.get('error')}"
    assert context.get('tenant') is not None


@then(parsers.parse('l\'état du tenant est "{state}"'))
def then_tenant_state(context, state):
    tenant = context['tenant']
    assert tenant.state == state, (
        f"Etat attendu: {state}, obtenu: {tenant.state}"
    )


@then(parsers.parse('le profil YAML contient la clé "{key}"'))
def then_yaml_contains_key(context, key):
    tenant = context['tenant']
    assert tenant.yaml_profile, "Le profil YAML n'a pas ete genere."
    data = yaml.safe_load(tenant.yaml_profile)
    assert key in data, (
        f"Cle '{key}' manquante dans le profil YAML. "
        f"Cles presentes: {list(data.keys())}"
    )
