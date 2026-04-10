from odoo import api, fields, models
from odoo.exceptions import ValidationError
import re


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ── Moroccan legal identifiers ─────────────────────────────────────────
    ice = fields.Char(
        string='ICE',
        size=15,
        help="Identifiant Commun de l'Entreprise (15 chiffres)",
    )
    if_number = fields.Char(string='Identifiant Fiscal (IF)')
    rc_number = fields.Char(string='Registre de Commerce (RC)')
    patente = fields.Char(string='Patente')
    cnss_number = fields.Char(string='N° CNSS')
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
        currency_field='capital_currency_id',
    )
    capital_currency_id = fields.Many2one(
        'res.currency',
        string='Devise capital',
        default=lambda self: self.env.ref('base.MAD', raise_if_not_found=False),
    )

    # ── Telecom partner classification ────────────────────────────────────
    partner_type = fields.Selection(
        selection=[
            ('operator', 'Opérateur télécom'),
            ('lessor', 'Bailleur de site'),
            ('subcontractor', 'Sous-traitant'),
            ('public_org', 'Organisme public'),
            ('supplier', 'Fournisseur équipements'),
            ('other', 'Autre'),
        ],
        string='Type de tiers télécom',
    )
    specialite_ids = fields.Many2many(
        'telecom.specialite',
        string='Spécialités',
        help="Spécialités du sous-traitant (fibre, RF, courant fort...)",
    )
    certification_ids = fields.One2many(
        'telecom.certification',
        'partner_id',
        string='Certifications & agréments',
    )
    certification_count = fields.Integer(
        string='Nb certifications',
        compute='_compute_certification_count',
    )
    apporteur_affaires = fields.Boolean(
        string="Apporteur d'affaires",
        default=False,
    )
    taux_commission = fields.Float(
        string='Taux commission (%)',
        digits=(5, 2),
    )

    @api.depends('certification_ids')
    def _compute_certification_count(self):
        for rec in self:
            rec.certification_count = len(rec.certification_ids)

    @api.constrains('ice')
    def _check_ice(self):
        for rec in self:
            if rec.ice and (len(rec.ice) != 15 or not rec.ice.isdigit()):
                raise ValidationError("L'ICE doit contenir exactement 15 chiffres.")

    def action_view_certifications(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Certifications',
            'res_model': 'telecom.certification',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }


class TelecomSpecialite(models.Model):
    """Spécialités techniques des sous-traitants et techniciens."""
    _name = 'telecom.specialite'
    _description = 'Spécialité télécom'
    _order = 'name'

    name = fields.Char(string='Spécialité', required=True)
    code = fields.Char(string='Code', size=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Cette spécialité existe déjà.'),
    ]
