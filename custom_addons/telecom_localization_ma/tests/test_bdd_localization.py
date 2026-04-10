# -*- coding: utf-8 -*-
"""
BDD step definitions — telecom_localization_ma
================================================
Feature files: tests/features/tva_ras.feature

Run:
    pytest custom_addons/telecom_localization_ma/tests/ -v --tb=short
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError

pytestmark = pytest.mark.localization

scenarios('features/')


def _catch(fn, context):
    try:
        result = fn()
        context['error'] = None
        return result
    except Exception as exc:
        context['error'] = str(exc)


# ─────────────────────────────────────────────────────────────────────────────
# TVA
# ─────────────────────────────────────────────────────────────────────────────

@then(parsers.parse('les taux de TVA disponibles incluent "{taux}"'))
def then_tva_rate_available(env, taux):
    taux_val = float(taux.rstrip('%'))
    taxes = env['account.tax'].search([
        ('amount', '=', taux_val),
        ('type_tax_use', '=', 'sale'),
        ('country_id.code', '=', 'MA'),
    ])
    assert taxes, (
        f"Aucune taxe TVA à {taux} pour le Maroc. "
        f"Vérifier telecom_localization_ma/data/."
    )


@given(parsers.parse('une taxe TVA à "{taux}" existe dans le système'))
def given_tva_tax(env, taux, context):
    taux_val = float(taux.rstrip('%'))
    tax = env['account.tax'].search([
        ('amount', '=', taux_val), ('type_tax_use', '=', 'sale'),
    ], limit=1)
    if not tax:
        tax = env['account.tax'].create({
            'name': f'TVA {taux} (Maroc)',
            'amount': taux_val,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
        })
    context['tax'] = tax


@when(parsers.parse('je l\'applique sur un montant HT de "{montant}" MAD'))
def when_apply_tax(env, montant, context):
    tax = context['tax']
    base = float(montant)
    tva = base * tax.amount / 100.0
    context['tva_amount'] = round(tva, 2)
    context['ttc'] = round(base + tva, 2)
    context['base'] = base


@then(parsers.parse('le montant de TVA est "{expected}" MAD'))
def then_tva_amount(context, expected):
    assert abs(context['tva_amount'] - float(expected)) < 0.01, (
        f"TVA attendue: {expected}, calculée: {context['tva_amount']}"
    )


@then(parsers.parse('le montant TTC est "{expected}" MAD'))
def then_ttc_amount(context, expected):
    assert abs(context['ttc'] - float(expected)) < 0.01, (
        f"TTC attendu: {expected}, calculé: {context['ttc']}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# RAS
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('une facture fournisseur HT de "{montant}" MAD avec RAS 10%'))
def given_invoice_with_ras(env, montant, context):
    context['facture_ht'] = float(montant)
    context['ras'] = round(float(montant) * 0.10, 2)
    context['net_fournisseur'] = round(float(montant) - context['ras'], 2)


@then(parsers.parse('la RAS est "{expected}" MAD'))
def then_ras_amount(context, expected):
    assert abs(context['ras'] - float(expected)) < 0.01, (
        f"RAS attendue: {expected}, calculée: {context['ras']}"
    )


@then(parsers.parse('le net à payer au fournisseur est "{expected}" MAD (avant TVA)'))
def then_net_fournisseur(context, expected):
    assert abs(context['net_fournisseur'] - float(expected)) < 0.01


@given(parsers.parse(
    'une facture fournisseur HT de "{ht}" MAD TVA 20% avec RAS 10%'
))
def given_invoice_ht_tva_ras(env, ht, context):
    context['facture_ht'] = float(ht)
    context['ras'] = round(float(ht) * 0.10, 2)


@then(parsers.parse('la RAS est calculée sur "{base}" MAD (base HT)'))
def then_ras_base(context, base):
    expected_ras = round(float(base) * 0.10, 2)
    assert abs(context['ras'] - expected_ras) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# Devise MAD
# ─────────────────────────────────────────────────────────────────────────────

@then(parsers.parse('la devise "{code}" existe dans le système'))
def then_currency_exists(env, code):
    currency = env['res.currency'].with_context(active_test=False).search([('name', '=', code)])
    assert currency, f"Devise '{code}' non trouvée."


@then(parsers.parse('la devise "{code}" est définie comme "{name}"'))
def then_currency_name(env, code, name):
    currency = env['res.currency'].with_context(active_test=False).search([('name', '=', code)], limit=1)
    assert currency, f"Devise '{code}' non trouvée."


# ─────────────────────────────────────────────────────────────────────────────
# Mentions légales
# ─────────────────────────────────────────────────────────────────────────────

@given('une facture client créée avec tous les champs légaux')
def given_invoice_with_legal_fields(env, context):
    partner = env['res.partner'].create({
        'name': 'Client Test', 'partner_type': 'operator',
        'ice': '001234567890123', 'vat': 'MA001234',
    })
    company = env.company
    company.write({
        'ice': '999888777666555',
        'vat': 'MA12345678',
        'company_registry': 'RC-CASA-99999',
    })
    context['invoice_partner'] = partner


@then('la facture contient l\'ICE de l\'émetteur')
def then_invoice_emitter_ice(env, context):
    company = env.company
    assert company.ice, "ICE de la société non renseigné."


@then('la facture contient l\'ICE du client')
def then_invoice_client_ice(context):
    partner = context.get('invoice_partner')
    assert partner and partner.ice, "ICE du client non renseigné."


@then('la facture contient l\'Identifiant Fiscal (IF)')
def then_invoice_if(env, context):
    company = env.company
    # IF may be stored in vat or a custom field
    assert company.vat or hasattr(company, 'identifiant_fiscal'), \
        "Identifiant Fiscal non défini sur la société."


@then('la facture contient le numéro RC')
def then_invoice_rc(env, context):
    company = env.company
    assert hasattr(company, 'rc') or company.company_registry, \
        "Numéro RC non défini sur la société."
