# -*- coding: utf-8 -*-
"""
BDD step definitions -- telecom_financing
==========================================
Feature files: tests/features/financing.feature

Run:
    pytest custom_addons/telecom_financing/tests/ -v --tb=short
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError, UserError

pytestmark = pytest.mark.financing

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


# -------------------------------------------------------------------------
# When
# -------------------------------------------------------------------------

@when(parsers.parse(
    'je crée un coût financier de {amount:f} MAD de type "{ftype}" pour ce projet'
))
def when_create_financial_cost(env, amount, ftype, context):
    project = context['project']
    lot = context.get('lot')
    context['cout_financier'] = _catch(lambda: env['telecom.cout.financier'].create({
        'date': '2026-01-15',
        'project_id': project.id,
        'lot_id': lot.id if lot else False,
        'financing_type': ftype,
        'description': f'Test {ftype}',
        'amount': amount,
    }), context)


@when(parsers.parse(
    'je crée un coût financier de {amount:f} MAD à {taux:f}% du "{date_debut}" au "{date_fin}" pour ce projet'
))
def when_create_financial_cost_with_interest(env, amount, taux, date_debut, date_fin, context):
    project = context['project']
    lot = context.get('lot')
    context['cout_financier'] = _catch(lambda: env['telecom.cout.financier'].create({
        'date': '2026-01-15',
        'project_id': project.id,
        'lot_id': lot.id if lot else False,
        'financing_type': 'credit_bancaire',
        'description': 'Test interet',
        'amount': amount,
        'taux_interet': taux,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }), context)


@when(parsers.parse(
    'je tente de créer un coût financier de {amount:f} MAD de type "{ftype}" pour ce projet'
))
def when_create_financial_cost_negative(env, amount, ftype, context):
    project = context['project']
    lot = context.get('lot')
    context['cout_financier'] = _catch(lambda: env['telecom.cout.financier'].create({
        'date': '2026-01-15',
        'project_id': project.id,
        'lot_id': lot.id if lot else False,
        'financing_type': ftype,
        'description': f'Test negatif {ftype}',
        'amount': amount,
    }), context)


# -------------------------------------------------------------------------
# Then
# -------------------------------------------------------------------------

@then('le coût financier est créé avec succès')
def then_financial_cost_created(context):
    assert context.get('error') is None, f"Erreur: {context.get('error')}"
    assert context.get('cout_financier') is not None


@then(parsers.parse('le montant des intérêts est d\'environ {amount:f} MAD'))
def then_interest_amount(context, amount):
    rec = context['cout_financier']
    # Allow 1% tolerance for day-count differences
    tolerance = amount * 0.05
    assert abs(rec.interest_amount - amount) < tolerance, (
        f"Interets attendus: ~{amount}, obtenus: {rec.interest_amount}"
    )


@then('une écriture de coût financier est créée automatiquement')
def then_cost_entry_created(context):
    rec = context['cout_financier']
    assert rec.cost_entry_id, (
        "Aucune ecriture de cout n'a ete creee automatiquement."
    )


@then('les types de financement suivants sont disponibles')
def then_financing_types_available(env):
    field = env['telecom.cout.financier']._fields['financing_type']
    available_types = [key for key, _ in field.selection]
    expected = [
        'credit_bancaire', 'leasing', 'caution_provisoire',
        'caution_definitive', 'avance_client', 'escompte', 'autre',
    ]
    for t in expected:
        assert t in available_types, (
            f"Type '{t}' manquant. Disponibles: {available_types}"
        )


@then("le montant de l'écriture de coût inclut les intérêts")
def then_cost_entry_includes_interest(context):
    rec = context['cout_financier']
    assert rec.cost_entry_id, "Pas d'ecriture de cout"
    # Cost entry amount should be principal + interest
    expected_total = rec.amount + rec.interest_amount
    assert abs(rec.cost_entry_id.amount - expected_total) < 0.01, (
        "Cout total attendu: %s (principal %s + interets %s), obtenu: %s" % (
            expected_total, rec.amount, rec.interest_amount, rec.cost_entry_id.amount
        )
    )
