# -*- coding: utf-8 -*-
"""
BDD step definitions — telecom_project
========================================
Feature files: tests/features/projet_structure.feature
               tests/features/pv_reception.feature

Run:
    pytest custom_addons/telecom_project/tests/ -v --tb=short
"""
import pytest
import base64
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError, UserError

pytestmark = pytest.mark.projet

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


# Minimal binary content for "signature" fields
_FAKE_SIGNATURE = base64.b64encode(b'fake-signature-data').decode()


def _make_site(env, name='Site Test', code='ST-001'):
    return env['telecom.site'].create({
        'name': name, 'code_interne': code, 'site_type': 'pylone_greenfield',
    })


def _make_project(env, name='Projet Test'):
    return env['project.project'].create({'name': name})


# ─────────────────────────────────────────────────────────────────────────────
# Background
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('un site physique "{name}" avec le code "{code}" existe'))
def given_physical_site(env, name, code, context):
    site = _make_site(env, name, code)
    context['physical_site'] = site


@given(parsers.parse('un projet "{name}" existe'))
def given_project(env, name, context):
    project = _make_project(env, name)
    context.setdefault('projects', {})[name] = project
    # Only set as primary project if none set yet (Background sets it first)
    if 'project' not in context:
        context['project'] = project


# ─────────────────────────────────────────────────────────────────────────────
# Given — lot setup
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('un projet "{name}" avec un lot "{code}" existe déjà'))
def given_project_with_lot(env, name, code, context):
    project = _make_project(env, name)
    env['telecom.lot'].create({'name': f'Lot {code}', 'code': code, 'project_id': project.id})
    context['project'] = project


@given(parsers.parse('un projet "{name}" avec un lot code "{code}" existe'))
def given_project_with_lot_code(env, name, code, context):
    project = _make_project(env, name)
    env['telecom.lot'].create({'name': f'Lot {code}', 'code': code, 'project_id': project.id})
    context.setdefault('projects', {})[name] = project


# ─────────────────────────────────────────────────────────────────────────────
# Given — project sites with states
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('un projet "{name}" avec un site à l\'état "{state}" existe'))
def given_project_with_site_in_state(env, name, state, context):
    project = _make_project(env, name)
    site = _make_site(env, f'Site {state}', f'S-{state[:3].upper()}')
    ps = env['telecom.project.site'].create({
        'project_id': project.id, 'site_id': site.id,
    })
    if state != 'prospection':
        ps.write({'state': state})
    context['project'] = project
    context['project_site'] = ps


