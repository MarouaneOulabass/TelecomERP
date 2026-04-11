# -*- coding: utf-8 -*-
"""
BDD step definitions — telecom_reporting
==========================================
Feature files: tests/features/kpi_operations.feature
               tests/features/kpi_commercial.feature

Strategy: rather than testing SQL views directly (they require full Odoo
install + real PostgreSQL), these tests verify KPI coherence by querying
the *source* models (telecom.intervention, telecom.site, telecom.ao,
telecom.contract) and comparing with what the view should return.

This approach:
- Works in unit test mode without a running PostgreSQL view
- Provides genuine business rule coverage (counts, rates, alerts)
- Detects regressions in underlying model data/logic

For integration environments (real DB with views installed), the view
models can be queried directly with env['report.telecom.intervention.analysis'].

Run:
    pytest custom_addons/telecom_reporting/tests/ -v --tb=short
"""
import pytest
from datetime import date
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError, UserError
from freezegun import freeze_time

pytestmark = pytest.mark.reporting

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


def _make_site(env, name, code, wilaya='casablanca_settat', site_type='pylone_greenfield'):
    return env['telecom.site'].create({
        'name': name, 'code_interne': code,
        'site_type': site_type, 'wilaya': wilaya,
    })


def _make_intervention(env, site, state='termine', sla_depasse=False, duree=0.0, date_pl=None):
    from datetime import timedelta
    # To make sla_depasse=True, set the SLA echéance in the past
    # To make sla_depasse=False, set it far in the future or state to 'valide'
    planned = date_pl or date.today().isoformat()
    vals = {
        'site_id': site.id,
        'intervention_type': 'corrective',
        'date_planifiee': planned,
    }
    if sla_depasse:
        # Set a very short SLA that's already expired
        vals['sla_delai_heures'] = 1
        # Use a past date so echéance is in the past
        vals['date_planifiee'] = '2020-01-01 08:00:00'
    int_ = env['telecom.intervention'].create(vals)
    write_vals = {}
    if duree:
        write_vals['duree_reelle'] = duree
    if state != 'draft':
        write_vals['state'] = state
    if write_vals:
        int_.write(write_vals)
    # For sla_depasse to be True, the state must be active (en_cours/planifie)
    if sla_depasse:
        int_.write({'state': 'en_cours'})
        int_._compute_sla_depasse()
    return int_


def _make_ao(env, state='detecte'):
    mo = env['res.partner'].create({'name': 'MO Reporting', 'partner_type': 'public_org'})
    ao = env['telecom.ao'].create({'name': f'AO {state}', 'maitre_ouvrage_id': mo.id})
    if state != 'detecte':
        ao.write({'state': state})
    return ao


def _make_contract(env, contract_type='maintenance', state='actif', montant=0.0, date_fin=None):
    partner = env['res.partner'].create({'name': 'Partenaire KPI', 'partner_type': 'operator'})
    vals = {
        'name': f'Contrat {contract_type}',
        'contract_type': contract_type,
        'partenaire_id': partner.id,
        'date_debut': date.today().isoformat(),
        'montant_total': montant,
    }
    if date_fin:
        vals['date_fin'] = date_fin
    c = env['telecom.contract'].create(vals)
    if state != 'brouillon':
        c.write({'state': state})
    return c


# ─────────────────────────────────────────────────────────────────────────────
# Background
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse(
    'un site "{name}" avec le code "{code}" dans la wilaya "{wilaya}" existe'
))
def given_kpi_site(env, name, code, wilaya, context):
    site = _make_site(env, name, code, wilaya)
    context.setdefault('sites', {})[code] = site
    context['site'] = site


# ─────────────────────────────────────────────────────────────────────────────
# Given — intervention setup for KPI tests
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('"{n}" interventions terminées existent sur le site "{code}"'))
def given_n_interventions_on_site(env, n, code, context):
    site = context.get('sites', {}).get(code) or context.get('site')
    interventions = []
    for i in range(int(n)):
        interventions.append(_make_intervention(env, site, state='termine'))
    context.setdefault('interventions_by_site', {})[code] = interventions


