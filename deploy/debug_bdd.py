# -*- coding: utf-8 -*-
import odoo
import subprocess
import os
odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
registry = odoo.registry('telecomerp')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    # 1. Check pytest location
    print("=== PYTEST ===")
    for path in ['/var/lib/odoo/.local/bin/pytest', '/usr/local/bin/pytest', '/usr/bin/pytest']:
        exists = os.path.exists(path)
        print(f"  {path}: {'EXISTS' if exists else 'MISSING'}")

    # 2. Check test run model
    print("\n=== TEST RUN MODEL ===")
    Run = env['telecom.test.run']
    run = Run.create({'module_filter': ''})
    print(f"  Created run id={run.id}")

    # 3. Try running tests manually
    print("\n=== MANUAL TEST RUN ===")
    addons_path = '/mnt/extra-addons'
    cmd = ['/var/lib/odoo/.local/bin/pytest', addons_path, '--collect-only', '-q', '--no-header']

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60,
            env={**os.environ, 'ODOO_RC': '/etc/odoo/odoo.conf', 'ODOO_DB': 'telecomerp'},
        )
        lines = result.stdout.strip().split('\n')
        print(f"  Exit code: {result.returncode}")
        print(f"  Last line: {lines[-1] if lines else 'empty'}")
        if result.stderr:
            print(f"  Stderr (last 200): {result.stderr[-200:]}")
    except Exception as e:
        print(f"  ERROR: {e}")

    # 4. Try actual run via model method
    print("\n=== MODEL RUN ===")
    try:
        run.action_run_tests()
        print(f"  State: {run.state}")
        print(f"  Total: {run.total_tests}")
        print(f"  Passed: {run.passed}")
        print(f"  Failed: {run.failed}")
        if run.output:
            print(f"  Output (last 300): {run.output[-300:]}")
    except Exception as e:
        print(f"  ERROR: {e}")

    cr.rollback()
