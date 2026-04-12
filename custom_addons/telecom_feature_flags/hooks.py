"""Post-init hook for automatic feature flag discovery."""

import importlib
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Scan all installed modules for feature_flags.py and register their flags."""
    _discover_and_register_flags(env)


def _discover_and_register_flags(env):
    """Discover feature_flags.py files in installed modules and register flags."""
    from .utils.feature_flag import register_flags

    installed_modules = env['ir.module.module'].search([
        ('state', '=', 'installed'),
        ('name', 'like', 'telecom_%'),
    ])

    for module in installed_modules:
        module_name = module.name
        try:
            mod = importlib.import_module(f'odoo.addons.{module_name}.feature_flags')
            if hasattr(mod, 'FLAGS'):
                register_flags(module_name, mod.FLAGS, env)
                _logger.info(
                    "Registered %d feature flags from %s",
                    len(mod.FLAGS), module_name,
                )
        except (ImportError, ModuleNotFoundError):
            # Module does not have a feature_flags.py — this is normal
            pass
        except Exception:
            _logger.exception(
                "Error loading feature flags from %s", module_name,
            )