@given(parsers.parse(
    '"{n_termine}" interventions terminées et "{n_annule}" annulée existent sur le site "{code}"'
))
def given_terminated_and_cancelled(env, n_termine, n_annule, code, context):
    site = context.get('sites', {}).get(code) or context.get('site')
    active_ints = []
    for i in range(int(n_termine)):
        active_ints.append(_make_intervention(env, site, state='termine'))
    for i in range(int(n_annule)):
        _make_intervention(env, site, state='annule')
    context.setdefault('interventions_by_site', {})[code] = active_ints


@given(parsers.parse(
    '"{n}" interventions dont "{n_sla}" avec SLA dépassé existent sur le site "{code}"'
))
def given_interventions_with_sla(env, n, n_sla, code, context):
    site = context.get('sites', {}).get(code) or context.get('site')
    ints = []
    for i in range(int(n_sla)):
        ints.append(_make_intervention(env, site, state='termine', sla_depasse=True))
    for i in range(int(n) - int(n_sla)):
        ints.append(_make_intervention(env, site, state='termine', sla_depasse=False))
    context.setdefault('interventions_by_site', {})[code] = ints
    context['n_sla_depasse'] = int(n_sla)


@given(parsers.parse(
    'une intervention avec "{duree}" heures de durée réelle existe sur le site "{code}"'
))
def given_intervention_with_duration(env, duree, code, context):
    site = context.get('sites', {}).get(code) or context.get('site')
    int_ = _make_intervention(env, site, state='termine', duree=float(duree))
    context['target_intervention'] = int_
    context['expected_duree'] = float(duree)


@given(parsers.parse('"{n}" interventions existent sur le site "{code}"'))
def given_n_interventions_generic(env, n, code, context):
    site = context.get('sites', {}).get(code)
    if not site:
        site = _make_site(env, f'Site {code}', code)
        context.setdefault('sites', {})[code] = site
    for i in range(int(n)):
        _make_intervention(env, site, state='termine')


@given(parsers.parse('le site "{code}" n\'a aucune intervention'))
def given_site_no_intervention(env, code, context):
    # Just ensure the site exists with no interventions
    site = context.get('sites', {}).get(code)
    assert site, f"Site {code} non trouvé dans le contexte"


@given(parsers.parse('un second site "{name}" avec le code "{code}" existe'))
def given_second_site(env, name, code, context):
    site = _make_site(env, name, code)
    context.setdefault('sites', {})[code] = site


# ─────────────────────────────────────────────────────────────────────────────
# Given — AO pipeline
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('"{n}" AO à l\'état "{state}" existent'))
def given_n_ao_in_state(env, n, state, context):
    # Snapshot count before creating test data
    if 'ao_baseline' not in context:
        context['ao_baseline'] = {}
        for s in ['detecte', 'etude', 'soumis', 'gagne', 'perdu', 'abandonne', 'projet']:
            context['ao_baseline'][s] = env['telecom.ao'].search_count([('state', '=', s)])
    for i in range(int(n)):
        _make_ao(env, state)
    context.setdefault('ao_counts', {})[state] = \
        context.get('ao_counts', {}).get(state, 0) + int(n)


@given(parsers.parse('"{n}" AO à l\'état "{state}" existe'))
def given_1_ao_in_state(env, n, state, context):
    if 'ao_baseline' not in context:
        context['ao_baseline'] = {}
        for s in ['detecte', 'etude', 'soumis', 'gagne', 'perdu', 'abandonne', 'projet']:
            context['ao_baseline'][s] = env['telecom.ao'].search_count([('state', '=', s)])
    for i in range(int(n)):
        _make_ao(env, state)
    context.setdefault('ao_counts', {})[state] = \
        context.get('ao_counts', {}).get(state, 0) + int(n)


# ─────────────────────────────────────────────────────────────────────────────
# Given — contracts
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('"{n}" contrat actif de type "{ctype}" existe'))
def given_1_active_contract(env, n, ctype, context):
    if 'contract_baseline' not in context:
        context['contract_baseline'] = env['telecom.contract'].search_count([('state', '=', 'actif')])
    for i in range(int(n)):
        _make_contract(env, contract_type=ctype, state='actif')


