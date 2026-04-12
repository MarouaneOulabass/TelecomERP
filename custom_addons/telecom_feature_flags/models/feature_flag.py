"""Feature flag model — runtime toggles for capabilities."""

import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

# Pattern: snake_case_module.snake_case_flag
FLAG_CODE_PATTERN = re.compile(r'^[a-z_]+\.[a-z_]+$')

CATEGORY_SELECTION = [
    ('watchers', 'Watchers'),
    ('notifications', 'Notifications'),
    ('channels', 'Channels'),
    ('ui', 'UI'),
    ('ux', 'UX'),
    ('debug', 'Debug'),
    ('experimental', 'Experimental'),
    ('core', 'Core'),
]


class FeatureFlag(models.Model):
    """Runtime feature flag declaration."""

    _name = 'feature.flag'
    _description = 'Feature Flag'
    _order = 'capability, category, code'
    _rec_name = 'code'

    code = fields.Char(
        string='Code',
        required=True,
        index=True,
        help="Technical identifier, e.g. assistant_proactive.watcher_marge_sous_seuil",
    )
    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
    )
    description = fields.Text(
        string='Description',
        translate=True,
    )
    capability = fields.Char(
        string='Capability',
        required=True,
        help="Technical name of the capability that declared this flag",
    )
    category = fields.Selection(
        selection=CATEGORY_SELECTION,
        string='Category',
        required=True,
        default='core',
    )
    default_value = fields.Boolean(
        string='Default Value',
        default=False,
    )
    active = fields.Boolean(
        string='Active',
        default=False,
    )
    last_changed_by = fields.Many2one(
        'res.users',
        string='Last Changed By',
        readonly=True,
    )
    last_changed_at = fields.Datetime(
        string='Last Changed At',
        readonly=True,
    )
    history_ids = fields.One2many(
        'feature.flag.history',
        'flag_id',
        string='Change History',
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Feature flag code must be unique.'),
    ]

    @api.constrains('code')
    def _check_code_pattern(self):
        """Ensure flag code matches the required pattern."""
        for record in self:
            if record.code and not FLAG_CODE_PATTERN.match(record.code):
                raise ValidationError(
                    _("Flag code '%(code)s' does not match the required pattern "
                      "'module.flag_name' (lowercase letters and underscores only).",
                      code=record.code)
                )

    def write(self, vals):
        """Override write to log changes to history and update tracking fields."""
        if 'active' in vals:
            for record in self:
                old_value = record.active
                new_value = vals['active']
                if old_value != new_value:
                    self.env['feature.flag.history'].sudo().create({
                        'flag_id': record.id,
                        'changed_by': self.env.uid,
                        'changed_at': fields.Datetime.now(),
                        'old_value': old_value,
                        'new_value': new_value,
                        'reason': vals.get('reason', ''),
                    })
            vals['last_changed_by'] = self.env.uid
            vals['last_changed_at'] = fields.Datetime.now()
        # Remove non-model field before writing
        vals_clean = {k: v for k, v in vals.items() if k != 'reason'}
        return super().write(vals_clean)
