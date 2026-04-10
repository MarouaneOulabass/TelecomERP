# -*- coding: utf-8 -*-
"""
BDD step definitions — telecom_ao
====================================
Feature files: tests/features/ao_pipeline.feature, ao_cautions_bpu.feature

Run:
    pytest custom_addons/telecom_ao/tests/ -v --tb=short
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError, UserError
from freezegun import freeze_time

pytestmark = pytest.mark.ao

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


def _make_ao(env, name='AO Test BDD', maitre_ouvrage=None, state=None, **kwargs):
    if not maitre_ouvrage:
        maitre_ouvrage = env['res.partner'].create({
            'name': 'Maître Ouvrage Test', 'partner_type': 'public_org',
        })
    vals = {'name': name, 'maitre_ouvrage_id': maitre_ouvrage.id}
    vals.update(kwargs)
    ao = env['telecom.ao'].create(vals)
    if state and state != 'detecte':
        ao.write({'state': state})
    return ao


# ─────────────────────────────────────────────────────────────────────────────
# Background
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('un organisme public "{name}" de type "public_org" existe'))
def given_public_org(env, name, context):
    p = env['res.partner'].create({'name': name, 'partner_type': 'public_org'})
    context['maitre_ouvrage'] = p


@given(parsers.parse('un opérateur "{name}" de type "operator" existe'))
def given_operator(env, name, context):
    env['res.partner'].create({'name': name, 'partner_type': 'operator'})


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline — Given/When
# ─────────────────────────────────────────────────────────────────────────────

@when(parsers.parse('je crée un AO "{name}" pour l\'organisme "{org}"'))
def when_create_ao(env, name, org, context):
    mo = context.get('maitre_ouvrage') or env['res.partner'].search(
        [('name', '=', org)], limit=1
    )
    context['ao'] = _catch(lambda: _make_ao(env, name, mo), context)


@given(parsers.parse('un AO avec le numéro "{numero}" existe déjà'))
def given_ao_with_number(env, numero, context):
    ao = _make_ao(env)
    ao.write({'numero_ao': numero})
    context['existing_ao'] = ao


@when(parsers.parse('je tente de créer un AO avec le même numéro "{numero}"'))
def when_create_duplicate_ao(env, numero, context):
    def _do():
        ao = _make_ao(env, name='Doublon AO')
        ao.write({'numero_ao': numero})
        env.cr.flush()
    _catch(_do, context)


@given(parsers.parse(
    'un AO à l\'état "etude" avec date limite de remise "{date_remise}" existe'
))
def given_ao_etude_with_date(env, date_remise, context):
    mo = context.get('maitre_ouvrage') or env['res.partner'].create({
        'name': 'MO Test', 'partner_type': 'public_org',
    })
    ao = _make_ao(env, maitre_ouvrage=mo, state='etude', date_remise=date_remise)
    context['ao'] = ao


@given(parsers.parse(
    'un AO à l\'état "etude" sans date limite de remise existe'
))
def given_ao_etude_no_date(env, context):
    mo = context.get('maitre_ouvrage') or env['res.partner'].create({
        'name': 'MO Test', 'partner_type': 'public_org',
    })
    ao = _make_ao(env, maitre_ouvrage=mo, state='etude')
    ao.write({'date_remise': False})
    context['ao'] = ao


@given(parsers.re(r'un AO à l\'état "(?P<state>[a-z_]+)" existe'))
def given_ao_in_state(env, state, context):
    mo = context.get('maitre_ouvrage') or env['res.partner'].create({
        'name': 'MO Test', 'partner_type': 'public_org',
    })
    ao = _make_ao(env, maitre_ouvrage=mo, state=state)
    context['ao'] = ao


@given(parsers.parse(
    'un AO avec date limite de remise "{date_remise}" existe'
))
def given_ao_with_date(env, date_remise, context):
    mo = context.get('maitre_ouvrage') or env['res.partner'].create({
        'name': 'MO Test', 'partner_type': 'public_org',
    })
    ao = _make_ao(env, maitre_ouvrage=mo, date_remise=date_remise)
    context['ao'] = ao


@given('un AO sans date limite de remise existe')
def given_ao_no_date(env, context):
    mo = context.get('maitre_ouvrage') or env['res.partner'].create({
        'name': 'MO Test', 'partner_type': 'public_org',
    })
    ao = _make_ao(env, maitre_ouvrage=mo)
    ao.write({'date_remise': False})
    context['ao'] = ao


# Actions

@when(parsers.parse('je passe l\'AO à l\'état "{state}"'))
def when_ao_state_transition(context, state):
    ao = context['ao']
    action_map = {
        'etude': 'action_etude',
        'soumis': 'action_soumettre',
        'gagne': 'action_gagner',
        'perdu': 'action_perdre',
        'projet': 'action_transformer_projet',
        'abandonne': 'action_abandonner',
    }
    method = action_map.get(state)
    if method:
        _catch(lambda: getattr(ao, method)(), context)


@when('je soumets l\'AO')
def when_soumettre_ao(context):
    _catch(lambda: context['ao'].action_soumettre(), context)


@when('je tente de soumettre l\'AO')
def when_try_soumettre_ao(context):
    _catch(lambda: context['ao'].action_soumettre(), context)


@when('je marque l\'AO comme gagné')
def when_gagne(context):
    _catch(lambda: context['ao'].action_gagner(), context)


@when('je marque l\'AO comme perdu')
def when_perdu(context):
    _catch(lambda: context['ao'].action_perdre(), context)


@when('je transforme l\'AO en projet')
def when_transformer(context):
    _catch(lambda: context['ao'].action_transformer_projet(), context)


@when('je tente de transformer l\'AO en projet')
def when_try_transformer(context):
    _catch(lambda: context['ao'].action_transformer_projet(), context)


@when("j'abandonne l'AO")
def when_abandonner(context):
    _catch(lambda: context['ao'].action_abandonner(), context)


@when(parsers.parse('je tente de passer directement à l\'état "soumis"'))
def when_try_direct_soumis(context):
    ao = context['ao']
    _catch(lambda: ao.action_soumettre(), context)


# ─────────────────────────────────────────────────────────────────────────────
# Assertions
# ─────────────────────────────────────────────────────────────────────────────

@then('l\'AO est créé avec succès')
def then_ao_created(context):
    assert context.get('error') is None, f"Erreur: {context.get('error')}"
    assert context.get('ao')


@then('le numéro AO est généré automatiquement')
def then_ao_number_generated(context):
    ao = context['ao']
    assert ao.numero_ao and ao.numero_ao != 'Nouveau', f"Numéro AO: '{ao.numero_ao}'"


@then(parsers.parse('l\'état de l\'AO est "{state}"'))
def then_ao_state(context, state):
    ao = context['ao']
    assert ao.state == state, f"État attendu '{state}', obtenu '{ao.state}'"


@then(parsers.parse('le champ "jours_avant_remise" de l\'AO est "{jours}"'))
def then_jours_avant_remise(context, jours):
    ao = context['ao']
    mocked = context.get('mocked_today')
    if mocked:
        with freeze_time(mocked):
            ao._compute_jours_avant_remise()
    assert ao.jours_avant_remise == int(jours), (
        f"Jours avant remise attendus: {jours}, obtenus: {ao.jours_avant_remise}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Cautions et BPU
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('un AO avec un montant soumissionné de "{montant}" MAD'))
def given_ao_with_montant(env, montant, context):
    mo = context.get('maitre_ouvrage') or env['res.partner'].create({
        'name': 'MO', 'partner_type': 'public_org',
    })
    ao = _make_ao(env, maitre_ouvrage=mo, montant_soumis=float(montant))
    context['ao'] = ao


@when(parsers.parse('je modifie le montant soumissionné à "{montant}" MAD'))
def when_update_montant(context, montant):
    context['ao'].write({'montant_soumis': float(montant)})


@then(parsers.parse('la caution provisoire calculée est "{expected}" MAD'))
def then_caution_provisoire(context, expected):
    ao = context['ao']
    assert abs(ao.caution_provisoire_montant - float(expected)) < 0.01, (
        f"Caution provisoire attendue: {expected}, obtenue: {ao.caution_provisoire_montant}"
    )


@then(parsers.parse('la caution définitive calculée est "{expected}" MAD'))
def then_caution_definitive(context, expected):
    ao = context['ao']
    assert abs(ao.caution_definitif_montant - float(expected)) < 0.01, (
        f"Caution définitive attendue: {expected}, obtenue: {ao.caution_definitif_montant}"
    )


@given(parsers.parse(
    'un AO avec {nb} lignes BPU de montants "{m1}", "{m2}" et "{m3}" MAD'
))
def given_ao_bpu_lines(env, nb, m1, m2, m3, context):
    mo = context.get('maitre_ouvrage') or env['res.partner'].create({
        'name': 'MO', 'partner_type': 'public_org',
    })
    ao = _make_ao(env, maitre_ouvrage=mo)
    for montant in [m1, m2, m3]:
        env['telecom.bpu.ligne'].create({
            'ao_id': ao.id,
            'designation': f'Prestation {montant} MAD',
            'unite': 'U',
            'quantite': 1.0,
            'prix_unitaire': float(montant),
        })
    context['ao'] = ao


@given('un AO avec un total BPU de "50000" MAD')
def given_ao_with_bpu_total(env, context):
    mo = context.get('maitre_ouvrage') or env['res.partner'].create({
        'name': 'MO', 'partner_type': 'public_org',
    })
    ao = _make_ao(env, maitre_ouvrage=mo)
    env['telecom.bpu.ligne'].create({
        'ao_id': ao.id, 'designation': 'BPU Existant',
        'unite': 'U', 'quantite': 1.0, 'prix_unitaire': 50000.0,
    })
    context['ao'] = ao


@when(parsers.parse('j\'ajoute une ligne BPU de "{montant}" MAD'))
def when_add_bpu_line(env, montant, context):
    ao = context['ao']
    env['telecom.bpu.ligne'].create({
        'ao_id': ao.id, 'designation': 'Nouvelle ligne BPU',
        'unite': 'U', 'quantite': 1.0, 'prix_unitaire': float(montant),
    })
    ao.invalidate_recordset()


@given('un AO sans lignes BPU')
def given_ao_no_bpu(env, context):
    mo = context.get('maitre_ouvrage') or env['res.partner'].create({
        'name': 'MO', 'partner_type': 'public_org',
    })
    context['ao'] = _make_ao(env, maitre_ouvrage=mo)


@then(parsers.parse('le total BPU HT est "{expected}" MAD'))
def then_bpu_total(context, expected):
    ao = context['ao']
    assert abs(ao.montant_bpu_total - float(expected)) < 0.01, (
        f"Total BPU attendu: {expected}, obtenu: {ao.montant_bpu_total}"
    )


@then(parsers.parse('le nombre de lignes BPU est "{count}"'))
def then_bpu_count(context, count):
    ao = context['ao']
    assert ao.bpu_count == int(count), f"Nb lignes BPU: {ao.bpu_count}"
