# -*- coding: utf-8 -*-
"""
BDD step definitions — telecom.site
====================================
Feature files: tests/features/site_*.feature

Run:
    pytest custom_addons/telecom_site/tests/ -v --tb=short
    pytest custom_addons/telecom_site/tests/ -m site -v
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError, UserError
from freezegun import freeze_time

pytestmark = pytest.mark.site

# Load all feature files in this module
scenarios('features/')


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _create_site(env, code, name='Site BDD Test', site_type='pylone_greenfield', **kwargs):
    """Helper: create a telecom.site with sensible defaults."""
    vals = {'name': name, 'code_interne': code, 'site_type': site_type}
    vals.update(kwargs)
    return env['telecom.site'].create(vals)


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


# ─────────────────────────────────────────────────────────────────────────────
# Background
# ─────────────────────────────────────────────────────────────────────────────

@given("un partenaire opérateur \"Maroc Telecom\" de type \"operator\" existe")
def partner_operator(env, context):
    p = env['res.partner'].create({'name': 'Maroc Telecom', 'partner_type': 'operator'})
    context['operator'] = p


@given("un partenaire bailleur \"Propriétaire Foncier SA\" de type \"lessor\" existe")
def partner_lessor(env, context):
    p = env['res.partner'].create({'name': 'Propriétaire Foncier SA', 'partner_type': 'lessor'})
    context['lessor'] = p


# ─────────────────────────────────────────────────────────────────────────────
# CREATION — When steps
# ─────────────────────────────────────────────────────────────────────────────

@when(parsers.parse(
    'je crée un site avec le code "{code}", le nom "{name}" et le type "{site_type}"'
))
def step_create_site_basic(env, code, name, site_type, context):
    context['site'] = _catch(lambda: _create_site(env, code, name, site_type), context)


@when(parsers.parse('je crée un site avec la latitude GPS "{lat}"'))
def step_create_site_lat(env, lat, context):
    context['site'] = _catch(
        lambda: _create_site(env, 'GPS-LAT-001', gps_lat=float(lat)), context
    )


@when(parsers.parse('je crée un site avec la longitude GPS "{lng}"'))
def step_create_site_lng(env, lng, context):
    context['site'] = _catch(
        lambda: _create_site(env, 'GPS-LNG-001', gps_lng=float(lng)), context
    )


@when(parsers.parse(
    'je crée un site avec la latitude GPS "{lat}" et la longitude GPS "{lng}"'
))
def step_create_site_coords(env, lat, lng, context):
    context['site'] = _catch(
        lambda: _create_site(env, 'GPS-BOTH-001', gps_lat=float(lat), gps_lng=float(lng)),
        context
    )


@when(parsers.parse(
    'je crée un site avec la date début de bail "{date_debut}"'
    ' et la date fin de bail "{date_fin}"'
))
def step_create_site_bail_dates(env, date_debut, date_fin, context):
    context['site'] = _catch(
        lambda: _create_site(
            env, 'BAIL-001',
            bail_date_debut=date_debut,
            bail_date_fin=date_fin,
        ),
        context
    )


@when(parsers.parse(
    'je crée un site avec le code "{code}" dans une autre société'
))
def step_create_site_other_company(env, code, context):
    other = env['res.company'].create({'name': 'Autre Société Test'})
    context['site'] = _catch(
        lambda: env['telecom.site'].with_company(other).create({
            'name': 'Site Autre Société', 'code_interne': code, 'site_type': 'shelter',
        }),
        context
    )


@when('je tente de créer un second site avec le même code "TLM-001"')
def step_create_duplicate_site(env, context):
    context['site'] = _catch(
        lambda: _create_site(env, 'TLM-001', name='Doublon'), context
    )


# ─────────────────────────────────────────────────────────────────────────────
# CREATION — Given / state setup
# ─────────────────────────────────────────────────────────────────────────────

@given('un site avec le code interne "TLM-001" existe déjà dans la société courante')
def step_site_already_exists(env, context):
    context['existing'] = _create_site(env, 'TLM-001', name='Premier Site')


@given(parsers.parse(
    'la société courante possède déjà un site avec le code "{code}"'
))
def step_site_exists_current_company(env, code, context):
    context['existing'] = _create_site(env, code)


@given(parsers.parse(
    'un site avec latitude "{lat}" et longitude "{lng}" existe'
))
def step_site_with_gps(env, lat, lng, context):
    context['site'] = _create_site(
        env, 'GPS-001', gps_lat=float(lat), gps_lng=float(lng)
    )


@given('un site sans coordonnées GPS existe')
def step_site_no_gps(env, context):
    context['site'] = _create_site(env, 'NO-GPS-001')


# ─────────────────────────────────────────────────────────────────────────────
# CREATION — Then assertions
# ─────────────────────────────────────────────────────────────────────────────

@then('le site est créé avec succès')
def step_site_created_ok(context):
    assert context.get('error') is None, f"Erreur inattendue : {context.get('error')}"
    assert context.get('site') is not None


@then(parsers.parse('l\'état du site est "{state}"'))
def step_site_state(context, state):
    site = context.get('site')
    assert site, "Aucun site dans le contexte."
    assert site.state == state, f"État attendu '{state}', obtenu '{site.state}'"


@then('la société rattachée est l\'entreprise courante')
def step_site_company(env, context):
    site = context.get('site')
    assert site.company_id == env.company


@then(parsers.parse('les types de sites disponibles incluent "{site_type}"'))
def step_site_type_available(env, site_type):
    available = [t[0] for t in env['telecom.site']._fields['site_type'].selection]
    assert site_type in available, f"Type '{site_type}' absent. Disponibles: {available}"


@then(parsers.parse('les wilayas disponibles incluent "{wilaya}"'))
def step_wilaya_available(env, wilaya):
    available = [w[0] for w in env['telecom.site']._fields['wilaya'].selection]
    assert wilaya in available, f"Wilaya '{wilaya}' absente. Disponibles: {available}"


@then(parsers.parse('une action URL contenant "{fragment1}" et "{fragment2}" est retournée'))
def step_action_url_contains(context, fragment1, fragment2):
    action = context.get('action')
    assert action, "Aucune action dans le contexte."
    assert action.get('type') == 'ir.actions.act_url'
    url = action.get('url', '')
    assert fragment1 in url, f"'{fragment1}' absent de l'URL '{url}'"
    assert fragment2 in url, f"'{fragment2}' absent de l'URL '{url}'"


@when('je demande l\'ouverture dans Google Maps')
def step_open_in_maps(context):
    site = context.get('site')
    assert site
    context['action'] = _catch(lambda: site.action_open_in_maps(), context)


# ─────────────────────────────────────────────────────────────────────────────
# CYCLE DE VIE
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse(
    'un site "{name}" avec le code "{code}" à l\'état "prospection" existe'
))
def step_site_in_prospection(env, name, code, context):
    context['site'] = _create_site(env, code, name)


@given(parsers.parse('le site est à l\'état "{state}"'))
def step_set_site_state(context, state):
    context['site'].write({'state': state})


@when(parsers.parse('je passe le site à l\'état "{state}"'))
def step_transition_site(context, state):
    site = context['site']
    action_map = {
        'etude':        'action_set_etude',
        'autorisation': 'action_set_autorisation',
        'deploiement':  'action_set_deploiement',
        'livre':        'action_set_livre',
        'maintenance':  'action_set_maintenance',
        'desactive':    'action_set_desactive',
    }
    method = action_map.get(state)
    if method:
        getattr(site, method)()
    else:
        site.write({'state': state})


@then(parsers.parse('le nombre de documents du site est "{count}"'))
def step_doc_count(context, count):
    site = context['site']
    assert site.document_count == int(count), (
        f"Nb documents attendu: {count}, obtenu: {site.document_count}"
    )


@then(parsers.parse('le nombre d\'interventions du site est "{count}"'))
def step_intervention_count(context, count):
    site = context['site']
    assert site.intervention_count == int(count)


@when(parsers.parse('j\'ajoute un document "{title}" de type "{doc_type}" au site'))
def step_add_document(env, context, title, doc_type):
    site = context['site']
    env['telecom.site.document'].create({
        'site_id': site.id,
        'name': title,
        'document_type': doc_type,
        'file': 'ZmFrZV9jb250ZW50',  # base64 of 'fake_content'
    })
    site.invalidate_recordset()


# ─────────────────────────────────────────────────────────────────────────────
# BAIL ALERTS
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('un site avec une date de fin de bail "{date_fin}" existe'))
def step_site_with_bail_end(env, date_fin, context):
    context['site'] = _create_site(env, 'BAIL-BDD-001', bail_date_fin=date_fin)


@given('un site sans date de fin de bail existe')
def step_site_no_bail(env, context):
    context['site'] = _create_site(env, 'NO-BAIL-BDD-001')


@when('je recalcule l\'alerte d\'expiration du bail')
def step_compute_bail_warning(context):
    """
    Recompute bail_expiration_warning.
    The mocked today date is set via freezegun in the scenario's given step.
    """
    site = context['site']
    mocked = context.get('mocked_today')
    if mocked:
        with freeze_time(mocked):
            site._compute_bail_expiration_warning()
    else:
        site._compute_bail_expiration_warning()


@then(parsers.parse('le champ "{field}" est True'))
def step_field_true(context, field):
    record = context.get('site') or context.get('record')
    assert record, "Aucun enregistrement dans le contexte."
    val = getattr(record, field)
    assert val is True, f"Champ '{field}' attendu True, obtenu {val!r}"


@then(parsers.parse('le champ "{field}" est False'))
def step_field_false(context, field):
    record = context.get('site') or context.get('record')
    assert record, "Aucun enregistrement dans le contexte."
    val = getattr(record, field)
    assert val is False, f"Champ '{field}' attendu False, obtenu {val!r}"
