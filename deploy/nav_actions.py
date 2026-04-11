# -*- coding: utf-8 -*-
import odoo
odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
registry = odoo.registry('telecomerp')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    acts = env['ir.actions.act_window'].search([('res_model', 'like', 'telecom.%')], order='res_model')
    for a in acts:
        xid = a.get_external_id().get(a.id, '')
        if xid:
            print(f'{a.res_model:40} | {a.name:45} | {xid}')
