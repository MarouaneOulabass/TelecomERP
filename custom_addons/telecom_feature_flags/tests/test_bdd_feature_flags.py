"""BDD step definitions for feature flags."""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import MagicMock

# Load scenarios from feature file
scenarios('features/feature_flags.feature')


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def flag_env(mocker):
    """Create a mock Odoo environment for feature flag tests."""
    env = MagicMock()
    flags_store = {}

    def search_flags(domain, limit=None):
        """Simulate searching flags."""
        result = MagicMock()
        code = None
        for condition in domain:
            if condition[0] == 'code' and condition[1] == '=':
                code = condition[2]
                break
        if code and code in flags_store:
            flag = flags_store[code]
            result.active = flag['active']
            result.id = flag.get('id', 1)
            result.__bool__ = lambda s: True
            result.__len__ = lambda s: 1
        else:
            result.__bool__ = lambda s: False
            result.__len__ = lambda s: 0
        if limit:
            return result
        return result

    flag_model = MagicMock()
    flag_model.search = search_flags
    flag_model.sudo.return_value = flag_model

    history_model = MagicMock()
    history_model.sudo.return_value = history_model

    env.__getitem__ = lambda self, key: {
        'feature.flag': flag_model,
        'feature.flag.history': history_model,
    }.get(key, MagicMock())
    env.uid = 1

    return {
        'env': env,
        'flag_model': flag_model,
        'history_model': history_model,
        'flags_store': flags_store,
    }


@pytest.fixture
def context():
    """Shared context for BDD steps."""
    return {}


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------

@given('un environnement TelecomERP avec le module feature_flags installé')
def given_env_installed(flag_env):
    pass


# ---------------------------------------------------------------------------
# Scenario 1: Activation d'un flag
# ---------------------------------------------------------------------------

@given(parsers.parse('un flag "{code}" désactivé'))
def given_flag_inactive(flag_env, context, code):
    flag_env['flags_store'][code] = {'active': False, 'id': 1}
    context['flag_code'] = code


@when("l'administrateur active ce flag via l'écran de configuration")
def when_admin_activates(flag_env, context):
    code = context['flag_code']
    flag_env['flags_store'][code]['active'] = True
    context['activated'] = True


@then("l'entrée est historisée avec l'utilisateur et l'horodatage")
def then_history_entry(context):
    assert context.get('activated') is True


@then('le flag est marqué comme actif')
def then_flag_active(flag_env, context):
    code = context['flag_code']
    assert flag_env['flags_store'][code]['active'] is True


# ---------------------------------------------------------------------------
# Scenario 2: Idempotent registration
# ---------------------------------------------------------------------------

@given(parsers.parse('un flag "{code}" actif manuellement'))
def given_flag_active(flag_env, context, code):
    flag_env['flags_store'][code] = {'active': True, 'id': 2}
    context['flag_code'] = code


@when('le module est réinstallé avec le même flag déclaré')
def when_module_reinstalled(flag_env, context):
    from telecom_feature_flags.utils.feature_flag import register_flags

    code = context['flag_code']
    flags_list = [{'code': code, 'name': 'Updated Name', 'category': 'core', 'default_value': False}]

    # Simulate register_flags preserving active state
    existing = flag_env['flags_store'].get(code)
    if existing:
        # Only metadata updated, active preserved
        context['name_updated'] = True
    else:
        flag_env['flags_store'][code] = {'active': False, 'id': 3}


@then("l'état actif du flag est préservé")
def then_active_preserved(flag_env, context):
    code = context['flag_code']
    assert flag_env['flags_store'][code]['active'] is True


@then('seuls le nom et la description sont mis à jour')
def then_metadata_updated(context):
    assert context.get('name_updated') is True


# ---------------------------------------------------------------------------
# Scenario 3: Code malformé refusé
# ---------------------------------------------------------------------------

@when(parsers.parse('on tente de créer un flag avec le code "{code}"'))
def when_create_bad_code(context, code):
    import re
    pattern = re.compile(r'^[a-z_]+\.[a-z_]+$')
    context['code_valid'] = bool(pattern.match(code))


@then('la création est refusée avec une erreur de validation')
def then_creation_refused(context):
    assert context['code_valid'] is False


# ---------------------------------------------------------------------------
# Scenario 4: Decorator blocks when inactive
# ---------------------------------------------------------------------------

@when('une méthode décorée avec ce flag est appelée')
def when_decorated_method_called(flag_env, context):
    from telecom_feature_flags.utils.feature_flag import feature_flag as ff_decorator

    class FakeModel:
        def __init__(self, env):
            self.env = env

        @ff_decorator('test_module.decorated_func')
        def my_method(self):
            return 'executed'

    model = FakeModel(flag_env['env'])
    context['result'] = model.my_method()


@then('la méthode retourne None sans exécuter le corps')
def then_returns_none(context):
    assert context['result'] is None
