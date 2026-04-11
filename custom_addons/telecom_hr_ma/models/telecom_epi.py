# -*- coding: utf-8 -*-
"""
telecom_epi.py
==============
Two models:
- telecom.epi.type     : reference table for EPI (Personal Protective Equipment) types
- telecom.epi.dotation : employee EPI assignment/dotation record with renewal tracking
"""

from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TelecomEpiType(models.Model):
    """Reference table: EPI (Équipement de Protection Individuelle) types."""

    _name = 'telecom.epi.type'
    _description = 'Type EPI'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Désignation EPI',
        required=True,
    )

    code = fields.Char(
        string='Code',
        size=20,
    )

    description = fields.Char(
        string='Description',
    )

    periodicite_renouvellement_mois = fields.Integer(
        string='Périodicité de renouvellement (mois)',
        default=12,
        help='Durée de vie réglementaire / délai de renouvellement en mois.',
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Ce type EPI existe déjà.'),
    ]


class TelecomEpiDotation(models.Model):
    """Employee EPI assignment record with expiry and state tracking."""

    _name = 'telecom.epi.dotation'
    _description = 'Dotation EPI employé'
    _order = 'date_expiration asc, employee_id'
    _rec_name = 'epi_type_id'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employé',
        required=True,
        ondelete='cascade',
        index=True,
    )

    epi_type_id = fields.Many2one(
        comodel_name='telecom.epi.type',
        string='Type EPI',
        required=True,
        ondelete='restrict',
    )

    date_dotation = fields.Date(
        string='Date de dotation',
        required=True,
        default=fields.Date.today,
    )

    date_expiration = fields.Date(
        string="Date d'expiration",
        compute='_compute_date_expiration',
        store=True,
        readonly=False,  # allow manual override
        help='Calculée automatiquement : date_dotation + périodicité. Modifiable manuellement.',
    )

    quantite = fields.Integer(
        string='Quantité',
        default=1,
    )

    etat = fields.Selection(
        selection=[
            ('neuf', 'Neuf'),
            ('bon_etat', 'Bon état'),
            ('use', 'Usé'),
            ('a_remplacer', 'À remplacer'),
            ('remplace', 'Remplacé'),
        ],
        string='État',
        default='neuf',
    )

    notes = fields.Char(
        string='Notes',
    )

    state = fields.Selection(
        selection=[
            ('valid', 'Valide'),
            ('expiring_soon', 'Expire bientôt (< 60 j)'),
            ('expired', 'Expiré'),
        ],
        string='Statut',
        compute='_compute_state',
        store=True,
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('date_dotation', 'epi_type_id', 'epi_type_id.periodicite_renouvellement_mois')
    def _compute_date_expiration(self):
        """Auto-fill expiration from dotation date + renewal period.
        Only fills if date_expiration is not yet set to preserve manual overrides."""
        for rec in self:
            if rec.date_dotation and rec.epi_type_id and not rec.date_expiration:
                months = rec.epi_type_id.periodicite_renouvellement_mois or 12
                rec.date_expiration = rec.date_dotation + relativedelta(months=months)

    @api.depends('date_expiration')
    def _compute_state(self):
        today = date.today()
        for rec in self:
            if not rec.date_expiration:
                rec.state = 'valid'
            elif rec.date_expiration < today:
                rec.state = 'expired'
            elif (rec.date_expiration - today).days <= 60:
                rec.state = 'expiring_soon'
            else:
                rec.state = 'valid'

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains('date_dotation', 'date_expiration')
    def _check_dates(self):
        for rec in self:
            if rec.date_dotation and rec.date_expiration:
                if rec.date_expiration < rec.date_dotation:
                    raise ValidationError(
                        _("La date d'expiration doit être postérieure à la date de dotation.")
                    )

    # ------------------------------------------------------------------
    # Onchange — suggest expiry when user fills dotation date or type
    # ------------------------------------------------------------------

    @api.onchange('date_dotation', 'epi_type_id')
    def _onchange_compute_expiration(self):
        if self.date_dotation and self.epi_type_id:
            months = self.epi_type_id.periodicite_renouvellement_mois or 12
            self.date_expiration = self.date_dotation + relativedelta(months=months)