@given(parsers.parse('"{n}" contrats actifs de type "{ctype}" existent'))
def given_n_active_contracts(env, n, ctype, context):
    if 'contract_baseline' not in context:
        context['contract_baseline'] = env['telecom.contract'].search_count([('state', '=', 'actif')])
    for i in range(int(n)):
        _make_contract(env, contract_type=ctype, state='actif')


@given(parsers.parse('"{n}" contrat de type "{ctype}" à l\'état "{state}" existe'))
def given_n_contracts_in_state(env, n, ctype, state, context):
    if 'contract_baseline' not in context:
        context['contract_baseline'] = env['telecom.contract'].search_count([('state', '=', 'actif')])
    for i in range(int(n)):
        _make_contract(env, contract_type=ctype, state=state)


@given(parsers.parse(
    'un contrat actif de type "{ctype}" avec un montant de "{montant}" MAD existe'
))
def given_contract_with_amount(env, ctype, montant, context):
    _make_contract(env, contract_type=ctype, state='actif', montant=float(montant))


@given(parsers.parse('un contrat actif avec date de fin "{date_fin}" existe'))
def given_active_contract_with_end_reporting(env, date_fin, context):
    _make_contract(env, state='actif', date_fin=date_fin)


@given('un contrat actif sans date de fin existe')
def given_active_contract_no_end_reporting(env, context):
    _make_contract(env, state='actif')


# ─────────────────────────────────────────────────────────────────────────────
# Then — intervention analysis assertions
# ─────────────────────────────────────────────────────────────────────────────

@then(parsers.parse(
    'la vue d\'analyse interventions retourne "{n}" lignes pour le site "{code}"'
))
def then_intervention_analysis_count(env, n, code, context):
    site = context.get('sites', {}).get(code) or context.get('site')
    # Query source model as proxy for view coherence
    count = env['telecom.intervention'].search_count([
        ('site_id', '=', site.id),
        ('active', '=', True),
        ('state', '!=', 'annule'),
    ])
    assert count == int(n), (
        f"Vue analyse interventions: attendu {n} lignes pour {code}, obtenu {count}"
    )


@then(parsers.parse(
    'la vue d\'analyse retourne "{n}" SLA dépassé pour le site "{code}"'
))
def then_sla_count_in_view(env, n, code, context):
    site = context.get('sites', {}).get(code) or context.get('site')
    count = env['telecom.intervention'].search_count([
        ('site_id', '=', site.id),
        ('active', '=', True),
        ('sla_depasse', '=', True),
    ])
    assert count == int(n), (
        f"SLA dépassés attendus: {n}, obtenus: {count}"
    )


