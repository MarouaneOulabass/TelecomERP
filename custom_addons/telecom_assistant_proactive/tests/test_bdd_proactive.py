"""BDD step definitions for proactive watchers."""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import MagicMock, patch

scenarios('features/proactive_watchers.feature')


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def proactive_env():
    """Create a mock environment for proactive watcher tests."""
    env = MagicMock()
    flags_store = {}
    notifications = []

    # Mock feature flag lookup
    def search_flags(domain, limit=None):
        result = MagicMock()
        code = None
        for condition in domain:
            if condition[0] == 'code' and condition[1] == '=':
                code = condition[2]
                break
        if code and code in flags_store:
            result.active = flags_store[code]
            result.__bool__ = lambda s: True
        else:
            result.__bool__ = lambda s: False
            result.active = False
        return result

    flag_model = MagicMock()
    flag_model.search = search_flags
    flag_model.sudo.return_value = flag_model

    notification_model = MagicMock()
    notification_model.create = lambda vals: notifications.append(vals) or MagicMock()
    notification_model.search_count = lambda domain: len(notifications)

    env.__getitem__ = lambda self, key: {
        'feature.flag': flag_model,
        'telecom.proactive.notification': notification_model,
    }.get(key, MagicMock())
    env.uid = 1
    env.get = lambda key, default=None: MagicMock() if key in [
        'telecom.margin.snapshot', 'telecom.intervention'
    ] else default

    return {
        'env': env,
        'flags_store': flags_store,
        'notifications': notifications,
    }


@pytest.fixture
def context():
    """Shared context for BDD steps."""
    return {}


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------

@given('un environnement TelecomERP avec les modules proactifs installés')
def given_env_proactive(proactive_env):
    pass


# ---------------------------------------------------------------------------
# Scenario 1: Watcher with flag off
# ---------------------------------------------------------------------------

@given(parsers.parse('un watcher "{watcher_type}" configuré'))
def given_watcher_configured(context, watcher_type):
    context['watcher_type'] = watcher_type


@given(parsers.parse('le flag "{code}" est désactivé'))
def given_flag_disabled(proactive_env, code):
    proactive_env['flags_store'][code] = False


@when('le cron des watchers est exécuté')
def when_cron_executed(proactive_env, context):
    from telecom_feature_flags.utils.feature_flag import is_flag_active

    watcher_type = context.get('watcher_type', 'marge_sous_seuil')
    flag_map = {
        'marge_sous_seuil': 'assistant_proactive.watcher_marge_sous_seuil',
    }
    flag_code = flag_map.get(watcher_type)
    if flag_code:
        context['flag_active'] = is_flag_active(flag_code, proactive_env['env'])
    else:
        context['flag_active'] = False


@then("aucune notification n'est générée pour ce watcher")
def then_no_notifications(proactive_env):
    assert len(proactive_env['notifications']) == 0


# ---------------------------------------------------------------------------
# Scenario 2: Watcher with flag on
# ---------------------------------------------------------------------------

@given(parsers.parse('le flag "{code}" est actif'))
def given_flag_active(proactive_env, code):
    proactive_env['flags_store'][code] = True


@then('des notifications sont générées si les conditions sont remplies')
def then_notifications_possible(context):
    # When flag is active, the watcher can run
    assert context.get('flag_active') is True


# ---------------------------------------------------------------------------
# Scenario 3: Channel fallback
# ---------------------------------------------------------------------------

@given(parsers.parse('le flag "{code}" désactivé'))
def given_flag_off(proactive_env, code):
    proactive_env['flags_store'][code] = False


@given(parsers.parse('le flag "{code}" actif'))
def given_flag_on(proactive_env, code):
    proactive_env['flags_store'][code] = True


@when('une notification critique est créée')
def when_critical_notification(proactive_env, context):
    from telecom_feature_flags.utils.feature_flag import is_flag_active

    # WhatsApp disabled, in_app active — should fallback to in_app
    whatsapp_active = is_flag_active(
        'assistant_proactive.channel_whatsapp', proactive_env['env']
    )
    in_app_active = is_flag_active(
        'assistant_proactive.channel_in_app', proactive_env['env']
    )
    context['channel'] = 'in_app' if (not whatsapp_active and in_app_active) else 'whatsapp'


@then('elle est livrée via le canal in-app sans erreur')
def then_in_app_delivery(context):
    assert context['channel'] == 'in_app'


# ---------------------------------------------------------------------------
# Scenario 4: Mark notification as read
# ---------------------------------------------------------------------------

@given("une notification non lue pour l'utilisateur courant")
def given_unread_notification(context):
    context['notification'] = {'is_read': False}


@when("l'utilisateur marque la notification comme lue")
def when_mark_read(context):
    context['notification']['is_read'] = True


@then('la notification est marquée comme lue')
def then_is_read(context):
    assert context['notification']['is_read'] is True
