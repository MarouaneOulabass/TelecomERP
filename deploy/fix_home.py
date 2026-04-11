# -*- coding: utf-8 -*-
import odoo
odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
registry = odoo.registry('telecomerp')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    # Find the sites action (act_window, not URL)
    sites_action = env['ir.actions.act_window'].search([
        ('res_model', '=', 'telecom.site'),
        ('view_mode', 'like', 'tree'),
    ], limit=1)

    # Remove the broken URL action as home
    admin = env['res.users'].browse(2)
    if sites_action:
        admin.write({'action_id': sites_action.id})
        print(f"Home action: {sites_action.name} (id={sites_action.id})")
    else:
        # Fallback: no home action (goes to default)
        admin.write({'action_id': False})
        print("Home action: cleared (default Odoo)")

    cr.commit()
    print("Done")
