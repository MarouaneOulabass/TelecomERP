# -*- coding: utf-8 -*-
"""
BDD step definitions -- telecom_carburant
==========================================
Feature files: tests/features/carburant.feature

Run:
    pytest custom_addons/telecom_carburant/tests/ -v --tb=short
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError, UserError

pytestmark = pytest.mark.carburant

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

@given(parsers.parse('un projet "{name}" existe'))
def given_project(env, name, context):
    project = env['project.project'].create({'name': name})
    context['project'] = project
    return project


@given(parsers.parse('un lot "{name}" existe pour ce projet'))
def given_lot_for_project(env, name, context):
    project = context['project']
    lot = env['telecom.lot'].create({
        'name': name,
        'project_id': project.id,
    })
    context['lot'] = lot
    return lot


@given(parsers.parse(
    'un véhicule "{name}" avec l\'immatriculation "{immatriculation}" existe'
))
def given_vehicle(env, name, immatriculation, context):
    parts = name.split(' ', 1)
    marque = parts[0] if parts else 'Test'
    modele = parts[1] if len(parts) > 1 else 'Test'
    vehicle = env['telecom.vehicle'].create({
        'immatriculation': immatriculation,
        'marque': marque,
        'modele': modele,
    })
    context['vehicle'] = vehicle
    return vehicle


# -------------------------------------------------------------------------
# When
# -------------------------------------------------------------------------

@when(parsers.parse(
    'je crée un plein de {litres:f} litres à {prix:f} MAD/litre pour ce véhicule'
))
def when_create_fillup(env, litres, prix, context):
    vehicle = context['vehicle']
    project = context['project']
    lot = context.get('lot')
    context['plein'] = _catch(lambda: env['telecom.plein.carburant'].create({
        'date': '2026-01-15',
        'vehicle_id': vehicle.id,
        'project_id': project.id,
        'lot_id': lot.id if lot else False,
        'litres': litres,
        'prix_litre': prix,
    }), context)


@when(parsers.parse(
    'je tente de créer un plein de {litres:f} litres à {prix:f} MAD/litre pour ce véhicule'
))
def when_create_fillup_negative(env, litres, prix, context):
    vehicle = context['vehicle']
    project = context['project']
    lot = context.get('lot')
    context['plein'] = _catch(lambda: env['telecom.plein.carburant'].create({
        'date': '2026-01-15',
        'vehicle_id': vehicle.id,
        'project_id': project.id,
        'lot_id': lot.id if lot else False,
        'litres': litres,
        'prix_litre': prix,
    }), context)


# -------------------------------------------------------------------------
# Then
# -------------------------------------------------------------------------

@then('le plein est créé avec succès')
def then_fillup_created(context):
    assert context.get('error') is None, f"Erreur: {context.get('error')}"
    assert context.get('plein') is not None


@then(parsers.parse('le montant du plein est {amount:f}'))
def then_fillup_amount(context, amount):
    plein = context['plein']
    assert abs(plein.amount - amount) < 0.01, (
        f"Montant attendu: {amount}, obtenu: {plein.amount}"
    )


@then('une écriture de coût carburant est créée automatiquement')
def then_cost_entry_created(context):
    plein = context['plein']
    assert plein.cost_entry_id, (
        "Aucune ecriture de cout n'a ete creee automatiquement."
    )


@then(parsers.parse('le plein est rattaché au véhicule "{immatriculation}"'))
def then_fillup_linked_to_vehicle(context, immatriculation):
    plein = context['plein']
    assert plein.vehicle_id.immatriculation == immatriculation, (
        f"Vehicule attendu: {immatriculation}, "
        f"obtenu: {plein.vehicle_id.immatriculation}"
    )


@then(parsers.parse("le montant de l'écriture de coût est {amount:f}"))
def then_cost_entry_amount(context, amount):
    plein = context['plein']
    assert plein.cost_entry_id, "Pas d'ecriture de cout"
    assert abs(plein.cost_entry_id.amount - amount) < 0.01, (
        "Montant cout attendu: %s, obtenu: %s" % (amount, plein.cost_entry_id.amount)
    )
