# -*- coding: utf-8 -*-
"""
telecom.caution.bancaire — Bank guarantee model.

Tracks all bank guarantees (cautions bancaires) attached to a contract:
provisional, definitive, retention, and performance bonds.
"""

from datetime import date, timedelta
from odoo import api, fields, models


class TelecomCautionBancaire(models.Model):
    """Bank guarantee associated with a telecom contract."""

    _name = 'telecom.caution.bancaire'
    _description = 'Caution bancaire'
    _order = 'date_expiration asc, id desc'
    _rec_name = 'reference_bancaire'

    # ------------------------------------------------------------------
    # Relational
    # ------------------------------------------------------------------
    contract_id = fields.Many2one(
        comodel_name='telecom.contract',
        string='Contrat',
        required=True,
        ondelete='cascade',
        index=True,
    )

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------
    caution_type = fields.Selection(
        selection=[
            ('provisoire',          'Caution provisoire (1,5%)'),
            ('definitive',          'Caution définitive (3%)'),
            ('retenue_garantie',    'Retenue de garantie (10%)'),
            ('bonne_fin',           'Caution bonne fin'),
        ],
        string='Type de caution',
        required=True,
    )
    banque = fields.Char(
        string='Banque émettrice',
        required=True,
    )
    reference_bancaire = fields.Char(
        string='Référence bancaire',
        required=True,
    )
    beneficiaire_id = fields.Many2one(
        comodel_name='res.partner',
        string='Bénéficiaire',
    )

    # ------------------------------------------------------------------
    # Amounts
    # ------------------------------------------------------------------
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Devise',
        required=True,
        default=lambda self: self.env.ref('base.MAD', raise_if_not_found=False)
                             or self.env['res.currency'].search([('name', '=', 'MAD')], limit=1),
    )
    montant = fields.Monetary(
        string='Montant',
        currency_field='currency_id',
    )

    # ------------------------------------------------------------------
    # Dates
    # ------------------------------------------------------------------
    date_emission = fields.Date(
        string="Date d'émission",
        required=True,
        default=fields.Date.today,
    )
    date_expiration = fields.Date(
        string="Date d'expiration",
    )
    date_liberation = fields.Date(
        string='Date de libération effective',
    )

    # ------------------------------------------------------------------
    # State (computed from dates)
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=[
            ('active',         'Active'),
            ('expiring_soon',  'Expire bientôt (≤ 60 j)'),
            ('expired',        'Expirée'),
            ('liberee',        'Libérée'),
        ],
        string='Statut',
        compute='_compute_state',
        store=True,
    )

    # ------------------------------------------------------------------
    # Document scan
    # ------------------------------------------------------------------
    document = fields.Binary(
        string='Scan caution',
        attachment=True,
    )
    document_filename = fields.Char(
        string='Nom du fichier',
    )

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------
    notes = fields.Char(
        string='Notes',
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends('date_expiration', 'date_liberation')
    def _compute_state(self):
        """
        Derive state from dates:
        - liberee:        date_liberation is set
        - expired:        expiration date is in the past
        - expiring_soon:  expiration within 60 calendar days
        - active:         otherwise
        """
        today = date.today()
        warning_threshold = today + timedelta(days=60)
        for rec in self:
            if rec.date_liberation:
                rec.state = 'liberee'
            elif rec.date_expiration and rec.date_expiration < today:
                rec.state = 'expired'
            elif rec.date_expiration and rec.date_expiration <= warning_threshold:
                rec.state = 'expiring_soon'
            else:
                rec.state = 'active'
