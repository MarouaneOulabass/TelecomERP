# -*- coding: utf-8 -*-
"""
BDD step definitions — telecom_equipment
==========================================
Feature files: tests/features/equipement.feature

Run:
    pytest custom_addons/telecom_equipment/tests/ -v --tb=short
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError, UserError
from freezegun import freeze_time

pytestmark = pytest.mark.equipement

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


@given(parsers.parse('une catégorie d\'équipement "{name}" existe'))
def given_category(env, name, context):
    cat = env['telecom.equipment.category'].create({'name': name})
    context['category'] = cat


@given(parsers.parse('un site "{name}" avec le code "{code}" existe'))
def given_site(env, name, code, context):
    site = env['telecom.site'].create({
        'name': name, 'code_interne': code, 'site_type': 'pylone_greenfield',
    })
    context['site'] = site


@when(parsers.parse(
    'je crée un équipement "{name}" avec le N° série "{serial}"'
))
def when_create_equipment(env, name, serial, context):
    cat = context.get('category') or env['telecom.equipment.category'].create({'name': 'Cat Test'})
    context['equipment'] = _catch(lambda: env['telecom.equipment'].create({
        'name': name,
        'numero_serie': serial,
        'category_id': cat.id,
    }), context)


@given(parsers.parse('un équipement avec le N° série "{serial}" existe déjà'))
def given_equipment_with_serial(env, serial, context):
    cat = context.get('category') or env['telecom.equipment.category'].create({'name': 'Cat Test'})
    env['telecom.equipment'].create({
        'name': 'Équipement Existant', 'numero_serie': serial, 'category_id': cat.id,
    })


@when(parsers.parse('je tente de créer un équipement avec le même N° série "{serial}"'))
def when_create_duplicate_serial(env, serial, context):
    cat = context.get('category') or env['telecom.equipment.category'].create({'name': 'Cat Test'})
    _catch(lambda: env['telecom.equipment'].create({
        'name': 'Doublon', 'numero_serie': serial, 'category_id': cat.id,
    }), context)


@given(parsers.parse('un équipement à l\'état "{state}" existe'))
def given_equipment_state(env, state, context):
    cat = context.get('category') or env['telecom.equipment.category'].create({'name': 'Cat Test'})
    eq = env['telecom.equipment'].create({
        'name': 'Équipement Test', 'numero_serie': f'SN-{state}-001', 'category_id': cat.id,
    })
    eq.write({'state': state})
    context['equipment'] = eq


@when(parsers.parse('je passe l\'équipement à l\'état "{state}"'))
def when_equipment_state_transition(context, state):
    context['equipment'].write({'state': state})


@then('l\'équipement est créé avec succès')
def then_equipment_created(context):
    assert context.get('error') is None
    assert context.get('equipment')


@then(parsers.parse('l\'état de l\'équipement est "{state}"'))
def then_equipment_state(context, state):
    eq = context['equipment']
    assert eq.state == state, f"État attendu '{state}', obtenu '{eq.state}'"


@given(parsers.parse(
    'un équipement avec une date de fin de garantie "{date_fin}" existe'
))
def given_equipment_warranty(env, date_fin, context):
    cat = context.get('category') or env['telecom.equipment.category'].create({'name': 'Cat'})
    eq = env['telecom.equipment'].create({
        'name': 'Équipement Garantie', 'numero_serie': 'SN-GARANTIE-001',
        'category_id': cat.id, 'date_fin_garantie': date_fin,
    })
    context['equipment'] = eq


@then('l\'alerte de fin de garantie est active')
def then_warranty_alert_active(context):
    eq = context['equipment']
    mocked = context.get('mocked_today')
    if mocked:
        with freeze_time(mocked):
            eq._compute_garantie_expiring()
    assert eq.garantie_expiring, "Alerte garantie non active"


@then('l\'alerte de fin de garantie est inactive')
def then_warranty_alert_inactive(context):
    eq = context['equipment']
    mocked = context.get('mocked_today')
    if mocked:
        with freeze_time(mocked):
            eq._compute_garantie_expiring()
    assert not eq.garantie_expiring, "Alerte garantie active à tort"


@when(parsers.parse('je crée un outillage "{name}" avec numéro "{ref}"'))
def when_create_outillage(env, name, ref, context):
    context['outillage'] = _catch(lambda: env['telecom.outillage'].create({
        'name': name, 'numero_serie': ref,
    }), context)


@when(parsers.parse('la prochaine date d\'étalonnage est "{date_etal}"'))
def when_set_etalonnage(context, date_etal):
    o = context.get('outillage')
    if o:
        o.write({'date_prochain_etalonnage': date_etal})


@then('l\'outillage est créé avec succès')
def then_outillage_created(context):
    assert context.get('error') is None
    assert context.get('outillage')


@given(parsers.parse(
    'un outillage avec dernière date d\'étalonnage "{date_etal}" existe'
))
def given_outillage_etalonnage(env, date_etal, context):
    o = env['telecom.outillage'].create({
        'name': 'Outillage Étalonnage', 'numero_serie': 'OT-001',
        'date_dernier_etalonnage': date_etal,
        'periodicite_etalonnage_mois': 12,
    })
    context['outillage'] = o


@then('l\'alerte d\'étalonnage est active')
def then_etalonnage_alert(context):
    o = context['outillage']
    mocked = context.get('mocked_today')
    if mocked:
        with freeze_time(mocked):
            o._compute_etalonnage_expiring()
    assert o.etalonnage_expiring, "Alerte étalonnage non active"


# ─────────────────────────────────────────────────────────────────────────────
# ACTIONS MÉTIER — Steps from equipement_actions.feature
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('un équipement "{name}" en stock sans site assigné'))
def given_equipment_no_site(env, name, context):
    cat = context.get('category') or env['telecom.equipment.category'].create({'name': 'Cat'})
    eq = env['telecom.equipment'].create({
        'name': name, 'numero_serie': 'SN-NOSITE-001', 'category_id': cat.id,
    })
    context['equipment'] = eq


@given(parsers.parse('un équipement "{name}" en stock avec un site assigné'))
def given_equipment_with_site(env, name, context):
    cat = context.get('category') or env['telecom.equipment.category'].create({'name': 'Cat'})
    site = context.get('site')
    eq = env['telecom.equipment'].create({
        'name': name, 'numero_serie': 'SN-SITE-001', 'category_id': cat.id,
        'site_id': site.id,
    })
    context['equipment'] = eq


@when("je tente d'installer l'équipement via l'action métier")
def when_try_install(context):
    _catch(lambda: context['equipment'].action_installer(), context)


@when("j'installe l'équipement via l'action métier")
def when_install(context):
    _catch(lambda: context['equipment'].action_installer(), context)


@then("la date d'installation est renseignée")
def then_install_date_set(context):
    eq = context['equipment']
    assert eq.date_installation, "Date d'installation non renseignée."


@given('un équipement installé sur le site')
def given_equipment_installed(env, context):
    cat = context.get('category') or env['telecom.equipment.category'].create({'name': 'Cat'})
    site = context.get('site')
    eq = env['telecom.equipment'].create({
        'name': 'Équipement Installé', 'numero_serie': 'SN-INST-001',
        'category_id': cat.id, 'site_id': site.id,
    })
    eq.action_installer()
    context['equipment'] = eq


@when("je déclare l'équipement en panne")
def when_declare_panne(context):
    _catch(lambda: context['equipment'].action_declarer_panne(), context)


@when("je tente de déclarer l'équipement en panne")
def when_try_declare_panne(context):
    _catch(lambda: context['equipment'].action_declarer_panne(), context)


@given("le compteur d'historique est à 0")
def given_historique_zero(context):
    eq = context['equipment']
    assert len(eq.historique_ids) == 0


@then(parsers.parse("le compteur d'historique est à {count:d}"))
def then_historique_count(context, count):
    eq = context['equipment']
    assert len(eq.historique_ids) == count, (
        f"Historique attendu: {count}, obtenu: {len(eq.historique_ids)}"
    )


@then(parsers.parse('le dernier événement contient "{old}" et "{new}"'))
def then_last_event_contains(context, old, new):
    eq = context['equipment']
    last = eq.historique_ids.sorted('id', reverse=True)[0]
    assert old in last.description and new in last.description, (
        f"Description: '{last.description}' — attendu '{old}' et '{new}'"
    )


@when(parsers.parse(
    'je tente de créer un équipement acheté le "{date_achat}" installé le "{date_install}"'
))
def when_create_equipment_bad_dates(env, date_achat, date_install, context):
    cat = context.get('category') or env['telecom.equipment.category'].create({'name': 'Cat'})
    _catch(lambda: env['telecom.equipment'].create({
        'name': 'Équipement Dates Test', 'numero_serie': 'SN-DATES-001',
        'category_id': cat.id, 'date_achat': date_achat,
        'date_installation': date_install,
    }), context)
