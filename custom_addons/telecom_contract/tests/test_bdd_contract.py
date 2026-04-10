# -*- coding: utf-8 -*-
"""
BDD step definitions — telecom_contract
=========================================
Feature files: tests/features/contrat_cycle_vie.feature

Run:
    pytest custom_addons/telecom_contract/tests/ -v --tb=short
"""
import pytest
from datetime import date, timedelta
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError, UserError
from freezegun import freeze_time

pytestmark = pytest.mark.contrat

scenarios('features/')


def _catch(fn, context):
    try:
        result = fn()
        context['error'] = None
        return result
    except (ValidationError, UserError) as exc:
        context['error'] = str(exc)
    except Exception as exc:
        context['error'] = str(exc)


def _make_partner(env, name, partner_type='operator'):
    return env['res.partner'].create({'name': name, 'partner_type': partner_type})


def _make_contract(env, name, contract_type, partner, state=None, **kwargs):
    vals = {
        'name': name,
        'contract_type': contract_type,
        'partenaire_id': partner.id,
        'date_debut': date.today().isoformat(),
    }
    vals.update(kwargs)
    c = env['telecom.contract'].create(vals)
    if state and state != 'brouillon':
        # Direct write to bypass action guards for setup
        c.write({'state': state})
    return c


# ─────────────────────────────────────────────────────────────────────────────
# Background
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('un partenaire opérateur "{name}" de type "operator" existe'))
def given_operator_partner(env, name, context):
    p = _make_partner(env, name, 'operator')
    context['partner'] = p


# ─────────────────────────────────────────────────────────────────────────────
# Given — contract setup
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('un contrat "{name}" à l\'état "{state}" existe'))
def given_contract_in_state(env, name, state, context):
    partner = context.get('partner') or _make_partner(env, 'Partenaire Test')
    c = _make_contract(env, name, 'maintenance', partner, state=state)
    context['contract'] = c


@given(parsers.parse('un contrat actif avec date de fin "{date_fin}" existe'))
def given_active_contract_with_end(env, date_fin, context):
    partner = context.get('partner') or _make_partner(env, 'Partenaire Test')
    c = _make_contract(env, 'Contrat Expiration', 'maintenance', partner,
                       date_fin=date_fin)
    c.write({'state': 'actif'})
    context['contract'] = c


@given(parsers.parse('un contrat en brouillon avec date de fin "{date_fin}" existe'))
def given_draft_contract_with_end(env, date_fin, context):
    partner = context.get('partner') or _make_partner(env, 'Partenaire Test')
    c = _make_contract(env, 'Contrat Brouillon Fin', 'maintenance', partner,
                       date_fin=date_fin)
    context['contract'] = c


@given('un contrat actif sans date de fin existe')
def given_active_contract_no_end(env, context):
    partner = context.get('partner') or _make_partner(env, 'Partenaire Test')
    c = _make_contract(env, 'Contrat CDI', 'maintenance', partner)
    c.write({'state': 'actif'})
    context['contract'] = c


@given(parsers.parse('un contrat actif "{name}" existe'))
def given_active_contract(env, name, context):
    partner = context.get('partner') or _make_partner(env, 'Partenaire Test')
    c = _make_contract(env, name, 'maintenance', partner)
    c.write({'state': 'actif'})
    context['contract'] = c


@given(parsers.parse(
    'une caution avec date d\'expiration "{date_exp}" existe'
))
def given_caution_with_expiry(env, date_exp, context):
    partner = context.get('partner') or _make_partner(env, 'Partenaire Test')
    c = _make_contract(env, 'Contrat Caution Expiry', 'maintenance', partner)
    caution = env['telecom.caution.bancaire'].create({
        'contract_id': c.id,
        'caution_type': 'provisoire',
        'banque': 'CIH Bank',
        'reference_bancaire': f'REF-{date_exp}',
        'date_emission': date.today().isoformat(),
        'date_expiration': date_exp,
    })
    context['caution'] = caution


@given('une caution libérée existe')
def given_liberee_caution(env, context):
    partner = context.get('partner') or _make_partner(env, 'Partenaire Test')
    c = _make_contract(env, 'Contrat Libération', 'maintenance', partner)
    caution = env['telecom.caution.bancaire'].create({
        'contract_id': c.id,
        'caution_type': 'definitive',
        'banque': 'BMCE',
        'reference_bancaire': 'REF-LIBEREE-001',
        'date_emission': '2023-01-01',
        'date_expiration': '2020-01-01',  # Already expired date
        'date_liberation': date.today().isoformat(),
    })
    context['caution'] = caution


# ─────────────────────────────────────────────────────────────────────────────
# When — creation
# ─────────────────────────────────────────────────────────────────────────────

@when(parsers.parse(
    'je crée un contrat "{name}" de type "{contract_type}" pour "{org}"'
))
def when_create_contract(env, name, contract_type, org, context):
    partner = context.get('partner') or env['res.partner'].search(
        [('name', '=', org)], limit=1
    )
    context['contract'] = _catch(
        lambda: _make_contract(env, name, contract_type, partner), context
    )


