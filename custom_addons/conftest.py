# -*- coding: utf-8 -*-
"""
TelecomERP — Shared pytest-bdd fixtures for all modules.

This conftest.py handles the tricky Odoo 17 requirement that all module
imports must go through `odoo.addons.*`.  We achieve this by:

  1. Bootstrapping Odoo at `pytest_configure` time (before any collection)
  2. Pre-importing every telecom_* module through `odoo.addons.*`
  3. Aliasing `sys.modules['telecom_*'] → sys.modules['odoo.addons.telecom_*']`
     so that when pytest later collects test files, Python finds the
     already-imported package and does NOT re-import via the local path.
"""
import os
import sys
import glob
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# pytest_configure — runs BEFORE any test file is collected
# ─────────────────────────────────────────────────────────────────────────────

def pytest_configure(config):
    """Bootstrap Odoo and pre-import all custom modules through odoo.addons.*"""
    try:
        import odoo
    except ImportError:
        return

    # Parse Odoo config
    config_path = os.environ.get('ODOO_RC', '/etc/odoo/odoo.conf')
    if not os.path.exists(config_path):
        config_path = os.path.join(
            os.path.dirname(__file__), '..', 'config', 'odoo.conf'
        )
    if not os.path.exists(config_path):
        return

    odoo.tools.config.parse_config(['--config', config_path])

    # Ensure custom_addons is in the Odoo addons path
    addons_dir = os.path.dirname(os.path.abspath(__file__))
    current_paths = odoo.tools.config['addons_path'].split(',')
    if addons_dir not in current_paths:
        current_paths.append(addons_dir)
        odoo.tools.config['addons_path'] = ','.join(current_paths)

    # Initialize the Odoo module system so odoo.addons.* resolves
    import odoo.modules.module as mod_module
    mod_module.initialize_sys_path()

    # Discover all telecom_* modules and pre-import them through odoo.addons
    for module_dir in sorted(glob.glob(os.path.join(addons_dir, 'telecom_*'))):
        module_name = os.path.basename(module_dir)
        odoo_key = f'odoo.addons.{module_name}'

        if odoo_key in sys.modules:
            # Already imported — just alias
            sys.modules[module_name] = sys.modules[odoo_key]
            continue

        try:
            # Import through Odoo namespace
            mod = __import__(odoo_key, fromlist=[module_name])
            # Alias so pytest finds it when collecting telecom_*/tests/
            sys.modules[module_name] = mod

            # Also alias sub-packages (models, tests) if already imported
            for sub_key in list(sys.modules.keys()):
                if sub_key.startswith(odoo_key + '.'):
                    short_key = sub_key.replace(f'odoo.addons.', '', 1)
                    if short_key not in sys.modules:
                        sys.modules[short_key] = sys.modules[sub_key]
        except Exception:
            # Module may not be installable yet — skip, pytest will handle
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Odoo environment fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope='session')
def odoo_session():
    """
    Session-scoped Odoo bootstrap.
    Opens the registry for the database.
    Skips the entire session if Odoo is not reachable.
    """
    try:
        import odoo
    except ImportError:
        pytest.skip("Odoo n'est pas disponible dans cet environnement.")

    db_name = os.environ.get('ODOO_DB', odoo.tools.config.get('db_name', 'telecomerp'))
    registry = odoo.registry(db_name)
    return registry, db_name


@pytest.fixture
def env(odoo_session):
    """
    Function-scoped Odoo environment.

    Each BDD scenario runs in isolation:
      - A cursor is opened
      - All writes are rolled back at the end of the test
      - No test can pollute another
    """
    import odoo
    registry, db_name = odoo_session
    with registry.cursor() as cr:
        test_env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {'test_mode': True})
        yield test_env
        cr.rollback()


@pytest.fixture
def superuser(env):
    """Return the admin res.users record."""
    import odoo
    return env['res.users'].browse(odoo.SUPERUSER_ID)


# ─────────────────────────────────────────────────────────────────────────────
# BDD shared state
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def context():
    """
    Mutable dictionary shared between Given/When/Then steps of a scenario.
    Reset automatically at the start of each scenario.
    """
    return {}


# ─────────────────────────────────────────────────────────────────────────────
# Common BDD steps (reused across multiple modules)
# ─────────────────────────────────────────────────────────────────────────────

from pytest_bdd import given, then, parsers


@given('la société courante est initialisée')
def company_ready(env):
    return env.company


@given(parsers.parse('la date du jour est "{date_str}"'))
def mock_today_global(date_str, context):
    """
    Stores a mocked today date for use in step implementations.
    Steps that need date injection should read context['mocked_today'].
    """
    context['mocked_today'] = date_str


@then('une erreur utilisateur est levée')
def user_error_raised(context):
    error = context.get('error', '')
    assert error, (
        "Une UserError était attendue "
        "mais aucune erreur n'a été levée."
    )


@then(parsers.parse('une erreur utilisateur est levée indiquant "{fragment}"'))
def user_error_contains(context, fragment):
    error = context.get('error', '')
    assert error, (
        f"Une UserError était attendue contenant '{fragment}' "
        f"mais aucune erreur n'a été levée."
    )
    assert fragment.lower() in error.lower(), (
        f"Fragment attendu : '{fragment}'\n"
        f"Erreur obtenue   : '{error}'"
    )


@then(parsers.parse('une erreur de validation est levée indiquant "{fragment}"'))
def validation_error_contains(context, fragment):
    error = context.get('error', '')
    assert error, (
        f"Une ValidationError était attendue contenant '{fragment}' "
        f"mais aucune erreur n'a été levée."
    )
    assert fragment.lower() in error.lower(), (
        f"Fragment attendu : '{fragment}'\n"
        f"Erreur obtenue   : '{error}'"
    )


@then(parsers.parse('une erreur d\'intégrité est levée'))
def integrity_error_raised(context):
    assert context.get('error'), (
        "Une erreur d'intégrité était attendue mais aucune erreur n'a été levée."
    )


@then(parsers.parse('une erreur d\'intégrité est levée indiquant "{fragment}"'))
def integrity_error_contains(context, fragment):
    error = context.get('error', '')
    assert error, "Une erreur d'intégrité était attendue."
    assert fragment.lower() in error.lower(), (
        f"Fragment attendu : '{fragment}'\nErreur : '{error}'"
    )
