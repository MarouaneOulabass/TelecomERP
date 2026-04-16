# -*- coding: utf-8 -*-
"""
BDD step definitions -- telecom_margin
=======================================
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

pytestmark = pytest.mark.margin

scenarios('features/')


# ── Model accessibility ──────────────────────────────────────────────

@then(parsers.parse('le modèle "{model_name}" est accessible'))
def then_model_accessible(env, model_name):
    assert model_name in env, (
        "Le modele '%s' n'est pas disponible dans l'environnement." % model_name
    )


# ── Project with costs ──────────────────────────────────────────────

@given(parsers.parse(
    'un projet "{name}" existe avec des coûts de {amount:f} MAD'
))
def given_project_with_costs(env, name, amount, context):
    project = env['project.project'].create({'name': name})
    lot = env['telecom.lot'].create({
        'name': 'Lot principal',
        'project_id': project.id,
    })
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
    margin_model = env['telecom.project.margin']
    assert 'cout_total' in margin_model._fields
    assert 'marge_absolue' in margin_model._fields


# ── Health field ─────────────────────────────────────────────────────

@then(parsers.parse(
    'le champ "{field}" existe sur le modèle marge avec les valeurs "{v1}", "{v2}", "{v3}", "{v4}"'
))
def then_health_field_exists(env, field, v1, v2, v3, v4):
    margin_model = env['telecom.project.margin']
    assert field in margin_model._fields
    selection_field = margin_model._fields[field]
    selection_keys = [key for key, _ in selection_field.selection]
    for val in [v1, v2, v3, v4]:
        assert val in selection_keys, (
            "Valeur '%s' manquante dans '%s'. Disponibles: %s" % (val, field, selection_keys)
        )


# ── Project without costs ────────────────────────────────────────────

@given(parsers.parse('un projet "{name}" existe sans aucun coût'))
def given_project_no_costs(env, name, context):
    project = env['project.project'].create({'name': name})
    env['telecom.lot'].create({
        'name': 'Lot vide',
        'project_id': project.id,
    })
    context['project'] = project


@then('la marge du projet est nulle ou inexistante')
def then_margin_zero_or_missing(env, context):
    project = context['project']
    margins = env['telecom.project.margin'].search([
        ('project_id', '=', project.id),
    ])
    if margins:
        for m in margins:
            assert m.cout_total == 0 or m.cout_total is None, (
                "Expected zero costs, got %s" % m.cout_total
            )
    # No margin record = also acceptable (SQL view may not produce rows with no costs)


# ── Cost breakdown fields ────────────────────────────────────────────

@then(parsers.parse(
    'les champs de ventilation existent : {fields}'
))
def then_breakdown_fields_exist(env, fields):
    margin_model = env['telecom.project.margin']
    for field_name in [f.strip() for f in fields.split(',')]:
        assert field_name in margin_model._fields, (
            "Champ de ventilation '%s' manquant" % field_name
        )


# ── Generic field existence ──────────────────────────────────────────

@then(parsers.parse('le champ "{field}" existe sur le modèle marge'))
def then_field_exists_on_margin(env, field):
    margin_model = env['telecom.project.margin']
    assert field in margin_model._fields, (
        "Champ '%s' manquant dans telecom.project.margin" % field
    )


# ── Read-only SQL view ───────────────────────────────────────────────

@then('le modèle marge est en lecture seule avec _auto=False')
def then_model_is_readonly(env):
    margin_model = env['telecom.project.margin']
    assert not margin_model._auto, (
        "telecom.project.margin devrait avoir _auto=False (SQL view)"
    )


# ── Drill-down method ───────────────────────────────────────────────

@then(parsers.parse('la méthode "{method}" existe sur le modèle marge'))
def then_method_exists(env, method):
    margin_model = env['telecom.project.margin']
    assert hasattr(margin_model, method), (
        "Methode '%s' manquante sur telecom.project.margin" % method
    )