@when(parsers.parse(
    'je crée un contrat "{name}" de type "{contract_type}" pour "{org}"'
    ' avec SLA "{h_int}" h intervention et "{h_rep}" h réparation'
))
def when_create_contract_with_sla(env, name, contract_type, org, h_int, h_rep, context):
    partner = context.get('partner') or env['res.partner'].search(
        [('name', '=', org)], limit=1
    )
    context['contract'] = _catch(lambda: _make_contract(
        env, name, contract_type, partner,
        sla_delai_intervention_h=int(h_int),
        sla_delai_reparation_h=int(h_rep),
    ), context)


# ─────────────────────────────────────────────────────────────────────────────
# When — state transitions
# ─────────────────────────────────────────────────────────────────────────────

@when("j'active le contrat")
def when_activate_contract(context):
    _catch(lambda: context['contract'].action_activer(), context)


@when('je suspends le contrat')
def when_suspend_contract(context):
    _catch(lambda: context['contract'].action_suspendre(), context)


@when('je réactive le contrat')
def when_reactivate_contract(context):
    _catch(lambda: context['contract'].action_reactiver(), context)


@when('je résilie le contrat')
def when_resilier_contract(context):
    _catch(lambda: context['contract'].action_resilier(), context)


@when('je tente de résilier le contrat')
def when_try_resilier(context):
    _catch(lambda: context['contract'].action_resilier(), context)


@when('je tente de suspendre le contrat')
def when_try_suspendre(context):
    _catch(lambda: context['contract'].action_suspendre(), context)


@when('je tente de réactiver le contrat')
def when_try_reactiver(context):
    _catch(lambda: context['contract'].action_reactiver(), context)


# ─────────────────────────────────────────────────────────────────────────────
# When — cautions
# ─────────────────────────────────────────────────────────────────────────────

@when(parsers.parse(
    'j\'ajoute une caution "{caution_type}" de "{montant}" MAD émise par "{banque}"'
))
def when_add_caution(env, caution_type, montant, banque, context):
    c = context['contract']
    env['telecom.caution.bancaire'].create({
        'contract_id': c.id,
        'caution_type': caution_type,
        'banque': banque,
        'reference_bancaire': f'REF-{caution_type.upper()}-001',
        'date_emission': date.today().isoformat(),
        'montant': float(montant),
    })
    c.invalidate_recordset()


# ─────────────────────────────────────────────────────────────────────────────
# Then — assertions
# ─────────────────────────────────────────────────────────────────────────────

@then('le contrat est créé avec succès')
def then_contract_created(context):
    assert context.get('error') is None, f"Erreur: {context.get('error')}"
    assert context.get('contract')


@then('la référence contrat est générée automatiquement')
def then_contract_ref_generated(context):
    c = context['contract']
    assert c.reference and c.reference != 'Nouveau', f"Référence: '{c.reference}'"


@then(parsers.parse('l\'état du contrat est "{state}"'))
def then_contract_state(context, state):
    c = context['contract']
    assert c.state == state, f"État attendu '{state}', obtenu '{c.state}'"


@then('une erreur de workflow est levée')
def then_workflow_error(context):
    assert context.get('error') is not None, "Aucune erreur levée alors qu'une erreur était attendue"


@then('l\'alerte d\'expiration du contrat est active')
def then_expiry_alert_active(context):
    c = context['contract']
    mocked = context.get('mocked_today')
    if mocked:
        with freeze_time(mocked):
            c._compute_expiry_warning()
    assert c.expiry_warning, "Alerte expiration non active"


@then('l\'alerte d\'expiration du contrat est inactive')
def then_expiry_alert_inactive(context):
    c = context['contract']
    mocked = context.get('mocked_today')
    if mocked:
        with freeze_time(mocked):
            c._compute_expiry_warning()
    assert not c.expiry_warning, "Alerte expiration active à tort"


@then(parsers.parse('le SLA d\'intervention est de "{heures}" heures'))
def then_sla_intervention(context, heures):
    c = context['contract']
    assert c.sla_delai_intervention_h == int(heures), (
        f"SLA intervention attendu: {heures}h, obtenu: {c.sla_delai_intervention_h}h"
    )


@then(parsers.parse('le SLA de réparation est de "{heures}" heures'))
def then_sla_reparation(context, heures):
    c = context['contract']
    assert c.sla_delai_reparation_h == int(heures), (
        f"SLA réparation attendu: {heures}h, obtenu: {c.sla_delai_reparation_h}h"
    )


@then(parsers.parse('le contrat possède "{count}" caution(s) bancaire(s)'))
def then_caution_count(context, count):
    c = context['contract']
    assert c.caution_count == int(count), (
        f"Nb cautions attendu: {count}, obtenu: {c.caution_count}"
    )


@then(parsers.parse('l\'état de la caution est "{state}"'))
def then_caution_state(context, state):
    caution = context['caution']
    mocked = context.get('mocked_today')
    if mocked:
        with freeze_time(mocked):
            caution._compute_state()
    assert caution.state == state, (
        f"État caution attendu '{state}', obtenu '{caution.state}'"
    )
