# -*- coding: utf-8 -*-
"""
BDD step definitions — telecom_fleet
=======================================
Feature files: tests/features/vehicule.feature

Run:
    pytest custom_addons/telecom_fleet/tests/ -v --tb=short
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError, UserError
from freezegun import freeze_time

pytestmark = pytest.mark.fleet

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


@given(parsers.parse('un employé technicien "{name}" existe'))
def given_technicien(env, name, context):
    emp = env['hr.employee'].create({'name': name})
    context['employee'] = emp


@when(parsers.parse(
    'je crée un véhicule "{name}" avec l\'immatriculation "{immatriculation}"'
))
def when_create_vehicle(env, name, immatriculation, context):
    # Parse name as "Marque Modele" — name is computed from marque + modele
    parts = name.split(' ', 1)
    marque = parts[0] if parts else 'Test'
    modele = parts[1] if len(parts) > 1 else 'Test'
    context['vehicle'] = _catch(lambda: env['telecom.vehicle'].create({
        'immatriculation': immatriculation,
        'marque': marque,
        'modele': modele,
    }), context)


@given(parsers.parse(
    'un véhicule avec l\'immatriculation "{immatriculation}" existe déjà'
))
def given_vehicle_exists(env, immatriculation, context):
    env['telecom.vehicle'].create({'immatriculation': immatriculation, 'marque': 'Test', 'modele': 'Test'})


@when(parsers.parse(
    'je tente de créer un véhicule avec la même immatriculation "{immatriculation}"'
))
def when_create_duplicate_vehicle(env, immatriculation, context):
    _catch(lambda: env['telecom.vehicle'].create({
        'immatriculation': immatriculation, 'marque': 'Test', 'modele': 'Test',
    }), context)


@given(parsers.parse(
    'un véhicule avec contrôle technique expirant le "{date_ct}" existe'
))
def given_vehicle_ct(env, date_ct, context):
    v = env['telecom.vehicle'].create({
        'immatriculation': 'CT-TEST-001',
        'marque': 'Test', 'modele': 'CT',
        'carte_grise_expiration': date_ct,
    })
    context['vehicle'] = v


@given(parsers.parse(
    'un véhicule avec assurance expirant le "{date_assurance}" existe'
))
def given_vehicle_insurance(env, date_assurance, context):
    v = env['telecom.vehicle'].create({
        'immatriculation': 'ASS-TEST-001',
        'marque': 'Test', 'modele': 'Assurance',
        'assurance_expiration': date_assurance,
    })
    context['vehicle'] = v


@then('le véhicule est créé avec succès')
def then_vehicle_created(context):
    assert context.get('error') is None
    assert context.get('vehicle')


@then('l\'alerte contrôle technique est active')
def then_ct_alert_active(context):
    v = context['vehicle']
    mocked = context.get('mocked_today')
    if mocked:
        with freeze_time(mocked):
            v._compute_document_alerts()
    assert v.visite_technique_expiring, "Alerte CT non active"


@then('l\'alerte contrôle technique est inactive')
def then_ct_alert_inactive(context):
    v = context['vehicle']
    mocked = context.get('mocked_today')
    if mocked:
        with freeze_time(mocked):
            v._compute_document_alerts()
    assert not v.visite_technique_expiring, "Alerte CT active à tort"


@then('l\'alerte assurance est active')
def then_insurance_alert(context):
    v = context['vehicle']
    mocked = context.get('mocked_today')
    if mocked:
        with freeze_time(mocked):
            v._compute_document_alerts()
    assert v.assurance_expiring, "Alerte assurance non active"


@given(parsers.parse(
    'un véhicule "{name}" avec l\'immatriculation "{immatriculation}" existe'
))
def given_vehicle_by_name(env, name, immatriculation, context):
    parts = name.split(' ', 1)
    marque = parts[0] if parts else 'Test'
    modele = parts[1] if len(parts) > 1 else 'Test'
    v = env['telecom.vehicle'].create({
        'immatriculation': immatriculation,
        'marque': marque,
        'modele': modele,
    })
    context['vehicle'] = v


@when(parsers.parse(
    'je crée un entretien "{type_entretien}" du "{date_ent}" pour ce véhicule'
))
def when_create_entretien(env, type_entretien, date_ent, context):
    v = context['vehicle']
    ent = env['telecom.vehicle.entretien'].create({
        'vehicle_id': v.id,
        'name': type_entretien,
        'entretien_type': 'vidange',
        'date': date_ent,
    })
    context['entretien'] = ent


@then('l\'entretien est enregistré pour le véhicule')
def then_entretien_created(context):
    assert context.get('entretien'), "Entretien non créé."


# ─────────────────────────────────────────────────────────────────────────────
# CYCLE DE VIE VÉHICULE
# ─────────────────────────────────────────────────────────────────────────────

@when('je mets le véhicule en mission')
def when_vehicle_mission(context):
    _catch(lambda: context['vehicle'].action_affecter_mission(), context)


@when('je retourne le véhicule')
def when_vehicle_return(context):
    _catch(lambda: context['vehicle'].action_retour(), context)


@then(parsers.parse("l'état du véhicule est \"{state}\""))
def then_vehicle_state(context, state):
    v = context['vehicle']
    assert v.state == state, f"État attendu '{state}', obtenu '{v.state}'"


# ─────────────────────────────────────────────────────────────────────────────
# ALERTE KM ENTRETIEN
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse(
    'un véhicule avec km dernier entretien "{km_dernier}" et intervalle "{intervalle}"'
))
def given_vehicle_km(env, km_dernier, intervalle, context):
    v = env['telecom.vehicle'].create({
        'name': 'Véhicule KM Test', 'immatriculation': 'KM-TEST-001',
        'marque': 'Test', 'modele': 'Test',
        'km_dernier_entretien': int(km_dernier),
        'intervalle_entretien_km': int(intervalle),
    })
    context['vehicle'] = v


@given(parsers.parse('le kilométrage actuel est "{km}"'))
def given_km_actuel(context, km):
    context['vehicle'].write({'kilometrage': int(km)})


@then("l'alerte entretien km est active")
def then_km_alert_active(context):
    v = context['vehicle']
    assert v.entretien_km_alerte, "Alerte entretien km non active"
