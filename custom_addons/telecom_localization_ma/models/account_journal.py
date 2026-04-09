from odoo import fields, models


class AccountJournal(models.Model):
    """Extend account.journal with LCN (Lettre de Change Normalisée) support."""

    _inherit = 'account.journal'

    is_lcn = fields.Boolean(
        string='Journal LCN',
        default=False,
        help=(
            "Activer si ce journal est dédié aux Lettres de Change Normalisées (LCN). "
            "Permet le suivi des remises LCN auprès de la banque."
        ),
    )
    lcn_bank_ref = fields.Char(
        string='Référence bancaire LCN',
        help=(
            "Référence du contrat ou de la convention LCN auprès de l'établissement bancaire "
            "(ex. numéro de dossier remise LCN)."
        ),
    )
