# -*- coding: utf-8 -*-
import odoo
odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
registry = odoo.registry('telecomerp')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    no_one = env.ref('base.group_no_one')

    # All root menus
    print("ALL ROOT MENUS:")
    print("=" * 70)
    roots = env['ir.ui.menu'].with_context(ir_ui_menu_full_list=True).search(
        [('parent_id', '=', False)], order='sequence'
    )
    for m in roots:
        hidden = no_one.id in m.groups_id.ids
        xid = m.get_external_id().get(m.id, '?')
        module = xid.split('.')[0] if '.' in xid else '?'
        status = 'HIDDEN' if hidden else 'VISIBLE'
        print(f"  [{status:7}] {m.name:30} seq={m.sequence:3}  ({xid})")

    # Telecom module menus that should be under TelecomERP root
    print("\n\nTELECOM MODULE MENUS (all levels):")
    print("=" * 70)
    telecom_menus = env['ir.ui.menu'].with_context(ir_ui_menu_full_list=True).search([])
    for m in telecom_menus:
        xid = m.get_external_id().get(m.id, '')
        if 'telecom_' in xid and not m.parent_id:
            print(f"\n  APP: {m.name} ({xid})")
            for c in env['ir.ui.menu'].search([('parent_id', '=', m.id)], order='sequence'):
                cxid = c.get_external_id().get(c.id, '')
                act = c.action.name if c.action else 'NO ACTION'
                print(f"    {c.name:30} -> {act}")
                for s in env['ir.ui.menu'].search([('parent_id', '=', c.id)], order='sequence'):
                    sact = s.action.name if s.action else 'NO ACTION'
                    print(f"      {s.name:28} -> {sact}")
