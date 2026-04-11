# -*- coding: utf-8 -*-
"""
TelecomERP — Branding & UX setup
==================================
Configure company info, logo, home action, and UI preferences.
"""
import odoo
import base64
import os

odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
registry = odoo.registry('telecomerp')

with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    print("=" * 50)
    print("  TelecomERP — Configuration Branding")
    print("=" * 50)

    # ── 1. Company info ──
    print("\n[1/5] Société...")
    company = env.company
    company.write({
        'name': 'TelecomERP',
        'street': 'Casablanca, Maroc',
        'city': 'Casablanca',
        'country_id': env.ref('base.ma').id,
        'phone': '+212 5 22 00 00 00',
        'website': 'https://erp.kleanse.fr',
        'ice': '000000000000000',
        'forme_juridique': 'sarl',
    })
    # Update partner too
    company.partner_id.write({
        'name': 'TelecomERP',
        'lang': 'fr_FR',
        'tz': 'Africa/Casablanca',
    })
    print(f"  Société: {company.name}")

    # ── 2. Currency MAD as default ──
    print("\n[2/5] Devise MAD par défaut...")
    mad = env['res.currency'].with_context(active_test=False).search([('name', '=', 'MAD')], limit=1)
    if mad:
        mad.write({'active': True})
        try:
            company.write({'currency_id': mad.id})
            print(f"  Devise: {mad.name}")
        except Exception:
            print(f"  Devise: conservée ({company.currency_id.name}) — écritures existantes")

    # ── 3. Admin user setup ──
    print("\n[3/5] Utilisateur admin...")
    admin = env['res.users'].browse(2)

    # Set home action to TelecomERP sites (main working view)
    telecom_action = env.ref('telecom_base.action_telecom_welcome_page', raise_if_not_found=False)
    if not telecom_action:
        # Fallback: find the sites action
        telecom_action = env['ir.actions.act_window'].search([
            ('res_model', '=', 'telecom.site'),
        ], limit=1)

    admin_vals = {
        'name': 'Administrateur TelecomERP',
        'lang': 'fr_FR',
        'tz': 'Africa/Casablanca',
    }
    if telecom_action:
        admin_vals['action_id'] = telecom_action.id
        print(f"  Home action: {telecom_action.name}")
    admin.write(admin_vals)
    print(f"  Admin: {admin.name}")

    # ── 4. Web app title ──
    print("\n[4/5] Titre navigateur...")
    # Set web.base.url
    param = env['ir.config_parameter'].sudo()
    param.set_param('web.base.url', 'https://erp.kleanse.fr')
    print("  URL: https://erp.kleanse.fr")

    # ── 5. Timezone for all users ──
    print("\n[5/5] Timezone Casablanca...")
    users = env['res.users'].search([])
    users.write({'tz': 'Africa/Casablanca'})
    print(f"  {len(users)} utilisateurs mis à jour")

    cr.commit()

    print("\n" + "=" * 50)
    print("  Branding terminé !")
    print("=" * 50)
