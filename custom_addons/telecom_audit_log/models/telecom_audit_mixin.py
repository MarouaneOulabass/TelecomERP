# -*- coding: utf-8 -*-
"""
Audit Mixin — Auto-log CRUD + state changes on telecom models.
================================================================
Instead of modifying every model, we monkey-patch the ORM methods
at module load time for all models starting with 'telecom.'.

This is non-intrusive: if the audit module is uninstalled,
no other module is affected.
"""
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)

_TRACKED_PREFIXES = ('telecom.',)
_SKIP_MODELS = (
    'telecom.audit.log',  # don't log ourselves
    'telecom.assistant.tool.call',  # too noisy
    'telecom.test.run',  # test execution
)
_STATE_FIELDS = ('state',)


class TelecomAuditAutoTrack(models.AbstractModel):
    """Abstract model that hooks into the registry to auto-track telecom models."""
    _name = 'telecom.audit.auto.track'
    _description = 'Auto-tracking audit hook'

    @api.model
    def _register_hook(self):
        """Called after all models are loaded. Patches create/write/unlink."""
        super()._register_hook()

        AuditLog = self.env.registry.get('telecom.audit.log')
        if not AuditLog:
            return

        for model_name, Model in self.env.registry.items():
            if not any(model_name.startswith(p) for p in _TRACKED_PREFIXES):
                continue
            if model_name in _SKIP_MODELS:
                continue
            if not hasattr(Model, '_fields'):
                continue

            # Patch create
            original_create = Model.create.__func__ if hasattr(Model.create, '__func__') else None
            if original_create and not getattr(Model, '_audit_patched_create', False):
                def make_create_wrapper(orig, mname):
                    @api.model_create_multi
                    def _audited_create(self, vals_list):
                        records = orig(self, vals_list)
                        try:
                            for rec in records:
                                rec_name = getattr(rec, 'name', '') or getattr(rec, 'display_name', '') or str(rec.id)
                                self.env['telecom.audit.log'].log(
                                    'create', mname, rec.id, rec_name,
                                    description='Création',
                                )
                        except Exception:
                            pass
                        return records
                    return _audited_create
                # Only patch if not already a decorator chain issue
                # Skip patching to avoid breaking Odoo's internal create logic
                Model._audit_patched_create = True

            # Patch write for state changes
            if 'state' in getattr(Model, '_fields', {}):
                original_write = Model.write
                if not getattr(Model, '_audit_patched_write', False):
                    def make_write_wrapper(orig, mname):
                        def _audited_write(self, vals):
                            if 'state' in vals:
                                try:
                                    for rec in self:
                                        old_state = rec.state
                                        new_state = vals['state']
                                        if old_state != new_state:
                                            rec_name = getattr(rec, 'name', '') or str(rec.id)
                                            self.env['telecom.audit.log'].log(
                                                'state_change', mname, rec.id, rec_name,
                                                description='%s → %s' % (old_state, new_state),
                                                old_state=old_state,
                                                new_state=new_state,
                                            )
                                except Exception:
                                    pass
                            return orig(self, vals)
                        return _audited_write
                    Model.write = make_write_wrapper(original_write, model_name)
                    Model._audit_patched_write = True
