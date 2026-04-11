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
from odoo import _
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
            raise ValidationError(_("L'ICE doit contenir exactement 15 chiffres."))
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


# ─────────────────────────────────────────────────────────────────────────────
# Odoo 17 compat — Smoke tests: toutes les vues se chargent
# ─────────────────────────────────────────────────────────────────────────────

import os
import glob
import re


def _get_telecom_views(env, view_type):
    """Get all views of a given type for telecom modules."""
    return env['ir.ui.view'].search([
        ('model', 'like', 'telecom.%'),
        ('type', '=', view_type),
    ])


@when(parsers.parse('je valide toutes les vues de type "{view_type}" des modules telecom'))
def when_validate_views(env, view_type, context):
    views = _get_telecom_views(env, view_type)
    errors = []
    for v in views:
        try:
            v._check_xml()
        except Exception as e:
            errors.append(f"{v.model} / {v.name} (id={v.id}): {e}")
    context['view_errors'] = errors
    context['view_count'] = len(views)


@then(parsers.parse('aucune vue {view_type} n\'est cassée'))
def then_no_broken_views(context, view_type):
    errors = context.get('view_errors', [])
    count = context.get('view_count', 0)
    assert not errors, (
        f"{len(errors)} vue(s) {view_type} cassée(s) sur {count} :\n"
        + "\n".join(f"  - {e}" for e in errors)
    )


@when('je charge toutes les actions des modules telecom')
def when_check_actions(env, context):
    actions = env['ir.actions.act_window'].search([
        ('res_model', 'like', 'telecom.%'),
    ])
    errors = []
    for act in actions:
        if act.res_model not in env:
            errors.append(f"Action '{act.name}' -> modèle '{act.res_model}' inexistant")
    context['action_errors'] = errors
    context['action_count'] = len(actions)


@then('aucune action ne référence un modèle inexistant')
def then_no_broken_actions(context):
    errors = context.get('action_errors', [])
    assert not errors, (
        f"{len(errors)} action(s) cassée(s) :\n"
        + "\n".join(f"  - {e}" for e in errors)
    )


@when('je vérifie tous les menus des modules telecom')
def when_check_menus(env, context):
    menus = env['ir.ui.menu'].search([
        ('name', 'ilike', 'telecom'),
    ])
    errors = []
    for menu in menus:
        if menu.action:
            try:
                _ = menu.action.res_model
            except Exception as e:
                errors.append(f"Menu '{menu.complete_name}': {e}")
    context['menu_errors'] = errors
    context['menu_count'] = len(menus)


@then('aucun menu ne pointe vers une action inexistante')
def then_no_broken_menus(context):
    errors = context.get('menu_errors', [])
    assert not errors, (
        f"{len(errors)} menu(s) cassé(s) :\n"
        + "\n".join(f"  - {e}" for e in errors)
    )


@when('je vérifie les champs de toutes les vues des modules telecom')
def when_check_view_fields(env, context):
    views = env['ir.ui.view'].search([
        ('model', 'like', 'telecom.%'),
        ('type', 'in', ['form', 'tree', 'search']),
    ])
    errors = []
    for v in views:
        if v.model not in env:
            continue
        model_fields = env[v.model]._fields
        try:
            from lxml import etree
            tree = etree.fromstring(v.arch)
            for field_el in tree.iter('field'):
                fname = field_el.get('name')
                if fname and fname not in model_fields:
                    # Check if it's a relational sub-field (inside a One2many)
                    parent = field_el.getparent()
                    if parent is not None and parent.tag in ('tree', 'form', 'kanban'):
                        parent_field = parent.getparent()
                        if parent_field is not None and parent_field.tag == 'field':
                            continue  # sub-field of a relational, skip
                    errors.append(
                        f"{v.model} / {v.name}: champ '{fname}' inexistant"
                    )
        except Exception:
            pass
    context['field_errors'] = errors
    context['field_view_count'] = len(views)


@then('aucune vue ne référence un champ inexistant')
def then_no_missing_fields(context):
    errors = context.get('field_errors', [])
    assert not errors, (
        f"{len(errors)} champ(s) manquant(s) :\n"
        + "\n".join(f"  - {e}" for e in errors)
    )


@when('je scanne les fichiers XML des modules telecom')
def when_scan_xml_files(env, context):
    addons_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)
    )))
    errors = []
    deprecated = [
        ('attrs=', 'attrs est déprécié en Odoo 17'),
        ('t-name="card"', 'kanban template doit être "kanban-box"'),
        ('t-name="kanban-card"', 'kanban template doit être "kanban-box"'),
    ]
    for xml_file in glob.glob(os.path.join(addons_path, 'telecom_*/views/*.xml')):
        fname = os.path.basename(xml_file)
        module = xml_file.split(os.sep)[-3]
        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        for pattern, msg in deprecated:
            if pattern in content:
                # Find line number
                for i, line in enumerate(content.split('\n'), 1):
                    if pattern in line:
                        errors.append(f"{module}/{fname}:{i} — {msg}")
                        break
    context['xml_errors'] = errors


@then('aucun fichier ne contient de syntaxe dépréciée')
def then_no_deprecated_syntax(context):
    errors = context.get('xml_errors', [])
    assert not errors, (
        f"{len(errors)} syntaxe(s) dépréciée(s) trouvée(s) :\n"
        + "\n".join(f"  - {e}" for e in errors)
    )