@then(parsers.parse(
    'la vue d\'analyse expose une durée de "{duree}" heures pour cette intervention'
))
def then_intervention_duration(env, duree, context):
    int_ = context.get('target_intervention')
    assert int_, "Intervention cible non trouvée dans le contexte"
    assert abs(int_.duree_reelle - float(duree)) < 0.01, (
        f"Durée réelle attendue: {duree}h, obtenue: {int_.duree_reelle}h"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Then — site analysis assertions
# ─────────────────────────────────────────────────────────────────────────────

@then(parsers.parse(
    'la vue d\'analyse sites indique "{n}" interventions totales pour "{code}"'
))
def then_site_analysis_intervention_count(env, n, code, context):
    site = context.get('sites', {}).get(code)
    assert site, f"Site {code} non trouvé dans le contexte"
    count = env['telecom.intervention'].search_count([
        ('site_id', '=', site.id),
        ('active', '=', True),
    ])
    assert count == int(n), (
        f"Vue analyse sites {code}: attendu {n} interventions, obtenu {count}"
    )


@then(parsers.parse('la vue d\'analyse sites expose le type du site "{code}"'))
def then_site_analysis_type(env, code, context):
    site = context.get('sites', {}).get(code) or context.get('site')
    assert site.site_type, f"Type de site non renseigné pour {code}"


@then(parsers.parse(
    'la vue d\'analyse sites expose la wilaya "{wilaya}" pour "{code}"'
))
def then_site_analysis_wilaya(env, wilaya, code, context):
    site = context.get('sites', {}).get(code) or context.get('site')
    assert site.wilaya == wilaya, (
        f"Wilaya attendue: '{wilaya}', obtenue: '{site.wilaya}'"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Then — AO commercial KPIs
# ─────────────────────────────────────────────────────────────────────────────

@then(parsers.parse('le nombre d\'AO détectés est "{n}"'))
def then_ao_detectes(env, n, context):
    baseline = context.get('ao_baseline', {}).get('detecte', 0)
    count = env['telecom.ao'].search_count([('state', '=', 'detecte')]) - baseline
    assert count == int(n), f"AO détectés attendus: {n}, obtenus: {count} (base: {baseline})"


@then(parsers.parse('le nombre d\'AO soumis est "{n}"'))
def then_ao_soumis(env, n, context):
    baseline = context.get('ao_baseline', {}).get('soumis', 0)
    count = env['telecom.ao'].search_count([('state', '=', 'soumis')]) - baseline
    assert count == int(n), f"AO soumis attendus: {n}, obtenus: {count}"


@then(parsers.parse('le nombre d\'AO gagnés est "{n}"'))
def then_ao_gagnes(env, n, context):
    baseline = context.get('ao_baseline', {}).get('gagne', 0)
    count = env['telecom.ao'].search_count([('state', '=', 'gagne')]) - baseline
    assert count == int(n), f"AO gagnés attendus: {n}, obtenus: {count}"


@then(parsers.parse('le taux de succès AO est de "{pct}" %'))
def then_ao_success_rate(env, pct, context):
    baseline_g = context.get('ao_baseline', {}).get('gagne', 0)
    baseline_p = context.get('ao_baseline', {}).get('perdu', 0)
    gagnes = env['telecom.ao'].search_count([('state', '=', 'gagne')]) - baseline_g
    perdus = env['telecom.ao'].search_count([('state', '=', 'perdu')]) - baseline_p
    total = gagnes + perdus
    if total == 0:
        assert False, "Aucun AO gagné ou perdu pour calculer le taux de succès"
    taux = round(gagnes / total * 100)
    assert taux == int(pct), f"Taux de succès attendu: {pct}%, obtenu: {taux}%"


# ─────────────────────────────────────────────────────────────────────────────
# Then — contract KPIs
# ─────────────────────────────────────────────────────────────────────────────

@then(parsers.parse('le nombre de contrats actifs est "{n}"'))
def then_active_contracts_count(env, n, context):
    baseline = context.get('contract_baseline', 0)
    count = env['telecom.contract'].search_count([('state', '=', 'actif')]) - baseline
    assert count == int(n), f"Contrats actifs attendus: {n}, obtenus: {count} (base: {baseline})"


@then(parsers.parse(
    'le montant total des contrats actifs est d\'au moins "{montant}" MAD'
))
def then_total_contract_amount(env, montant, context):
    contracts = env['telecom.contract'].search([('state', '=', 'actif')])
    total = sum(contracts.mapped('montant_total'))
    assert total >= float(montant), (
        f"Montant total attendu ≥ {montant} MAD, obtenu: {total} MAD"
    )


@then(parsers.parse('le nombre de contrats avec alerte d\'expiration est "{n}"'))
def then_expiry_warning_count(env, n, context):
    mocked = context.get('mocked_today')
    if mocked:
        with freeze_time(mocked):
            contracts = env['telecom.contract'].search([('state', '=', 'actif')])
            for c in contracts:
                c._compute_expiry_warning()
    else:
        contracts = env['telecom.contract'].search([('state', '=', 'actif')])
    count = len(contracts.filtered(lambda c: c.expiry_warning))
    assert count == int(n), (
        f"Contrats avec alerte expiration attendus: {n}, obtenus: {count}"
    )
