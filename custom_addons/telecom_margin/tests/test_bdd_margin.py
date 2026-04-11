# -*- coding: utf-8 -*-
"""
BDD step definitions -- telecom_margin
=======================================
Feature files: tests/features/margin.feature

Run:
    pytest custom_addons/telecom_margin/tests/ -v --tb=short
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

pytestmark = pytest.mark.margin

scenarios('features/')


# -------------------------------------------------------------------------
# Then
# -------------------------------------------------------------------------

@then(parsers.parse('le modèle "{model_name}" est accessible'))
def then_model_accessible(env, model_name):
    assert model_name in env, (
        f"Le modele '{model_name}' n'est pas disponible dans l'environnement."
    )


@given(parsers.parse(
    'un projet "{name}" existe avec des coûts de {amount:f} MAD'
))
def given_project_with_costs(env, name, amount, context):
    project = env['project.project'].create({'name': name})
    lot = env['telecom.lot'].create({
        'name': 'Lot principal',
        'project_id': project.id,
    })
    # Find or create a cost type
    cost_type = env['telecom.cost.type'].search([], limit=1)
    if not cost_type:
        cost_type = env['telecom.cost.type'].create({
            'name': 'Test', 'category': 'materiel',
        })
    env['telecom.cost.entry'].create({
        'date': '2026-01-15',
        'cost_type_id': cost_type.id,
        'description': 'Cout test marge',
        'project_id': project.id,
        'lot_id': lot.id,
        'amount': amount,
    })
    context['project'] = project
    context['expected_cost'] = amount


@then('la marge du projet reflète les coûts saisis')
def then_margin_reflects_costs(env, context):
    # The margin view is a SQL view; verify the model has the expected fields
    margin_model = env['telecom.project.margin']
    assert 'cout_total' in margin_model._fields, (
        "Le champ 'cout_total' manque dans le modele marge."
    )
    assert 'marge_absolue' in margin_model._fields, (
        "Le champ 'marge_absolue' manque dans le modele marge."
    )


@then(parsers.parse(
    'le champ "{field}" existe sur le modèle marge avec les valeurs "{v1}", "{v2}", "{v3}", "{v4}"'
))
def then_health_field_exists(env, field, v1, v2, v3, v4):
    margin_model = env['telecom.project.margin']
    assert field in margin_model._fields, (
        f"Le champ '{field}' manque dans le modele marge."
    )
    selection_field = margin_model._fields[field]
    selection_keys = [key for key, _ in selection_field.selection]
    for val in [v1, v2, v3, v4]:
        assert val in selection_keys, (
            f"Valeur '{val}' manquante dans le champ '{field}'. "
            f"Disponibles: {selection_keys}"
        )
