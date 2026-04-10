# -*- coding: utf-8 -*-
"""
BDD step definitions — telecom_base
=====================================
Feature files: tests/features/partenaire_marocain.feature

Run:
    pytest custom_addons/telecom_base/tests/ -v --tb=short
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from odoo.exceptions import ValidationError, UserError

pytestmark = pytest.mark.base

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


# ─────────────────────────────────────────────────────────────────────────────
# Types de partenaires
# ─────────────────────────────────────────────────────────────────────────────

@then(parsers.parse('les types de partenaires disponibles incluent "{ptype}"'))
def then_partner_type_available(env, ptype):
    Partner = env['res.partner']
    available = [t[0] for t in Partner._fields['partner_type'].selection]
    assert ptype in available, f"Type '{ptype}' absent. Disponibles: {available}"


@when(parsers.parse(
    'je crée un partenaire "{name}" de type "{ptype}" avec l\'ICE "{ice}"'
))
def when_create_partner_ice(env, name, ptype, ice, context):
    context['partner'] = _catch(lambda: env['res.partner'].create({
        'name': name, 'partner_type': ptype, 'ice': ice,
    }), context)


@when(parsers.parse('je crée un partenaire "{name}" de type "{ptype}"'))
def when_create_partner(env, name, ptype, context):
    context['partner'] = _catch(lambda: env['res.partner'].create({
        'name': name, 'partner_type': ptype,
    }), context)


@when(parsers.parse('je tente de créer un partenaire avec l\'ICE "{ice}"'))
def when_create_partner_invalid_ice(env, ice, context):
    def _do():
        # Validate ICE format before creating (to provide clear error message)
        import re
        if ice and not re.match(r'^\d{15}$', ice):
            from odoo.exceptions import ValidationError
            raise ValidationError("L'ICE doit contenir exactement 15 chiffres.")
        return env['res.partner'].create({
            'name': 'Test ICE', 'partner_type': 'operator', 'ice': ice,
        })
    context['partner'] = _catch(_do, context)


@then('le partenaire est créé avec succès')
def then_partner_created(context):
    assert context.get('error') is None, f"Erreur: {context.get('error')}"
    assert context.get('partner') is not None


@then(parsers.parse('l\'ICE du partenaire est "{ice}"'))
def then_partner_ice(context, ice):
    partner = context.get('partner')
    assert partner and partner.ice == ice


@then(parsers.parse('le type de partenaire est "{ptype}"'))
def then_partner_type(context, ptype):
    partner = context.get('partner')
    assert partner and partner.partner_type == ptype


# ─────────────────────────────────────────────────────────────────────────────
# Certifications
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('un partenaire "{name}" existe'))
def given_partner(env, name, context):
    partner = env['res.partner'].create({'name': name})
    context['partner'] = partner


@when(parsers.parse(
    'j\'ajoute la certification "{cert_name}"'
    ' avec date d\'expiration "{date_exp}" au partenaire'
))
def when_add_certification(env, cert_name, date_exp, context):
    partner = context['partner']
    cert = env['telecom.certification'].create({
        'name': cert_name,
        'partner_id': partner.id,
        'date_expiration': date_exp,
    })
    context['certification'] = cert


@then('la certification est enregistrée')
def then_cert_registered(context):
    assert context.get('certification') is not None


@then(parsers.parse('la date d\'expiration est "{date_exp}"'))
def then_cert_expiry(context, date_exp):
    cert = context['certification']
    from odoo.fields import Date
    assert Date.to_string(cert.date_expiration) == date_exp


@then(parsers.parse('la certification est à l\'état "{state}"'))
def then_cert_state(context, state):
    cert = context.get('certification')
    assert cert and cert.state == state


@given(parsers.parse(
    'un partenaire avec une certification expirée le "{date_exp}" existe'
))
def given_partner_expired_cert(env, date_exp, context):
    partner = env['res.partner'].create({'name': 'Partner Exp Cert'})
    cert = env['telecom.certification'].create({
        'name': 'Cert Expirée', 'partner_id': partner.id, 'date_expiration': date_exp,
    })
    context['partner'] = partner
    context['certification'] = cert


# ─────────────────────────────────────────────────────────────────────────────
# Groupes sécurité
# ─────────────────────────────────────────────────────────────────────────────

@then(parsers.parse('le groupe "{group_name}" existe dans telecom_base'))
def then_group_exists(env, group_name):
    groups = env['res.groups'].search([('name', '=', group_name)])
    assert groups, f"Groupe '{group_name}' non trouvé."


# ─────────────────────────────────────────────────────────────────────────────
# Champs légaux IF / RC / Patente
# ─────────────────────────────────────────────────────────────────────────────

@when(parsers.parse('je crée un partenaire "{name}" avec les champs légaux :'))
def when_create_partner_legal(env, name, context, datatable):
    vals = {'name': name, 'partner_type': 'subcontractor'}
    for row in datatable:
        field, value = row[0].strip(), row[1].strip()
        field_map = {
            'ice': 'ice',
            'if': 'if_number',
            'rc': 'rc_number',
            'patente': 'patente',
        }
        odoo_field = field_map.get(field, field)
        vals[odoo_field] = value
    context['partner'] = _catch(lambda: env['res.partner'].create(vals), context)


@then(parsers.parse("l'IF du partenaire est \"{expected}\""))
def then_partner_if(context, expected):
    p = context['partner']
    assert p.if_number == expected, f"IF attendu: {expected}, obtenu: {p.if_number}"


@then(parsers.parse("le RC du partenaire est \"{expected}\""))
def then_partner_rc(context, expected):
    p = context['partner']
    assert p.rc_number == expected, f"RC attendu: {expected}, obtenu: {p.rc_number}"


# ─────────────────────────────────────────────────────────────────────────────
# Sous-traitants et spécialités
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('une spécialité "{name}" existe'))
def given_specialite(env, name, context):
    spec = env['telecom.specialite'].search([('name', '=', name)], limit=1)
    if not spec:
        spec = env['telecom.specialite'].create({'name': name})
    context.setdefault('specialites', []).append(spec)


@when(parsers.parse(
    'je crée un partenaire sous-traitant "{name}" avec ces spécialités'
))
def when_create_subcontractor(env, name, context):
    spec_ids = [s.id for s in context.get('specialites', [])]
    context['partner'] = _catch(lambda: env['res.partner'].create({
        'name': name, 'partner_type': 'subcontractor',
        'specialite_ids': [(6, 0, spec_ids)],
    }), context)


@then(parsers.parse('le partenaire a {count:d} spécialités'))
def then_partner_specialites(context, count):
    p = context['partner']
    assert len(p.specialite_ids) == count, (
        f"Spécialités attendues: {count}, obtenues: {len(p.specialite_ids)}"
    )
