# -*- coding: utf-8 -*-
import odoo
odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
registry = odoo.registry('telecomerp')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    print('=' * 60)
    print('  AUDIT FINAL — TelecomERP')
    print('=' * 60)

    # Modules
    mods = env['ir.module.module'].search([('state', '=', 'installed'), ('name', 'like', 'telecom_%')])
    print('\nMODULES INSTALLES: %d' % len(mods))
    for m in mods.sorted('name'):
        print('  %s' % m.name)

    # Data
    print('\nDONNEES:')
    checks = [
        ('Sites', 'telecom.site', []),
        ('Interventions', 'telecom.intervention', []),
        ('Employes tech', 'hr.employee', [('telecom_technicien', '=', True)]),
        ('Equipements', 'telecom.equipment', []),
        ('Vehicules', 'telecom.vehicle', []),
        ('Projets', 'project.project', []),
        ('AO', 'telecom.ao', []),
        ('Contrats', 'telecom.contract', []),
        ('Cost entries', 'telecom.cost.entry', []),
        ('Bulletins paie', 'telecom.paie.bulletin', []),
        ('Tenants', 'telecom.tenant', []),
    ]
    for label, model, domain in checks:
        if model in env:
            count = env[model].search_count(domain)
            print('  %s: %d' % (label, count))

    # Views & Actions
    views = env['ir.ui.view'].search_count([('model', 'like', 'telecom.%')])
    actions = env['ir.actions.act_window'].search_count([('res_model', 'like', 'telecom.%')])
    menus = env['ir.ui.menu'].search([])
    telecom_menus = [m for m in menus if 'telecom' in (m.get_external_id().get(m.id, '') or '')]
    print('\nUI:')
    print('  Vues telecom: %d' % views)
    print('  Actions telecom: %d' % actions)
    print('  Menus telecom: %d' % len(telecom_menus))

    # Languages
    langs = env['res.lang'].search([('active', '=', True)])
    print('\nLANGUES: %s' % ', '.join(l.name for l in langs))

    # Currency
    mad = env['res.currency'].search([('name', '=', 'MAD'), ('active', '=', True)], limit=1)
    print('MAD: %s' % ('active' if mad else 'MISSING'))

    print('\n' + '=' * 60)
    print('  STATUT: COMPLET')
    print('=' * 60)
