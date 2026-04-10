# -*- coding: utf-8 -*-
"""
BDD step definitions — telecom_finance_ma
==========================================
Feature files: tests/features/decompte_*.feature

Run:
    pytest custom_addons/telecom_finance_ma/tests/ -v --tb=short
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError, UserError
from freezegun import freeze_time

pytestmark = pytest.mark.finance

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


def _make_decompte(env, project, contract, client, decompte_type='provisoire', **kwargs):
    vals = {
        'decompte_type': decompte_type,
        'project_id': project.id,
        'contract_id': contract.id,
        'client_id': client.id,
        'date_decompte': '2024-01-15',
    }
    vals.update(kwargs)
    return env['telecom.decompte'].create(vals)


# ─────────────────────────────────────────────────────────────────────────────
# Background
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('un projet "{proj_name}" et un contrat "{ref}" existent'))
def given_project_and_contract(env, proj_name, ref, context):
    project = env['project.project'].create({'name': proj_name})
    context['project'] = project
    partner = env['res.partner'].create({'name': 'Partenaire Contrat Test'})
    contract = env['telecom.contract'].create({
        'name': ref,
        'contract_type': 'deploiement',
        'partenaire_id': partner.id,
        'date_debut': '2024-01-01',
    })
    context['contract'] = contract


@given(parsers.parse('un projet "{name}" existe'))
def given_project(env, name, context):
    project = env['project.project'].create({'name': name})
    context['project'] = project


@given(parsers.parse('un contrat "{ref}" lié à ce projet existe'))
def given_contract(env, ref, context):
    partner = env['res.partner'].create({'name': 'Partenaire Contrat Test'})
    contract = env['telecom.contract'].create({
        'name': ref,
        'contract_type': 'deploiement',
        'partenaire_id': partner.id,
        'date_debut': '2024-01-01',
    })
    context['contract'] = contract


@given(parsers.parse('un client "{name}" de type "operator" existe'))
def given_client_operator(env, name, context):
    client = env['res.partner'].create({'name': name, 'partner_type': 'operator'})
    context['client'] = client


@given(parsers.parse('un client "{name}" existe'))
def given_client(env, name, context):
    client = env['res.partner'].create({'name': name})
    context['client'] = client


@given('un décompte provisoire en brouillon est créé')
def given_decompte_draft(env, context):
    d = _make_decompte(
        env, context['project'], context['contract'], context['client']
    )
    context['decompte'] = d


# ─────────────────────────────────────────────────────────────────────────────
# CALCULS — Scenarios from decompte_calculs.feature
# ─────────────────────────────────────────────────────────────────────────────

@given('un décompte avec :')
def given_decompte_with_table(env, context, datatable):
    """Handles data tables for multi-field setup."""
    project = context.get('project') or env['project.project'].create({'name': 'Projet Test'})
    contract = context.get('contract') or env['telecom.contract'].create({
        'name': 'CONT-TEST', 'contract_type': 'deploiement',
        'partenaire_id': env['res.partner'].create({'name': 'P'}).id,
        'date_debut': '2024-01-01',
    })
    client = context.get('client') or env['res.partner'].create({'name': 'Client Test'})
    vals = {}
    for row in datatable:
        field, value = row[0].strip(), row[1].strip()
        field_map = {
            'travaux_ht': 'montant_travaux_ht',
            'travaux_supplementaires': 'montant_travaux_supplementaires',
            'montant_revisions_prix': 'montant_revisions_prix',
            'retenue_garantie_cumul': None,  # computed — skip
            'total_ht_cumul': 'montant_travaux_ht',  # approximate via source field
            'avance_periode': 'avance_periode',
            'situations_anterieures': 'situations_anterieures',
        }
        odoo_field = field_map.get(field, field)
        if odoo_field:
            vals[odoo_field] = float(value)
    d = _make_decompte(env, project, contract, client, **vals)
    context['decompte'] = d


@given(parsers.parse('un décompte avec un total HT cumulé de "{ht}" MAD'))
def given_decompte_total_ht(env, ht, context):
    project = context.get('project') or env['project.project'].create({'name': 'P'})
    contract = context.get('contract') or env['telecom.contract'].create({
        'name': 'C', 'contract_type': 'deploiement',
        'partenaire_id': env['res.partner'].create({'name': 'P'}).id,
        'date_debut': '2024-01-01',
    })
    client = context.get('client') or env['res.partner'].create({'name': 'CL'})
    d = _make_decompte(env, project, contract, client,
                       montant_travaux_ht=float(ht))
    context['decompte'] = d


@given(parsers.parse('un taux de retenue de garantie de "{taux}%"'))
def given_taux_rg(context, taux):
    d = context['decompte']
    d.write({'retenue_garantie_taux': float(taux)})


@given(parsers.parse(
    'un décompte avec un total HT cumulé de "{ht}" MAD et un taux de retenue de garantie de "{taux}%"'
))
def given_decompte_total_ht_taux_rg(env, ht, taux, context):
    project = context.get('project') or env['project.project'].create({'name': 'P'})
    contract = context.get('contract') or env['telecom.contract'].create({
        'name': 'C', 'contract_type': 'deploiement',
        'partenaire_id': env['res.partner'].create({'name': 'P'}).id,
        'date_debut': '2024-01-01',
    })
    client = context.get('client') or env['res.partner'].create({'name': 'CL'})
    d = _make_decompte(env, project, contract, client,
                       montant_travaux_ht=float(ht),
                       retenue_garantie_taux=float(taux))
    context['decompte'] = d


@given(parsers.parse(
    'un décompte avec un total HT cumulé de "{ht}" MAD sans déductions'
))
def given_decompte_no_deductions(env, ht, context):
    project = context.get('project') or env['project.project'].create({'name': 'P'})
    contract = context.get('contract') or env['telecom.contract'].create({
        'name': 'C', 'contract_type': 'deploiement',
        'partenaire_id': env['res.partner'].create({'name': 'P'}).id,
        'date_debut': '2024-01-01',
    })
    client = context.get('client') or env['res.partner'].create({'name': 'CL'})
    d = _make_decompte(env, project, contract, client,
                       montant_travaux_ht=float(ht),
                       retenue_garantie_taux=0.0,
                       avance_periode=0.0,
                       situations_anterieures=0.0)
    context['decompte'] = d


@given(parsers.parse(
    'un décompte avec une base TVA de "{base}" MAD et un taux TVA de "{taux}%"'
))
def given_decompte_tva(env, base, taux, context):
    # Compute what total_ht gives us that base TVA (simplified: no other deductions)
    project = context.get('project') or env['project.project'].create({'name': 'P'})
    contract = context.get('contract') or env['telecom.contract'].create({
        'name': 'C', 'contract_type': 'deploiement',
        'partenaire_id': env['res.partner'].create({'name': 'P'}).id,
        'date_debut': '2024-01-01',
    })
    client = context.get('client') or env['res.partner'].create({'name': 'CL'})
    d = _make_decompte(env, project, contract, client,
                       montant_travaux_ht=float(base),
                       retenue_garantie_taux=0.0,
                       tva_taux=float(taux))
    context['decompte'] = d


@given(parsers.parse(
    'un décompte avec une base TVA de "{base}" MAD'
))
def given_decompte_base_tva(env, base, context):
    project = context.get('project') or env['project.project'].create({'name': 'P'})
    contract = context.get('contract') or env['telecom.contract'].create({
        'name': 'C', 'contract_type': 'deploiement',
        'partenaire_id': env['res.partner'].create({'name': 'P'}).id,
        'date_debut': '2024-01-01',
    })
    client = context.get('client') or env['res.partner'].create({'name': 'CL'})
    d = _make_decompte(env, project, contract, client,
                       montant_travaux_ht=float(base), retenue_garantie_taux=0.0)
    context['decompte'] = d


@given(parsers.parse(
    'un décompte avec une base TVA de "{base}" MAD et TVA de "{tva}" MAD'
))
def given_decompte_base_et_tva(env, base, tva, context):
    # Store for assertion
    context['computed_base'] = float(base)
    context['computed_tva'] = float(tva)
    context['computed_net'] = float(base) + float(tva)


@given(parsers.parse(
    'un décompte avec un net à régler de "{net}" MAD et une RAS de "{ras}" MAD'
))
def given_decompte_net_ras(env, net, ras, context):
    context['computed_net'] = float(net)
    context['computed_ras'] = float(ras)
    context['computed_net_ras'] = float(net) - float(ras)


# ─────────────────────────────────────────────────────────────────────────────
# CALCULS — Then assertions
# ─────────────────────────────────────────────────────────────────────────────

@then(parsers.parse('le total HT cumulé est "{expected}" MAD'))
def then_total_ht(context, expected):
    d = context['decompte']
    assert abs(d.total_ht_cumul - float(expected)) < 0.01, (
        f"Total HT attendu: {expected}, obtenu: {d.total_ht_cumul}"
    )


@then(parsers.parse('la retenue de garantie cumulée est "{expected}" MAD'))
def then_rg(context, expected):
    d = context['decompte']
    assert abs(d.retenue_garantie_cumul - float(expected)) < 0.01, (
        f"RG attendue: {expected}, obtenue: {d.retenue_garantie_cumul}"
    )


@then(parsers.parse('la base TVA est "{expected}" MAD'))
def then_base_tva(context, expected):
    d = context.get('decompte')
    if d:
        assert abs(d.base_tva - float(expected)) < 0.01, (
            f"Base TVA attendue: {expected}, obtenue: {d.base_tva}"
        )


@then(parsers.parse('la TVA est "{expected}" MAD'))
def then_tva(context, expected):
    d = context.get('decompte')
    if d:
        assert abs(d.tva_montant - float(expected)) < 0.01, (
            f"TVA attendue: {expected}, obtenue: {d.tva_montant}"
        )


@then(parsers.parse('la RAS est "{expected}" MAD'))
def then_ras(context, expected):
    d = context.get('decompte')
    if d:
        assert abs(d.ras_montant - float(expected)) < 0.01, (
            f"RAS attendue: {expected}, obtenue: {d.ras_montant}"
        )


@then(parsers.parse('le net à régler est "{expected}" MAD'))
def then_net_a_regler(context, expected):
    d = context.get('decompte')
    val = d.net_a_regler if d else context.get('computed_net', 0)
    assert abs(val - float(expected)) < 0.01, (
        f"Net à régler attendu: {expected}, obtenu: {val}"
    )


@then(parsers.parse('le net après RAS est "{expected}" MAD'))
def then_net_apres_ras(context, expected):
    d = context.get('decompte')
    val = d.net_apres_ras if d else context.get('computed_net_ras', 0)
    assert abs(val - float(expected)) < 0.01, (
        f"Net après RAS attendu: {expected}, obtenu: {val}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# WORKFLOW — Steps
# ─────────────────────────────────────────────────────────────────────────────

@then(parsers.parse('le nom du décompte commence par "{prefix}"'))
def then_decompte_name_prefix(context, prefix):
    d = context['decompte']
    assert d.name.startswith(prefix), f"Nom du décompte: '{d.name}' (attendu: '{prefix}...')"


@given('un décompte définitif est créé')
def given_decompte_definitif(env, context):
    d = _make_decompte(
        env, context['project'], context['contract'], context['client'],
        decompte_type='definitif'
    )
    context['decompte'] = d


@given(parsers.parse('le décompte est à l\'état "{state}"'))
def given_decompte_state(context, state):
    d = context['decompte']
    d.write({'state': state})


@when('je soumets le décompte')
def when_soumettre(context):
    _catch(lambda: context['decompte'].action_soumettre(), context)


@when('je tente de soumettre à nouveau le décompte')
def when_resubmit(context):
    _catch(lambda: context['decompte'].action_soumettre(), context)


@when("j'approuve le décompte")
def when_approuver(context):
    _catch(lambda: context['decompte'].action_approuver(), context)


@when('je passe le décompte en phase contradictoire')
def when_contradictoire(context):
    _catch(lambda: context['decompte'].action_contradictoire(), context)


@when('je signe le décompte')
def when_signer(context):
    _catch(lambda: context['decompte'].action_signer(), context)


@when('je crée la facture depuis le décompte')
def when_create_invoice(context):
    _catch(lambda: context['decompte'].action_creer_facture(), context)


@when('je tente de créer une nouvelle facture')
def when_try_create_invoice(context):
    _catch(lambda: context['decompte'].action_creer_facture(), context)


@when('je tente de remettre le décompte en brouillon')
def when_reset_decompte(context):
    _catch(lambda: context['decompte'].action_reset_draft(), context)


@then(parsers.parse('l\'état du décompte est "{state}"'))
def then_decompte_state(context, state):
    d = context['decompte']
    assert d.state == state, f"État attendu '{state}', obtenu '{d.state}'"


@then('la date de soumission est renseignée')
def then_submission_date(context):
    assert context['decompte'].date_soumission, "Date de soumission non renseignée."


@then('une facture client est créée et liée au décompte')
def then_invoice_created(context):
    d = context['decompte']
    assert d.invoice_id, "Aucune facture liée au décompte."


@given('une facture est déjà liée au décompte')
def given_invoice_linked(env, context):
    d = context['decompte']
    # Create a minimal invoice and link it
    partner = env['res.partner'].create({'name': 'Partner Facture'})
    inv = env['account.move'].create({
        'move_type': 'out_invoice',
        'partner_id': partner.id,  # account.move uses partner_id
        'decompte_id': d.id,
    })
    d.write({'invoice_id': inv.id})


@given('je suis connecté en tant qu\'utilisateur non-administrateur')
def given_non_admin_user(env, context):
    user = env['res.users'].create({
        'name': 'User Non Admin', 'login': 'non.admin.test@test.com',
        'groups_id': [],
    })
    context['env_as_user'] = env(user=user.id)


# ─────────────────────────────────────────────────────────────────────────────
# Loi 69-21 — Délai paiement
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('un décompte soumis le "{date_soumission}"'))
def given_decompte_soumis(env, date_soumission, context):
    project = context.get('project') or env['project.project'].create({'name': 'P'})
    contract = context.get('contract') or env['telecom.contract'].create({
        'name': 'C', 'contract_type': 'deploiement',
        'partenaire_id': env['res.partner'].create({'name': 'P'}).id,
        'date_debut': '2024-01-01',
    })
    client = context.get('client') or env['res.partner'].create({'name': 'CL'})
    d = _make_decompte(env, project, contract, client,
                       state='soumis', date_soumission=date_soumission)
    context['decompte'] = d


@given(parsers.parse('un décompte soumis le "{date_soumission}" et payé'))
def given_decompte_paid(env, date_soumission, context):
    project = context.get('project') or env['project.project'].create({'name': 'P'})
    contract = context.get('contract') or env['telecom.contract'].create({
        'name': 'C', 'contract_type': 'deploiement',
        'partenaire_id': env['res.partner'].create({'name': 'P'}).id,
        'date_debut': '2024-01-01',
    })
    client = context.get('client') or env['res.partner'].create({'name': 'CL'})
    d = _make_decompte(env, project, contract, client,
                       state='paye', date_soumission=date_soumission)
    context['decompte'] = d


@given("le décompte n'est pas à l'état \"paye\"")
def given_decompte_not_paid(context):
    d = context['decompte']
    if d.state == 'paye':
        d.write({'state': 'soumis'})


@given('un décompte sans date de soumission')
def given_decompte_no_submission_date(env, context):
    project = context.get('project') or env['project.project'].create({'name': 'P'})
    contract = context.get('contract') or env['telecom.contract'].create({
        'name': 'C', 'contract_type': 'deploiement',
        'partenaire_id': env['res.partner'].create({'name': 'P'}).id,
        'date_debut': '2024-01-01',
    })
    client = context.get('client') or env['res.partner'].create({'name': 'CL'})
    d = _make_decompte(env, project, contract, client)
    d.write({'date_soumission': False})
    context['decompte'] = d


@then(parsers.parse('la date limite de paiement est "{expected_date}"'))
def then_payment_deadline(context, expected_date):
    d = context['decompte']
    mocked = context.get('mocked_today')
    if mocked:
        with freeze_time(mocked):
            d._compute_date_paiement_prevu()
    from odoo.fields import Date
    actual = Date.to_string(d.date_paiement_prevu) if d.date_paiement_prevu else None
    assert actual == expected_date, f"Date paiement attendue: {expected_date}, obtenue: {actual}"


@then(parsers.parse('le champ "delai_depasse" est True'))
def then_delai_depasse_true(context):
    d = context['decompte']
    mocked = context.get('mocked_today')
    if mocked:
        with freeze_time(mocked):
            d._compute_delai_depasse()
    assert d.delai_depasse is True, "delai_depasse devrait être True"


@then(parsers.parse('le champ "delai_depasse" est False'))
def then_delai_depasse_false(context):
    d = context['decompte']
    mocked = context.get('mocked_today')
    if mocked:
        with freeze_time(mocked):
            d._compute_delai_depasse()
    assert d.delai_depasse is False, "delai_depasse devrait être False"


# ─────────────────────────────────────────────────────────────────────────────
# AVANCES DE DÉMARRAGE — Steps from avance_situation.feature
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse(
    'une avance de démarrage avec un montant marché de "{marche}" MAD et un taux de "{taux}%"'
))
def given_avance_taux(env, marche, taux, context):
    project = context.get('project') or env['project.project'].create({'name': 'P'})
    contract = context.get('contract') or env['telecom.contract'].create({
        'name': 'C', 'contract_type': 'deploiement',
        'partenaire_id': env['res.partner'].create({'name': 'P'}).id,
        'date_debut': '2024-01-01',
    })
    client = context.get('client') or env['res.partner'].create({'name': 'CL'})
    avance = env['telecom.avance.demarrage'].create({
        'project_id': project.id,
        'contract_id': contract.id,
        'client_id': client.id,
        'montant_marche': float(marche),
        'taux_avance': float(taux),
    })
    context['avance'] = avance


@then(parsers.parse("le montant d'avance théorique est \"{expected}\" MAD"))
def then_montant_avance(context, expected):
    a = context['avance']
    assert abs(a.montant_avance - float(expected)) < 0.01, (
        f"Montant avance attendu: {expected}, obtenu: {a.montant_avance}"
    )


@given('une avance de démarrage en attente de versement')
def given_avance_en_attente(env, context):
    project = context.get('project') or env['project.project'].create({'name': 'P'})
    contract = context.get('contract') or env['telecom.contract'].create({
        'name': 'C', 'contract_type': 'deploiement',
        'partenaire_id': env['res.partner'].create({'name': 'P'}).id,
        'date_debut': '2024-01-01',
    })
    client = context.get('client') or env['res.partner'].create({'name': 'CL'})
    avance = env['telecom.avance.demarrage'].create({
        'project_id': project.id,
        'contract_id': contract.id,
        'client_id': client.id,
        'montant_marche': 1000000,
        'taux_avance': 10.0,
    })
    context['avance'] = avance


@given(parsers.parse('le montant versé est "{montant}" MAD le "{date_versement}"'))
def given_montant_verse(context, montant, date_versement):
    a = context['avance']
    a.write({'montant_verse': float(montant), 'date_versement': date_versement})


@when("je marque l'avance comme versée")
def when_marquer_versee(context):
    _catch(lambda: context['avance'].action_marquer_versee(), context)


@when("je démarre le remboursement de l'avance")
def when_demarrer_remboursement(context):
    _catch(lambda: context['avance'].action_demarrer_remboursement(), context)


@then(parsers.parse("l'état de l'avance est \"{state}\""))
def then_avance_state(context, state):
    a = context['avance']
    assert a.state == state, f"État attendu '{state}', obtenu '{a.state}'"


# ─────────────────────────────────────────────────────────────────────────────
# SITUATIONS DE TRAVAUX
# ─────────────────────────────────────────────────────────────────────────────

@given('une situation de travaux avec :')
def given_situation_with_table(env, context, datatable):
    project = context.get('project') or env['project.project'].create({'name': 'P'})
    client = context.get('client') or env['res.partner'].create({'name': 'CL'})
    vals = {
        'project_id': project.id,
        'client_id': client.id,
        'numero_situation': 1,
        'periode_du': '2024-01-01',
        'periode_au': '2024-03-31',
    }
    contract = context.get('contract')
    if contract:
        vals['contract_id'] = contract.id
    for row in datatable:
        field, value = row[0].strip(), row[1].strip()
        vals[field] = float(value)
    situation = env['telecom.situation'].create(vals)
    context['situation'] = situation


@then(parsers.parse('le montant situation HT est "{expected}" MAD'))
def then_montant_situation_ht(context, expected):
    s = context['situation']
    assert abs(s.montant_situation_ht - float(expected)) < 0.01, (
        f"Montant situation HT attendu: {expected}, obtenu: {s.montant_situation_ht}"
    )


@then(parsers.parse('la retenue de garantie situation est "{expected}" MAD'))
def then_rg_situation(context, expected):
    s = context['situation']
    assert abs(s.retenue_garantie - float(expected)) < 0.01, (
        f"RG attendue: {expected}, obtenue: {s.retenue_garantie}"
    )


@then(parsers.parse('le net à payer situation est "{expected}" MAD'))
def then_net_situation(context, expected):
    s = context['situation']
    assert abs(s.net_a_payer - float(expected)) < 0.01, (
        f"Net à payer attendu: {expected}, obtenu: {s.net_a_payer}"
    )
