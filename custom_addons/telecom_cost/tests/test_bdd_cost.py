# -*- coding: utf-8 -*-
"""
BDD step definitions — telecom_cost
=====================================
Feature files: tests/features/cost_entry.feature

Run:
    pytest custom_addons/telecom_cost/tests/ -v --tb=short
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError, UserError

pytestmark = pytest.mark.cost

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
# Given — Projects, lots, tasks, cost types
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


@given(parsers.parse('un lot orphelin "{name}" existe'))
def given_orphan_lot(env, name, context):
    """Create a lot attached to a throwaway project (for negative tests)."""
    tmp_project = env['project.project'].create({'name': 'Tmp Orphan'})
    lot = env['telecom.lot'].create({
        'name': name,
        'project_id': tmp_project.id,
    })
    context['lot'] = lot
    return lot


@given(parsers.parse('une tache "{name}" existe pour ce projet'))
def given_task(env, name, context):
    project = context['project']
    task = env['project.task'].create({
        'name': name,
        'project_id': project.id,
    })
    context['task'] = task
    return task


@given(parsers.parse('un type de coût "{name}" de catégorie "{category}" existe'))
def given_cost_type(env, name, category, context):
    cost_type = env['telecom.cost.type'].search([
        ('name', '=', name),
    ], limit=1)
    if not cost_type:
        cost_type = env['telecom.cost.type'].create({
            'name': name,
            'category': category,
        })
    context['cost_type'] = cost_type
    return cost_type


@given(parsers.parse(
    'un coût de {amount:f} MAD existe en brouillon pour ce projet et ce lot'
))
def given_draft_cost(env, amount, context):
    cost_type = context.get('cost_type')
    entry = env['telecom.cost.entry'].create({
        'date': '2026-01-15',
        'cost_type_id': cost_type.id,
        'description': 'Cout test brouillon',
        'project_id': context['project'].id,
        'lot_id': context['lot'].id,
        'amount': amount,
    })
    assert entry.state == 'draft'
    context['cost_entry'] = entry
    return entry


# -------------------------------------------------------------------------
# When — Create cost entries
# -------------------------------------------------------------------------

@when(parsers.parse(
    'je créé un coût de {amount:f} MAD pour ce projet et ce lot'
))
def when_create_cost(env, amount, context):
    cost_type = context.get('cost_type')
    context['cost_entry'] = _catch(lambda: env['telecom.cost.entry'].create({
        'date': '2026-01-15',
        'cost_type_id': cost_type.id,
        'description': 'Cout test nominal',
        'project_id': context['project'].id,
        'lot_id': context['lot'].id,
        'amount': amount,
    }), context)


@when(parsers.parse('je tente de creer un coût de {amount:f} MAD sans projet'))
def when_create_cost_no_project(env, amount, context):
    cost_type = context.get('cost_type')
    lot = context.get('lot')
    context['cost_entry'] = _catch(lambda: env['telecom.cost.entry'].create({
        'date': '2026-01-15',
        'cost_type_id': cost_type.id,
        'description': 'Cout sans projet',
        'project_id': False,
        'lot_id': lot.id if lot else False,
        'amount': amount,
    }), context)


@when(parsers.parse('je tente de creer un coût de {amount:f} MAD sans lot'))
def when_create_cost_no_lot(env, amount, context):
    cost_type = context.get('cost_type')
    project = context.get('project')
    context['cost_entry'] = _catch(lambda: env['telecom.cost.entry'].create({
        'date': '2026-01-15',
        'cost_type_id': cost_type.id,
        'description': 'Cout sans lot',
        'project_id': project.id,
        'lot_id': False,
        'amount': amount,
    }), context)


@when(parsers.parse(
    'je tente de creer un coût de {amount:f} MAD pour ce projet et ce lot'
))
def when_create_cost_negative(env, amount, context):
    cost_type = context.get('cost_type')
    context['cost_entry'] = _catch(lambda: env['telecom.cost.entry'].create({
        'date': '2026-01-15',
        'cost_type_id': cost_type.id,
        'description': 'Cout montant negatif',
        'project_id': context['project'].id,
        'lot_id': context['lot'].id,
        'amount': amount,
    }), context)


@when(parsers.parse(
    'je créé un coût de {amount:f} MAD pour ce projet et ce lot sans tache'
))
def when_create_cost_no_task(env, amount, context):
    cost_type = context.get('cost_type')
    context['cost_entry'] = _catch(lambda: env['telecom.cost.entry'].create({
        'date': '2026-01-15',
        'cost_type_id': cost_type.id,
        'description': 'Cout sans tache',
        'project_id': context['project'].id,
        'lot_id': context['lot'].id,
        'amount': amount,
        'task_id': False,
    }), context)


@when(parsers.parse(
    'je créé un coût de {amount:f} MAD pour ce projet et ce lot avec cette tache'
))
def when_create_cost_with_task(env, amount, context):
    cost_type = context.get('cost_type')
    context['cost_entry'] = _catch(lambda: env['telecom.cost.entry'].create({
        'date': '2026-01-15',
        'cost_type_id': cost_type.id,
        'description': 'Cout avec tache',
        'project_id': context['project'].id,
        'lot_id': context['lot'].id,
        'amount': amount,
        'task_id': context['task'].id,
    }), context)


# -------------------------------------------------------------------------
# When — Workflow
# -------------------------------------------------------------------------

@when('je confirme le cout')
def when_confirm_cost(context):
    entry = context['cost_entry']
    entry.action_confirm()


@when('je valide le cout')
def when_validate_cost(context):
    entry = context['cost_entry']
    entry.action_validate()


# -------------------------------------------------------------------------
# Then — Assertions
# -------------------------------------------------------------------------

@then('le coût est créé avec succès')
def then_cost_created(context):
    assert context.get('error') is None, f"Erreur: {context.get('error')}"
    assert context.get('cost_entry') is not None


@then(parsers.parse('le montant du coût est {amount:f}'))
def then_cost_amount(context, amount):
    entry = context['cost_entry']
    assert abs(entry.amount - amount) < 0.01, (
        f"Montant attendu: {amount}, obtenu: {entry.amount}"
    )


@then('une erreur est levée')
def then_error_raised(context):
    assert context.get('error'), (
        "Une erreur etait attendue mais aucune erreur n'a ete levee."
    )


@then(parsers.parse('le flag task_missing est True'))
def then_task_missing_true(context):
    entry = context['cost_entry']
    assert entry.task_missing is True, (
        f"task_missing attendu: True, obtenu: {entry.task_missing}"
    )


@then(parsers.parse('le flag task_missing est False'))
def then_task_missing_false(context):
    entry = context['cost_entry']
    assert entry.task_missing is False, (
        f"task_missing attendu: False, obtenu: {entry.task_missing}"
    )


@then(parsers.parse('l\'etat du coût est "{state}"'))
def then_cost_state(context, state):
    entry = context['cost_entry']
    assert entry.state == state, (
        f"Etat attendu: {state}, obtenu: {entry.state}"
    )


@then(parsers.parse('au moins {count:d} types de couts existent dans le systeme'))
def then_cost_types_count(env, count):
    types = env['telecom.cost.type'].search([])
    assert len(types) >= count, (
        f"Types de couts attendus: >= {count}, trouves: {len(types)}"
    )
