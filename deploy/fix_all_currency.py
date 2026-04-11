# -*- coding: utf-8 -*-
"""Fix all telecom records to use MAD instead of company default (USD)."""
import odoo
odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
registry = odoo.registry('telecomerp')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    mad = env['res.currency'].with_context(active_test=False).search([('name', '=', 'MAD')], limit=1)
    if not mad:
        print('MAD currency not found!')
        exit()

    print(f'MAD: id={mad.id}, symbol={mad.symbol}')

    # All telecom models with currency_id field
    models_to_fix = [
        'telecom.paie.bulletin',
        'telecom.equipment',
        'telecom.vehicle.entretien',
        'telecom.decompte',
        'telecom.situation',
        'telecom.avance.demarrage',
        'telecom.avance.remboursement',
        'telecom.contract',
        'telecom.ao',
        'telecom.caution.bancaire',
        'telecom.equipment.historique',
    ]

    total_fixed = 0
    for model_name in models_to_fix:
        if model_name not in env:
            continue
        model = env[model_name]
        if 'currency_id' not in model._fields:
            continue

        records = model.with_context(active_test=False).search([
            ('currency_id', '!=', mad.id),
        ])
        if records:
            records.write({'currency_id': mad.id})
            total_fixed += len(records)
            print(f'  {model_name}: {len(records)} records -> MAD')

    # Also fix res.partner capital_currency_id
    partners = env['res.partner'].search([('capital_currency_id', '!=', False), ('capital_currency_id', '!=', mad.id)])
    if partners:
        partners.write({'capital_currency_id': mad.id})
        print(f'  res.partner capital: {len(partners)} -> MAD')

    cr.commit()
    print(f'\nTotal: {total_fixed} records fixed to MAD')

    # Clean up this script from custom_addons
    import os
    for f in ['fix_bulletin_currency.py', 'fix_all_currency.py']:
        path = os.path.join('/mnt/extra-addons', f)
        if os.path.exists(path):
            os.remove(path)
