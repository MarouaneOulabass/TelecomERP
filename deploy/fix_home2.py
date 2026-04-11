# -*- coding: utf-8 -*-
import odoo
odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
registry = odoo.registry('telecomerp')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    sites_action = env.ref('telecom_site.action_telecom_site', raise_if_not_found=False)
    admin = env['res.users'].browse(2)

    if sites_action:
        admin.write({'action_id': sites_action.id})
        print(f"Home action set to: {sites_action.name}")
    else:
        print("telecom_site.action_telecom_site not found")
        # List available telecom actions
        acts = env['ir.actions.act_window'].search([('res_model', 'like', 'telecom.%')], limit=5)
        for a in acts:
            xid = a.get_external_id().get(a.id, '?')
            print(f"  Available: {a.name} ({xid})")

    cr.commit()
