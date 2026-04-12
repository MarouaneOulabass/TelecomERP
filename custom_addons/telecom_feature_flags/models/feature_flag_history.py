"""Feature flag history model — audit trail for flag changes."""

from odoo import fields, models


class FeatureFlagHistory(models.Model):
    """Audit log entry for a feature flag state change."""

    _name = 'feature.flag.history'
    _description = 'Feature Flag History'
    _order = 'changed_at desc'

    flag_id = fields.Many2one(
        'feature.flag',
        string='Feature Flag',
        required=True,
        ondelete='cascade',
        index=True,
    )
    changed_by = fields.Many2one(
        'res.users',
        string='Changed By',
        required=True,
    )
    changed_at = fields.Datetime(
        string='Changed At',
        required=True,
        default=fields.Datetime.now,
    )
    old_value = fields.Boolean(
        string='Old Value',
    )
    new_value = fields.Boolean(
        string='New Value',
    )
    reason = fields.Char(
        string='Reason',
    )