@given(parsers.parse(
    'le site "{site_name}" est déjà rattaché à ce projet'
))
def given_site_already_in_project(env, site_name, context):
    project = context['project']
    site = env['telecom.site'].search([('name', '=', site_name)], limit=1)
    if not site:
        site = context.get('physical_site') or _make_site(env, site_name)
    env['telecom.project.site'].create({
        'project_id': project.id, 'site_id': site.id,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Given — lot advancement scenarios
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('un lot avec "{n}" sites tous à l\'état "{state}" existe'))
def given_lot_with_n_sites_in_state(env, n, state, context):
    project = _make_project(env, 'Projet Avancement')
    lot = env['telecom.lot'].create({
        'name': 'Lot Avancement', 'code': 'LA', 'project_id': project.id,
    })
    for i in range(int(n)):
        site = _make_site(env, f'Site Avancement {i}', f'SAV-{i:03d}')
        ps = env['telecom.project.site'].create({
            'project_id': project.id, 'lot_id': lot.id, 'site_id': site.id,
        })
        if state != 'prospection':
            ps.write({'state': state})
    lot.invalidate_recordset()
    context['lot'] = lot


@given(parsers.parse(
    'un lot avec "{n}" sites dont "{n_livre}" à l\'état "livre" et "{n_other}" à l\'état "{other_state}" existe'
))
def given_lot_with_mixed_sites(env, n, n_livre, n_other, other_state, context):
    project = _make_project(env, 'Projet Mix')
    lot = env['telecom.lot'].create({
        'name': 'Lot Mix', 'code': 'LM', 'project_id': project.id,
    })
    for i in range(int(n_livre)):
        site = _make_site(env, f'Site Livré {i}', f'SLV-{i:03d}')
        ps = env['telecom.project.site'].create({
            'project_id': project.id, 'lot_id': lot.id, 'site_id': site.id,
        })
        ps.write({'state': 'livre'})
    for i in range(int(n_other)):
        site = _make_site(env, f'Site Other {i}', f'SOT-{i:03d}')
        ps = env['telecom.project.site'].create({
            'project_id': project.id, 'lot_id': lot.id, 'site_id': site.id,
        })
        if other_state != 'prospection':
            ps.write({'state': other_state})
    lot.invalidate_recordset()
    context['lot'] = lot


@given(parsers.parse('un lot à l\'état "{state}" existe'))
def given_lot_in_state(env, state, context):
    project = _make_project(env, 'Projet Lot State')
    lot = env['telecom.lot'].create({
        'name': 'Lot Test State', 'code': 'LTS', 'project_id': project.id,
    })
    if state != 'en_cours':
        lot.write({'state': state})
    context['lot'] = lot


# ─────────────────────────────────────────────────────────────────────────────
# Given — PV setup (Background)
# ─────────────────────────────────────────────────────────────────────────────

@given('un site de projet à l\'état "recette" existe dans ce projet')
def given_project_site_recette(env, context):
    project = context.get('project')
    site = context.get('physical_site') or _make_site(env, 'Site Recette', 'SR-001')
    ps = env['telecom.project.site'].create({
        'project_id': project.id, 'site_id': site.id,
    })
    ps.write({'state': 'recette'})
    context['project_site'] = ps


# ─────────────────────────────────────────────────────────────────────────────
# Given — PV states
# ─────────────────────────────────────────────────────────────────────────────

@given('un PV en brouillon avec les deux signatures présentes existe')
def given_pv_draft_with_sigs(env, context):
    project = context.get('project')
    project_site = context.get('project_site')
    pv = env['telecom.pv.reception'].create({
        'pv_type': 'partiel',
        'project_id': project.id,
        'project_site_id': project_site.id if project_site else False,
        'date_pv': '2024-03-01',
        'travaux_realises': 'Installation antenne 4G',
        'signature_entreprise': _FAKE_SIGNATURE,
        'signature_client': _FAKE_SIGNATURE,
    })
    context['pv'] = pv


@given('un PV en brouillon sans signature entreprise existe')
def given_pv_no_company_sig(env, context):
    project = context.get('project')
    pv = env['telecom.pv.reception'].create({
        'pv_type': 'partiel',
        'project_id': project.id,
        'date_pv': '2024-03-01',
        'travaux_realises': 'Travaux test',
        'signature_client': _FAKE_SIGNATURE,
    })
    context['pv'] = pv


@given('un PV en brouillon sans signature client existe')
def given_pv_no_client_sig(env, context):
    project = context.get('project')
    pv = env['telecom.pv.reception'].create({
        'pv_type': 'partiel',
        'project_id': project.id,
        'date_pv': '2024-03-01',
        'travaux_realises': 'Travaux test',
        'signature_entreprise': _FAKE_SIGNATURE,
    })
    context['pv'] = pv


@given('un PV à l\'état "signe" existe')
def given_pv_signed(env, context):
    project = context.get('project')
    pv = env['telecom.pv.reception'].create({
        'pv_type': 'partiel',
        'project_id': project.id,
        'date_pv': '2024-03-01',
        'travaux_realises': 'Travaux test signés',
        'signature_entreprise': _FAKE_SIGNATURE,
        'signature_client': _FAKE_SIGNATURE,
    })
    pv.write({'state': 'signe', 'date_signature': '2024-03-01'})
    context['pv'] = pv


@given(parsers.parse(
    'un PV {pv_type} à l\'état "signe" lié à ce site de projet existe'
))
def given_pv_type_signed_linked(env, pv_type, context):
    project = context.get('project')
    project_site = context.get('project_site')
    pv_type_val = 'definitif' if 'définitif' in pv_type else 'partiel'
    pv = env['telecom.pv.reception'].create({
        'pv_type': pv_type_val,
        'project_id': project.id,
        'project_site_id': project_site.id,
        'date_pv': '2024-03-01',
        'travaux_realises': f'Travaux {pv_type}',
        'signature_entreprise': _FAKE_SIGNATURE,
        'signature_client': _FAKE_SIGNATURE,
    })
    pv.write({'state': 'signe', 'date_signature': '2024-03-01'})
    context['pv'] = pv


# ─────────────────────────────────────────────────────────────────────────────
# When — actions
# ─────────────────────────────────────────────────────────────────────────────

@when(parsers.parse('je crée un projet "{name}"'))
def when_create_project(env, name, context):
    project = _make_project(env, name)
    context['project'] = project
    context.setdefault('projects', {})[name] = project


@when(parsers.parse(
    'j\'ajoute un lot "{name}" avec le code "{code}" à ce projet'
))
def when_add_lot(env, name, code, context):
    project = context['project']
    context['lot'] = _catch(lambda: env['telecom.lot'].create({
        'name': name, 'code': code, 'project_id': project.id,
    }), context)


@when(parsers.parse(
    'je tente de créer un second lot avec le code "{code}" dans ce même projet'
))
def when_try_duplicate_lot(env, code, context):
    project = context['project']
    _catch(lambda: env['telecom.lot'].create({
        'name': f'Doublon Lot {code}', 'code': code, 'project_id': project.id,
    }), context)


@when(parsers.parse('j\'ajoute un lot avec le code "{code}" au projet "{project_name}"'))
def when_add_lot_to_project(env, code, project_name, context):
    project = context.get('projects', {}).get(project_name) or \
              env['project.project'].search([('name', '=', project_name)], limit=1)
    context['lot'] = _catch(lambda: env['telecom.lot'].create({
        'name': f'Lot {code}', 'code': code, 'project_id': project.id,
    }), context)


@when(parsers.parse('j\'ajoute le site "{site_name}" à ce projet'))
def when_add_site_to_project(env, site_name, context):
    project = context['project']
    site = env['telecom.site'].search([('name', '=', site_name)], limit=1) \
        or context.get('physical_site')
    context['project_site'] = _catch(lambda: env['telecom.project.site'].create({
        'project_id': project.id, 'site_id': site.id,
    }), context)


@when(parsers.parse(
    'je tente d\'ajouter à nouveau le site "{site_name}" à ce projet'
))
def when_try_duplicate_site(env, site_name, context):
    project = context['project']
    site = env['telecom.site'].search([('name', '=', site_name)], limit=1) \
        or context.get('physical_site')
    _catch(lambda: env['telecom.project.site'].create({
        'project_id': project.id, 'site_id': site.id,
    }), context)


@when(parsers.parse('je passe le site de projet à l\'état "{state}"'))
def when_project_site_state(context, state):
    ps = context['project_site']
    ps.write({'state': state})


@when('je marque le lot comme livré')
def when_lot_set_livre(context):
    context['lot'].action_set_livre()


@when('je suspends le lot')
def when_lot_set_suspendu(context):
    context['lot'].action_set_suspendu()


@when('je reprends le lot')
def when_lot_set_en_cours(context):
    context['lot'].action_set_en_cours()


@when('je crée un PV partiel pour ce site de projet')
def when_create_pv_partiel(env, context):
    project = context.get('project')
    project_site = context.get('project_site')
    context['pv'] = _catch(lambda: env['telecom.pv.reception'].create({
        'pv_type': 'partiel',
        'project_id': project.id,
        'project_site_id': project_site.id if project_site else False,
        'date_pv': '2024-03-01',
        'travaux_realises': 'Installation antenne 4G — test partiel',
    }), context)


@when('je crée un PV définitif pour ce site de projet')
def when_create_pv_definitif(env, context):
    project = context.get('project')
    project_site = context.get('project_site')
    context['pv'] = _catch(lambda: env['telecom.pv.reception'].create({
        'pv_type': 'definitif',
        'project_id': project.id,
        'project_site_id': project_site.id if project_site else False,
        'date_pv': '2024-03-01',
        'travaux_realises': 'Installation antenne 4G — réception définitive',
    }), context)


@when(parsers.parse(
    'je crée un PV définitif avec les deux signatures pour ce site de projet'
))
def when_create_pv_definitif_with_sigs(env, context):
    project = context.get('project')
    project_site = context.get('project_site')
    context['pv'] = _catch(lambda: env['telecom.pv.reception'].create({
        'pv_type': 'definitif',
        'project_id': project.id,
        'project_site_id': project_site.id if project_site else False,
        'date_pv': '2024-03-01',
        'travaux_realises': 'Déploiement complet 5G',
        'signature_entreprise': _FAKE_SIGNATURE,
        'signature_client': _FAKE_SIGNATURE,
    }), context)


@when('je signe le PV')
def when_sign_pv(context):
    _catch(lambda: context['pv'].action_signer(), context)


@when('je tente de signer le PV')
def when_try_sign_pv(context):
    _catch(lambda: context['pv'].action_signer(), context)


@when("j'approuve le PV")
def when_approve_pv(context):
    _catch(lambda: context['pv'].action_approuver(), context)


@when("j'approuve le PV directement sans signer")
def when_try_approve_without_sign(context):
    _catch(lambda: context['pv'].action_approuver(), context)


# ─────────────────────────────────────────────────────────────────────────────
# Then — lot assertions
# ─────────────────────────────────────────────────────────────────────────────

@then('le lot est créé avec succès')
def then_lot_created(context):
    assert context.get('error') is None, f"Erreur: {context.get('error')}"
    assert context.get('lot')


@then('le lot appartient au projet')
def then_lot_belongs_project(context):
    lot = context['lot']
    project = context['project']
    assert lot.project_id.id == project.id, "Le lot n'appartient pas au bon projet"


@then(parsers.parse('l\'état du lot est "{state}"'))
def then_lot_state(context, state):
    lot = context['lot']
    assert lot.state == state, f"État lot attendu '{state}', obtenu '{lot.state}'"


@then(parsers.parse('le taux d\'avancement du lot est "{taux}" %'))
def then_lot_advancement(context, taux):
    lot = context['lot']
    lot.invalidate_recordset()
    expected = float(taux)
    assert abs(lot.taux_avancement - expected) < 0.01, (
        f"Taux avancement attendu: {taux}%, obtenu: {lot.taux_avancement}%"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Then — project site assertions
# ─────────────────────────────────────────────────────────────────────────────

@then('le site de projet est créé avec succès')
def then_project_site_created(context):
    assert context.get('error') is None, f"Erreur: {context.get('error')}"
    assert context.get('project_site')


@then(parsers.parse('l\'état du site de projet est "{state}"'))
def then_project_site_state(context, state):
    ps = context['project_site']
    assert ps.state == state, f"État site projet attendu '{state}', obtenu '{ps.state}'"


@then(parsers.parse('l\'état du site de projet n\'est pas "{state}"'))
def then_project_site_state_not(context, state):
    ps = context['project_site']
    assert ps.state != state, f"L'état du site de projet est '{state}' alors qu'il ne devrait pas l'être"


# ─────────────────────────────────────────────────────────────────────────────
# Then — PV assertions
# ─────────────────────────────────────────────────────────────────────────────

@then('le PV est créé avec succès')
def then_pv_created(context):
    assert context.get('error') is None, f"Erreur: {context.get('error')}"
    assert context.get('pv')


@then('le numéro de PV est généré automatiquement')
def then_pv_number_generated(context):
    pv = context['pv']
    assert pv.sequence_number and pv.sequence_number != 'PV/NEW', (
        f"Numéro PV non généré: '{pv.sequence_number}'"
    )


@then(parsers.parse('l\'état du PV est "{state}"'))
def then_pv_state(context, state):
    pv = context['pv']
    assert pv.state == state, f"État PV attendu '{state}', obtenu '{pv.state}'"


@then('la date de signature est renseignée')
def then_pv_signature_date(context):
    pv = context['pv']
    assert pv.date_signature, "Date de signature non renseignée"


@then('une erreur de signature est levée')
def then_signature_error(context):
    assert context.get('error') is not None, "Aucune erreur levée — signature manquante non détectée"


@then('une erreur de workflow PV est levée')
def then_pv_workflow_error(context):
    assert context.get('error') is not None, "Aucune erreur levée alors qu'attendue"


@then('la date de livraison réelle est renseignée')
def then_delivery_date_set(context):
    ps = context['project_site']
    ps.invalidate_recordset()
    assert ps.date_livraison_reel, "Date de livraison réelle non renseignée"
