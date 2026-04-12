"""Feature flag utilities — decorator, lookup, and registration."""

import functools
import logging

_logger = logging.getLogger(__name__)


def is_flag_active(code, env):
    """Check whether a feature flag is active.

    Returns False if the flag does not exist (fail-safe default).
    """
    flag = env['feature.flag'].sudo().search([('code', '=', code)], limit=1)
    if not flag:
        return False
    return flag.active


def register_flags(capability_name, flags_list, env):
    """Register feature flags from a capability's FLAGS list.

    Idempotent: if a flag already exists, only name/description/category
    are updated. The 'active' state is preserved.
    """
    Flag = env['feature.flag'].sudo()
    for flag_def in flags_list:
        code = flag_def.get('code')
        if not code:
            _logger.warning("Skipping flag without code in %s", capability_name)
            continue

        existing = Flag.search([('code', '=', code)], limit=1)
        vals = {
            'name': flag_def.get('name', code),
            'description': flag_def.get('description', ''),
            'capability': capability_name,
            'category': flag_def.get('category', 'core'),
        }
        if existing:
            # Preserve active state — only update metadata
            existing.write(vals)
        else:
            # New flag — set active from default_value
            vals.update({
                'code': code,
                'default_value': flag_def.get('default_value', False),
                'active': flag_def.get('default_value', False),
            })
            Flag.create(vals)


def feature_flag(code, default_return=None):
    """Decorator that skips function execution if the flag is inactive.

    Usage::

        @feature_flag('assistant_proactive.watcher_marge_sous_seuil')
        def check_marge_sous_seuil(self):
            ...

    If the flag is inactive or does not exist, the decorated method
    returns *default_return* (None by default).
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            env = getattr(self, 'env', None)
            if env is None:
                _logger.warning(
                    "Cannot check feature flag %s: no env on %s",
                    code, type(self).__name__,
                )
                return default_return
            if not is_flag_active(code, env):
                _logger.debug(
                    "Feature flag %s is inactive — skipping %s",
                    code, func.__name__,
                )
                return default_return
            return func(self, *args, **kwargs)
        return wrapper
    return decorator
