# -*- coding: utf-8 -*-
import odoo
odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
registry = odoo.registry('telecomerp')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    company = env.company
    print(f'Company currency: {company.currency_id.name} / {company.currency_id.symbol}')

    mad = env['res.currency'].with_context(active_test=False).search([('name', '=', 'MAD')], limit=1)
    print(f'MAD: id={mad.id}, active={mad.active}, symbol={mad.symbol}')

    # Check bulletin currency field
    bf = env['telecom.paie.bulletin']._fields.get('currency_id')
    if bf:
        print(f'Bulletin currency_id field: type={bf.type}, related={getattr(bf, "related", None)}')
    else:
        print('Bulletin: NO currency_id field — uses company currency')

    # Check existing bulletins
    bulletins = env['telecom.paie.bulletin'].search([], limit=3)
    for b in bulletins:
        if hasattr(b, 'currency_id') and b.currency_id:
            print(f'  Bulletin {b.id}: {b.currency_id.name} ({b.currency_id.symbol})')
        else:
            print(f'  Bulletin {b.id}: no currency_id — shows company currency = {company.currency_id.symbol}')

    # FIX: The problem is company.currency_id = USD
    # All monetary fields without explicit currency_id use company currency
    # We need to add currency_id = MAD to all bulletins
    if mad:
        # Update all bulletins to MAD
        all_bulletins = env['telecom.paie.bulletin'].search([])
        if bf and bf.type == 'many2one':
            all_bulletins.write({'currency_id': mad.id})
            print(f'\nFixed {len(all_bulletins)} bulletins -> MAD')
        else:
            print('\nBulletin has no writable currency_id field')
            print('The currency comes from company — need to check model')

    cr.commit()
