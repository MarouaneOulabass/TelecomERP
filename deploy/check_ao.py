# -*- coding: utf-8 -*-
import odoo
odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
registry = odoo.registry('telecomerp')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    ao = env['telecom.ao']
    methods = [m for m in dir(ao) if m.startswith('action_')]
    print('AO actions:', methods)
    fields = [f for f in ao._fields if 'mont' in f or 'caution' in f]
    print('AO montant/caution fields:', fields)
    # Check if caution is computed from montant_soumis or montant_estimatif
    import inspect
    for fname in ['_compute_caution_provisoire', '_compute_cautions']:
        if hasattr(ao, fname):
            src = inspect.getsource(getattr(type(ao), fname))
            for line in src.split('\n'):
                if 'montant' in line:
                    print(f'  {fname}: {line.strip()}')
