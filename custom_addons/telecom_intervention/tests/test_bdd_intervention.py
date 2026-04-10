# -*- coding: utf-8 -*-
"""
BDD step definitions — telecom.intervention
=============================================
Feature files: tests/features/intervention_*.feature

Run:
    pytest custom_addons/telecom_intervention/tests/ -v --tb=short
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError, UserError
from freezegun import freeze_time

pytestmark = pytest.mark.intervention

scenarios('features/')


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _catch(fn, context):
    try:
        result = fn()
        context['error'] = None
        return result
    except (ValidationError, UserError) as exc:
        context['error'] = str(exc)
    except Exception as exc:
        context['error'] = str(exc)


def _make_site(env, name='Site Test BI', code='BI-SITE-001'):
    return env['telecom.site'].create({
        'name': name, 'code_interne': code, 'site_type': 'pylone_greenfield',
    })


def _make_bi(env, site, date_planifiee='2024-03-15 09:00:00',
             state=None, sla_delai_heures=48, **kwargs):
    vals = {
        'site_id': site.id,
        'intervention_type': 'corrective',
        'date_planifiee': date_planifiee,
        'sla_delai_heures': sla_delai_heures,
    }
    vals.update(kwargs)
    bi = env['telecom.intervention'].create(vals)
    if state and state != 'draft':
        # Force state for setup purposes
        bi.write({'state': state})
    return bi


# ─────────────────────────────────────────────────────────────────────────────
# Background
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse(
    'un site "{name}" avec le code "{code}" existe'
))
def given_site(env, name, code, context):
    context['site'] = _make_site(env, name, code)


@given(parsers.parse('un site "{name}" existe'))
def given_site_simple(env, name, context):
    code = name.upper().replace(' ', '-')[:20]
    context['site'] = _make_site(env, name, code)


@given(parsers.parse('un employé technicien "{name}" existe'))
def given_technicien(env, name, context):
    emp = env['hr.employee'].create({'name': name})
    context['technicien'] = emp


@given(parsers.parse(
    'un employé chef de chantier "{name}" avec le groupe "chef_chantier" existe'
))
def given_chef(env, name, context):
    emp = env['hr.employee'].create({'name': name})
    context['chef'] = emp
    # Create user linked to this employee with chef group
    group = env.ref('telecom_base.group_telecom_chef_chantier', raise_if_not_found=False)
    user = env['res.users'].create({
        'name': name,
        'login': f"{name.lower().replace(' ', '.')}@test.com",
        'employee_id': emp.id,
        'groups_id': [(4, group.id)] if group else [],
    })
    context['chef_user'] = user


# ─────────────────────────────────────────────────────────────────────────────
# WORKFLOW — When/Given steps
# ─────────────────────────────────────────────────────────────────────────────

@when(parsers.parse(
    'je crée un bon d\'intervention pour le site "{site_name}"'
    ' planifié le "{date_planifiee}"'
))
def when_create_bi(env, site_name, date_planifiee, context):
    site = context.get('site') or env['telecom.site'].search(
        [('name', '=', site_name)], limit=1
    )
    # Set operator from site if available (simulates onchange)
    operateur_id = site.operateur_ids[0].id if site.operateur_ids else False
    context['bi'] = _catch(
        lambda: _make_bi(env, site, date_planifiee=date_planifiee,
                         operateur_id=operateur_id), context
    )


@given(parsers.parse(
    'un BI en brouillon avec la date planifiée "{date_planifiee}" existe'
))
def given_bi_draft_with_date(env, date_planifiee, context):
    site = context.get('site') or _make_site(env)
    context['bi'] = _make_bi(env, site, date_planifiee=date_planifiee)


@given('un BI en brouillon sans date planifiée existe')
def given_bi_no_date(env, context):
    site = context.get('site') or _make_site(env)
    bi = env['telecom.intervention'].create({
        'site_id': site.id,
        'intervention_type': 'corrective',
        'date_planifiee': '2024-01-01 08:00:00',  # required field
        'sla_delai_heures': 48,
    })
    # Remove the date after creation
    bi.write({'date_planifiee': False})
    context['bi'] = bi


@given(parsers.parse('un BI à l\'état "{state}" existe'))
def given_bi_in_state(env, state, context):
    site = context.get('site') or _make_site(env)
    context['bi'] = _make_bi(env, site, state=state)


@given(parsers.parse(
    'un BI avec début réel "{date_debut}" et fin réelle "{date_fin}" existe'
))
def given_bi_with_real_dates(env, date_debut, date_fin, context):
    site = context.get('site') or _make_site(env)
    bi = _make_bi(env, site, state='termine')
    bi.write({'date_debut_reel': date_debut, 'date_fin_reel': date_fin})
    context['bi'] = bi


@given(parsers.parse('un BI à l\'état "en_cours" sans fin réelle existe'))
def given_bi_no_end(env, context):
    site = context.get('site') or _make_site(env)
    bi = _make_bi(env, site, state='en_cours')
    bi.write({'date_fin_reel': False})
    context['bi'] = bi


@given(parsers.parse('je suis connecté en tant que chef de chantier "{name}"'))
def given_logged_as_chef(env, name, context):
    user = context.get('chef_user')
    if user:
        context['env_as_user'] = env(user=user.id)


@given('je suis connecté en tant que responsable')
def given_logged_as_responsable(env, context):
    group = env.ref('telecom_base.group_telecom_responsable', raise_if_not_found=False)
    if group:
        user = env['res.users'].create({
            'name': 'Responsable Test', 'login': 'resp.test@test.com',
            'groups_id': [(4, group.id)],
        })
        context['env_as_user'] = env(user=user.id)


@given('je suis connecté en tant que technicien sans droits de validation')
def given_logged_as_technicien(env, context):
    user = env['res.users'].create({
        'name': 'Technicien Test', 'login': 'tech.test@test.com',
        'groups_id': [],
    })
    context['env_as_user'] = env(user=user.id)


# Actions

@when('je planifie le BI')
def when_planifie(context):
    bi = context['bi']
    _catch(lambda: bi.action_planifier(), context)


@when('je tente de planifier le BI')
def when_try_planifie(context):
    bi = context['bi']
    _catch(lambda: bi.action_planifier(), context)


@when('je démarre le BI')
def when_demarrer(context):
    bi = context['bi']
    _catch(lambda: bi.action_demarrer(), context)


@when('je tente de démarrer le BI')
def when_try_demarrer(context):
    bi = context['bi']
    _catch(lambda: bi.action_demarrer(), context)


@when('je termine le BI')
def when_terminer(context):
    bi = context['bi']
    _catch(lambda: bi.action_terminer(), context)


@when('je tente de terminer le BI')
def when_try_terminer(context):
    bi = context['bi']
    _catch(lambda: bi.action_terminer(), context)


@when('je valide le BI')
def when_valider(context):
    bi = context['bi']
    env_to_use = context.get('env_as_user', bi.env)
    _catch(lambda: bi.with_env(env_to_use).action_valider(), context)


@when('je tente de valider le BI')
def when_try_valider(context):
    bi = context['bi']
    env_to_use = context.get('env_as_user', bi.env)
    _catch(lambda: bi.with_env(env_to_use).action_valider(), context)


@when("j'annule le BI")
def when_annuler(context):
    bi = context['bi']
    _catch(lambda: bi.action_annuler(), context)


@when("je tente d'annuler le BI")
def when_try_annuler(context):
    bi = context['bi']
    _catch(lambda: bi.action_annuler(), context)


@when('je remets le BI en brouillon')
def when_reset_draft(context):
    bi = context['bi']
    _catch(lambda: bi.action_reset_draft(), context)


@when('je tente de remettre le BI en brouillon')
def when_try_reset_draft(context):
    bi = context['bi']
    _catch(lambda: bi.action_reset_draft(), context)


@when(parsers.parse(
    'je crée un BI avec début réel "{debut}" et fin réelle "{fin}"'
))
def when_create_bi_bad_dates(env, debut, fin, context):
    site = context.get('site') or _make_site(env)
    _catch(lambda: env['telecom.intervention'].create({
        'site_id': site.id,
        'intervention_type': 'corrective',
        'date_planifiee': '2024-03-15 08:00:00',
        'sla_delai_heures': 48,
        'date_debut_reel': debut,
        'date_fin_reel': fin,
    }), context)


# ─────────────────────────────────────────────────────────────────────────────
# WORKFLOW — Then assertions
# ─────────────────────────────────────────────────────────────────────────────

@then('le bon d\'intervention est créé avec succès')
def then_bi_created(context):
    assert context.get('error') is None, f"Erreur: {context.get('error')}"
    assert context.get('bi') is not None


@then('le numéro du BI commence par "BI/"')
def then_bi_number(context):
    bi = context['bi']
    assert bi.name.startswith('BI/'), f"Numéro BI: '{bi.name}'"


@then(parsers.parse('l\'état du BI est "{state}"'))
def then_bi_state(context, state):
    bi = context['bi']
    assert bi.state == state, f"État attendu '{state}', obtenu '{bi.state}'"


@then('la date de début réelle est renseignée')
def then_start_date_set(context):
    bi = context['bi']
    assert bi.date_debut_reel, "Date de début réelle non renseignée."


@then('la date de fin réelle est renseignée')
def then_end_date_set(context):
    bi = context['bi']
    assert bi.date_fin_reel, "Date de fin réelle non renseignée."


@then(parsers.parse('la durée réelle du BI est "{heures}" heures'))
def then_duree_reelle(context, heures):
    bi = context['bi']
    expected = float(heures)
    assert abs(bi.duree_reelle - expected) < 0.01, (
        f"Durée attendue: {expected}h, obtenue: {bi.duree_reelle}h"
    )


@then(parsers.parse('l\'opérateur du BI est "{operator_name}"'))
def then_bi_operator(context, operator_name):
    bi = context['bi']
    assert bi.operateur_id.name == operator_name


@then(parsers.parse('les types d\'intervention disponibles incluent "{itype}"'))
def then_intervention_type_available(env, itype):
    available = [t[0] for t in env['telecom.intervention']._fields['intervention_type'].selection]
    assert itype in available, f"Type '{itype}' absent. Disponibles: {available}"


@given(parsers.parse(
    'le site "{site_name}" a un opérateur "{operator_name}" rattaché'
))
def given_site_with_operator(env, site_name, operator_name, context):
    site = context.get('site')
    op = env['res.partner'].create({'name': operator_name, 'partner_type': 'operator'})
    if site:
        site.write({'operateur_ids': [(4, op.id)]})


# ─────────────────────────────────────────────────────────────────────────────
# SLA steps
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse(
    'un BI planifié le "{date_planifiee}" avec un SLA de "{heures}" heures existe'
))
def given_bi_with_sla(env, date_planifiee, heures, context):
    site = context.get('site') or _make_site(env, code='SLA-SITE-001')
    context['bi'] = _make_bi(env, site, date_planifiee=date_planifiee,
                             sla_delai_heures=int(heures))


@given(parsers.parse(
    'un BI planifié le "{date_planifiee}" sans délai SLA existe'
))
def given_bi_no_sla(env, date_planifiee, context):
    site = context.get('site') or _make_site(env, code='SLA-SITE-002')
    context['bi'] = _make_bi(env, site, date_planifiee=date_planifiee, sla_delai_heures=0)


@given(parsers.parse('la date/heure courante est "{dt_str}"'))
def given_frozen_datetime(dt_str, context):
    context['frozen_dt'] = dt_str


@given(parsers.parse('le BI est à l\'état "{state}"'))
def given_bi_state(context, state):
    context['bi'].write({'state': state})


@then(parsers.parse('l\'échéance SLA du BI est "{expected_dt}"'))
def then_sla_echeance(context, expected_dt):
    bi = context['bi']
    from odoo.fields import Datetime
    actual = bi.sla_echeance
    assert actual, "Échéance SLA non calculée."
    actual_str = Datetime.to_string(actual)[:19]
    assert actual_str == expected_dt, f"Échéance attendue: {expected_dt}, obtenue: {actual_str}"


@then('l\'échéance SLA du BI est nulle')
def then_sla_echeance_null(context):
    bi = context['bi']
    assert not bi.sla_echeance, f"Échéance SLA devrait être nulle, obtenue: {bi.sla_echeance}"


@then(parsers.parse('le champ "sla_depasse" est False'))
def then_sla_not_exceeded(context):
    bi = context['bi']
    dt = context.get('frozen_dt')
    if dt:
        with freeze_time(dt):
            bi._compute_sla_depasse()
    assert bi.sla_depasse is False, f"sla_depasse devrait être False"


@then(parsers.parse('le champ "sla_depasse" est True'))
def then_sla_exceeded(context):
    bi = context['bi']
    dt = context.get('frozen_dt')
    if dt:
        with freeze_time(dt):
            bi._compute_sla_depasse()
    assert bi.sla_depasse is True, f"sla_depasse devrait être True"


@then(parsers.parse('la couleur SLA du BI est "{couleur}"'))
def then_sla_couleur(context, couleur):
    bi = context['bi']
    dt = context.get('frozen_dt')
    if dt:
        with freeze_time(dt):
            bi._compute_sla_couleur()
    expected = int(couleur)
    assert bi.sla_couleur == expected, (
        f"Couleur SLA attendue: {expected}, obtenue: {bi.sla_couleur}"
    )


@then(parsers.parse('les priorités disponibles incluent "{priority}"'))
def then_priority_available(env, priority):
    available = [p[0] for p in env['telecom.intervention']._fields['priority'].selection]
    assert priority in available, f"Priorité '{priority}' absente."
