# -*- coding: utf-8 -*-
"""
telecom_habilitation.py
=======================
Two models:
- telecom.habilitation.type  : reference table for habilitation types
- telecom.habilitation.employee : individual habilitation record per employee

The expiry date defaults to date_obtention + periodicite_renouvellement months
but can be overridden manually (stored field with optional compute).
"""

from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TelecomHabilitationType(models.Model):
    """Reference table: safety habilitation types (working at height, electrical, etc.)."""

    _name = 'telecom.habilitation.type'
    _description = 'Type d\'habilitation sécurité'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Désignation',
        required=True,
    )

    code = fields.Char(
        string='Code',
        required=True,
        size=30,
        help='Code unique identifiant le type d\'habilitation (ex: TRAV_HAUTEUR).',
    )

    description = fields.Text(
        string='Description',
    )

    periodicite_renouvellement = fields.Integer(
        string='Périodicité de renouvellement (mois)',
        default=36,
        help='Nombre de mois avant expiration / renouvellement obligatoire.',
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
    )

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code)', 'Ce code d\'habilitation est déjà utilisé.'),
        ('name_uniq', 'UNIQUE(name)', 'Ce type d\'habilitation existe déjà.'),
    ]


class TelecomHabilitationEmployee(models.Model):
    """Employee individual habilitation record with expiry tracking."""

    _name = 'telecom.habilitation.employee'
    _description = 'Habilitation employé'
    _order = 'date_expiration asc, employee_id'
    _rec_name = 'habilitation_type_id'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employé',
        required=True,
        ondelete='cascade',
        index=True,
    )

    habilitation_type_id = fields.Many2one(
        comodel_name='telecom.habilitation.type',
        string='Type d\'habilitation',
        required=True,
        ondelete='restrict',
    )

    date_obtention = fields.Date(
        string="Date d'obtention",
        required=True,
    )

    # date_expiration is stored; it gets auto-computed when date_obtention or
    # habilitation_type_id changes, but the user can also override it manually.
    date_expiration = fields.Date(
        string="Date d'expiration",
        store=True,
        compute='_compute_date_expiration',
        readonly=False,   # allow manual override
        help='Calculée automatiquement depuis la date d\'obtention + périodicité. '
             'Peut être saisie manuellement pour remplacer le calcul.',
    )

    organisme_formateur = fields.Char(
        string='Organisme formateur',
    )

    document = fields.Binary(
        string='Document (scan/PDF)',
        attachment=True,
    )

    document_filename = fields.Char(
        string='Nom du fichier',
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
        help='Calculé automatiquement d\'après la date d\'expiration.',
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('date_obtention', 'habilitation_type_id', 'habilitation_type_id.periodicite_renouvellement')
    def _compute_date_expiration(self):
        """Auto-fill date_expiration from date_obtention + periodicite months.
        Only fills if date_expiration is not yet set (to preserve manual overrides
        during the same session). On existing records the stored value is kept."""
        for rec in self:
            if rec.date_obtention and rec.habilitation_type_id and not rec.date_expiration:
                months = rec.habilitation_type_id.periodicite_renouvellement or 36
                rec.date_expiration = rec.date_obtention + relativedelta(months=months)

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

    @api.constrains('date_obtention', 'date_expiration')
    def _check_dates(self):
        for rec in self:
            if rec.date_obtention and rec.date_expiration:
                if rec.date_expiration < rec.date_obtention:
                    raise ValidationError(
                        "La date d'expiration doit être postérieure à la date d'obtention."
                    )

    # ------------------------------------------------------------------
    # Onchange — auto-compute expiry when user changes key fields
    # ------------------------------------------------------------------

    @api.onchange('date_obtention', 'habilitation_type_id')
    def _onchange_compute_expiration(self):
        """Suggest expiry date when the user sets obtention date or habilitation type."""
        if self.date_obtention and self.habilitation_type_id:
            months = self.habilitation_type_id.periodicite_renouvellement or 36
            self.date_expiration = self.date_obtention + relativedelta(months=months)
