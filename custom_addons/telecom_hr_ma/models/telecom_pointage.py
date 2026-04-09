# -*- coding: utf-8 -*-
"""
telecom_pointage.py
===================
telecom.pointage.chantier: daily field attendance record for telecom technicians.

Features:
- One record per employee × site × date (sql_constraint)
- Float time fields (8.5 = 08:30)
- Computed overtime (> 8h/day)
- Travel allowance (prime de déplacement) in MAD
- Workflow: draft → valide / refuse
- mail.thread for chatter tracking
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class TelecomPointageChantier(models.Model):
    """Daily field attendance record for a technician on a telecom site."""

    _name = 'telecom.pointage.chantier'
    _description = 'Pointage chantier'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, employee_id'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Identification (computed display name)
    # ------------------------------------------------------------------

    name = fields.Char(
        string='Référence',
        compute='_compute_name',
        store=True,
    )

    # ------------------------------------------------------------------
    # Core fields
    # ------------------------------------------------------------------

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employé',
        required=True,
        ondelete='restrict',
        tracking=True,
        index=True,
    )

    site_id = fields.Many2one(
        comodel_name='telecom.site',
        string='Site',
        required=True,
        ondelete='restrict',
        tracking=True,
        index=True,
    )

    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today,
        tracking=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Time fields (float: 8.5 = 08h30)
    # ------------------------------------------------------------------

    heure_debut = fields.Float(
        string='Heure de début',
        required=True,
        default=8.0,
        digits=(4, 2),
    )

    heure_fin = fields.Float(
        string='Heure de fin',
        required=True,
        default=17.0,
        digits=(4, 2),
    )

    duree_heures = fields.Float(
        string='Durée (heures)',
        compute='_compute_duree',
        store=True,
        digits=(4, 2),
    )

    heures_supplementaires = fields.Float(
        string='Heures supplémentaires',
        compute='_compute_duree',
        store=True,
        digits=(4, 2),
        help='Heures au-delà de 8h dans la journée.',
    )

    # ------------------------------------------------------------------
    # Financial
    # ------------------------------------------------------------------

    prime_deplacement = fields.Monetary(
        string='Prime de déplacement',
        currency_field='currency_id',
        default=0.0,
        help='Indemnité de déplacement pour cette journée (MAD).',
        tracking=True,
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Devise',
        default=lambda self: self.env['res.currency'].search([('name', '=', 'MAD')], limit=1).id
            or self.env.company.currency_id.id,
    )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    chef_validation_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Chef validateur',
        help='Chef de chantier qui valide ce pointage.',
        tracking=True,
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Brouillon'),
            ('valide', 'Validé'),
            ('refuse', 'Refusé'),
        ],
        string='Statut',
        default='draft',
        required=True,
        tracking=True,
        copy=False,
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Société',
        default=lambda self: self.env.company,
        required=True,
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------

    @api.depends('employee_id', 'date')
    def _compute_name(self):
        for rec in self:
            emp_name = rec.employee_id.name or ''
            date_str = str(rec.date) if rec.date else ''
            rec.name = f"Pointage {emp_name} {date_str}".strip() or 'Nouveau pointage'

    @api.depends('heure_debut', 'heure_fin')
    def _compute_duree(self):
        for rec in self:
            duree = max(0.0, rec.heure_fin - rec.heure_debut)
            rec.duree_heures = duree
            rec.heures_supplementaires = max(0.0, duree - 8.0)

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------

    def action_valider(self):
        """Validate a draft pointage record (draft → valide)."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    f"Le pointage '{rec.name}' ne peut être validé que depuis l'état Brouillon."
                )
            rec.state = 'valide'
        return True

    def action_refuser(self):
        """Refuse a draft pointage record (draft → refuse)."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    f"Le pointage '{rec.name}' ne peut être refusé que depuis l'état Brouillon."
                )
            rec.state = 'refuse'
        return True

    def action_remettre_brouillon(self):
        """Reset a validated/refused record back to draft."""
        for rec in self:
            rec.state = 'draft'
        return True

    # ------------------------------------------------------------------
    # SQL constraints
    # ------------------------------------------------------------------

    _sql_constraints = [
        (
            'uniq_employee_site_date',
            'UNIQUE(employee_id, site_id, date)',
            'Un seul pointage par employé, par site et par date est autorisé.',
        ),
    ]

    # ------------------------------------------------------------------
    # Python constraints
    # ------------------------------------------------------------------

    @api.constrains('heure_debut', 'heure_fin')
    def _check_heures(self):
        for rec in self:
            if rec.heure_fin <= rec.heure_debut:
                raise UserError(
                    "L'heure de fin doit être postérieure à l'heure de début."
                )
            if not (0.0 <= rec.heure_debut <= 24.0) or not (0.0 <= rec.heure_fin <= 24.0):
                raise UserError("Les heures doivent être comprises entre 0 et 24.")
