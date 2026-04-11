# -*- coding: utf-8 -*-
import odoo
odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
registry = odoo.registry('telecomerp')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    company = env.company
    print(f"Company currency: {company.currency_id.name} / {company.currency_id.symbol}")

    mad = env['res.currency'].with_context(active_test=False).search([('name', '=', 'MAD')], limit=1)
    eur = env['res.currency'].with_context(active_test=False).search([('name', '=', 'EUR')], limit=1)
    usd = env['res.currency'].with_context(active_test=False).search([('name', '=', 'USD')], limit=1)

    print(f"MAD: active={mad.active}, symbol='{mad.symbol}'" if mad else "MAD: NOT FOUND")
    print(f"EUR: active={eur.active}, symbol='{eur.symbol}'" if eur else "EUR: NOT FOUND")
    print(f"USD: active={usd.active}, symbol='{usd.symbol}'" if usd else "USD: NOT FOUND")

    # The company uses USD — we can't change it (journal entries exist)
    # But we can make MAD the display currency for all telecom models
    # by ensuring telecom model defaults point to MAD

    # Make sure MAD is active
    if mad and not mad.active:
        mad.write({'active': True})
        print("MAD activated")

    # Set MAD symbol properly
    if mad and mad.symbol != 'MAD':
        mad.write({'symbol': 'MAD'})
        print(f"MAD symbol fixed to 'MAD'")

    # Deactivate EUR to avoid confusion (if not used)
    if eur:
        # Check if EUR is used anywhere
        eur_count = env['account.move.line'].search_count([('currency_id', '=', eur.id)])
        if eur_count == 0:
            eur.write({'active': False})
            print("EUR deactivated (not used)")
        else:
            print(f"EUR kept active ({eur_count} journal entries)")

    cr.commit()
    print("\nDone")
