from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    ice = fields.Char(string='ICE', size=15)
    if_number = fields.Char(string='Identifiant Fiscal (IF)')
    rc_number = fields.Char(string='Registre de Commerce (RC)')
    patente = fields.Char(string='Patente')
    cnss_number = fields.Char(string='N° CNSS employeur')
    forme_juridique = fields.Selection(
        selection=[
            ('sarl', 'SARL'),
            ('sa', 'SA'),
            ('sarl_au', 'SARL AU'),
            ('sas', 'SAS'),
            ('snc', 'SNC'),
            ('gie', 'GIE'),
            ('auto_entrepreneur', 'Auto-entrepreneur'),
            ('autre', 'Autre'),
        ],
        string='Forme juridique',
    )
    capital_social = fields.Monetary(
        string='Capital social (MAD)',
        currency_field='currency_id',
    )
    # Tax identification for invoices
    amo_number = fields.Char(string='N° AMO employeur')
    # Default currency hint — operations use MAD
    default_currency_hint = fields.Char(
        string='Devise par défaut',
        default='MAD',
        readonly=True,
    )
