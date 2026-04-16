# -*- coding: utf-8 -*-
"""
BDD step definitions -- telecom_facturation
============================================
Feature files: tests/features/facturation.feature

Run:
    pytest custom_addons/telecom_facturation/tests/ -v --tb=short
    pytest custom_addons/telecom_facturation/tests/ -k facturation -v
"""
import pytest
from datetime import date, timedelta
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError, UserError

pytestmark = pytest.mark.facturation

# Load all feature files in this module
scenarios('features/')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_partner(env, name, partner_type='customer', ice=False):
    """Helper: create a res.partner."""
    vals = {
        'name': name,
        'partner_type': partner_type if partner_type != 'customer' else False,
        'customer_rank': 1,
    }
    if ice:
        vals['ice'] = ice
    return env['res.partner'].create(vals)


def _create_invoice(env, partner, telecom_type='standard', project=False, due_date=False):
    """Helper: create a draft customer invoice."""
    vals = {
        'move_type': 'out_invoice',
        'partner_id': partner.id,
        'telecom_type': telecom_type,
        'invoice_line_ids': [(0, 0, {
            'name': 'Prestation telecom',
            'quantity': 1,
            'price_unit': 10000.0,
        })],
    }
    if project:
        vals['telecom_project_id'] = project.id
    if due_date:
        vals['invoice_date_due'] = due_date
        vals['invoice_date'] = due_date - timedelta(days=30)
    move = env['account.move'].create(vals)
    return move


def _post_invoice(move):
    """Post a draft invoice."""
    move.action_post()
    return move


def _catch(fn, context):
    """Run fn(), store error message in context['error'] if any exception raised."""
    try:
        result = fn()
        context['error'] = None
        return result
    except (ValidationError, UserError) as exc:
        context['error'] = str(exc)
    except Exception as exc:
        context['error'] = str(exc)


# ---------------------------------------------------------------------------
# Background / Given
# ---------------------------------------------------------------------------

@given('la societe courante est initialisee')
def company_ready(env):
    return env.company


@given(parsers.parse('un partenaire client "{name}" avec ICE "{ice}" existe'))
def partner_with_ice(env, context, name, ice):
    partner = _create_partner(env, name, ice=ice)
    context.setdefault('partners', {})[name] = partner


@given(parsers.parse('un partenaire client "{name}" sans ICE existe'))
def partner_without_ice(env, context, name):
    partner = _create_partner(env, name)
    context.setdefault('partners', {})[name] = partner


@given(parsers.parse('un projet telecom "{project_name}" existe'))
def project_exists(env, context, project_name):
    project = env['project.project'].create({'name': project_name})
    context.setdefault('projects', {})[project_name] = project


@given(parsers.parse(
    'une facture postee pour "{partner_name}" avec echeance il y a {days:d} jours'
))
def posted_invoice_overdue(env, context, partner_name, days):
    partner = context['partners'][partner_name]
    due_date = date.today() - timedelta(days=days)
    move = _create_invoice(env, partner, due_date=due_date)
    _post_invoice(move)
    # Force recompute after posting
    move._compute_payment_delay()
    context['invoice'] = move


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------

@when(parsers.parse(
    'je cree une facture client pour "{partner_name}" de type "{telecom_type}" '
    'liee au projet "{project_name}"'
))
def create_invoice_with_project(env, context, partner_name, telecom_type, project_name):
    partner = context['partners'][partner_name]
    project = context['projects'][project_name]
    move = _create_invoice(env, partner, telecom_type=telecom_type, project=project)
    context['invoice'] = move


@when(parsers.parse(
    'je cree une facture client pour "{partner_name}" de type "{telecom_type}" sans projet'
))
def create_invoice_without_project(env, context, partner_name, telecom_type):
    partner = context['partners'][partner_name]
    move = _create_invoice(env, partner, telecom_type=telecom_type)
    context['invoice'] = move


@when(parsers.parse(
    'je cree une facture client pour "{partner_name}" de type "{telecom_type}"'
))
def create_invoice_simple(env, context, partner_name, telecom_type):
    partner = context['partners'][partner_name]
    move = _create_invoice(env, partner, telecom_type=telecom_type)
    context['invoice'] = move


@when('je recalcule le delai de paiement')
def recompute_delay(context):
    context['invoice']._compute_payment_delay()


@when(parsers.parse('je cree une relance de niveau "{level}" par "{mode}"'))
def create_relance(env, context, level, mode):
    invoice = context['invoice']
    relance = env['telecom.relance'].create({
        'invoice_id': invoice.id,
        'level': level,
        'mode': mode,
        'date': date.today(),
    })
    context['relance'] = relance


@when("j'envoie la relance")
def send_relance(context):
    context['relance'].action_send()


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------

@then('la facture est creee avec succes')
def invoice_created(context):
    assert context['invoice'], "La facture n'a pas ete creee."
    assert context['invoice'].id, "La facture n'a pas d'ID."


@then(parsers.parse('le type telecom de la facture est "{expected_type}"'))
def invoice_telecom_type(context, expected_type):
    assert context['invoice'].telecom_type == expected_type, (
        f"Type attendu: {expected_type}, "
        f"obtenu: {context['invoice'].telecom_type}"
    )


@then(parsers.parse('le projet telecom est "{project_name}"'))
def invoice_has_project(context, project_name):
    assert context['invoice'].telecom_project_id.name == project_name, (
        f"Projet attendu: {project_name}, "
        f"obtenu: {context['invoice'].telecom_project_id.name}"
    )


@then('le projet telecom est vide')
def invoice_no_project(context):
    assert not context['invoice'].telecom_project_id, (
        "Le projet telecom devrait etre vide."
    )


@then(parsers.parse('le retard de paiement est de {days:d} jours'))
def delay_days(context, days):
    actual = context['invoice'].payment_delay_days
    assert actual == days, (
        f"Retard attendu: {days} jours, obtenu: {actual} jours"
    )


@then("l'alerte delai paiement est activee")
def delay_alert_on(context):
    assert context['invoice'].payment_delay_alert, (
        "L'alerte delai paiement devrait etre activee."
    )


@then("l'alerte delai paiement est desactivee")
def delay_alert_off(context):
    assert not context['invoice'].payment_delay_alert, (
        "L'alerte delai paiement devrait etre desactivee."
    )


@then(parsers.parse('la relance est en etat "{expected_state}"'))
def relance_state(context, expected_state):
    assert context['relance'].state == expected_state, (
        f"Etat attendu: {expected_state}, "
        f"obtenu: {context['relance'].state}"
    )


@then(parsers.parse('le compteur de relances de la facture est {count:d}'))
def relance_count(context, count):
    assert context['invoice'].relance_count == count, (
        f"Compteur attendu: {count}, "
        f"obtenu: {context['invoice'].relance_count}"
    )


@then(parsers.parse('le champ ICE client de la facture est "{expected_ice}"'))
def invoice_ice(context, expected_ice):
    assert context['invoice'].ice_client == expected_ice, (
        f"ICE attendu: {expected_ice}, "
        f"obtenu: {context['invoice'].ice_client}"
    )
