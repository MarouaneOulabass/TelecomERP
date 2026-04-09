from odoo import fields, models


class AccountTax(models.Model):
    """Extend account.tax to flag Retenue à la Source (RAS) taxes."""

    _inherit = 'account.tax'

    is_ras = fields.Boolean(
        string='Retenue à la source (RAS)',
        default=False,
        help="Cocher si cette taxe est une retenue à la source (ex. RAS 10 % prestations).",
    )
