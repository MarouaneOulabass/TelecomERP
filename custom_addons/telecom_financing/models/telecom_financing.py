# -*- coding: utf-8 -*-
"""
telecom.cout.financier — Financial cost tracking for project margin
====================================================================
Tracks financial costs (bank credit, leasing, bonds, etc.) and computes
interest over the duration. Auto-creates a telecom.cost.entry on creation.
"""
from datetime import date as dt_date

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TelecomCoutFinancier(models.Model):
    _name = 'telecom.cout.financier'
    _description = 'Cout financier projet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'description'

    # -- Identification --
    date = fields.Date(
        string='Date', required=True,
        default=fields.Date.today, tracking=True,
    )
    project_id = fields.Many2one(
        'project.project', string='Projet',
        required=True, tracking=True, index=True,
        ondelete='restrict',
    )
    lot_id = fields.Many2one(
        'telecom.lot', string='Lot',
        tracking=True,
        domain="[('project_id', '=', project_id)]",
        ondelete='restrict',
    )
    financing_type = fields.Selection([
        ('credit_bancaire', 'Credit bancaire'),
        ('leasing', 'Leasing'),
        ('caution_provisoire', 'Caution provisoire'),
        ('caution_definitive', 'Caution definitive'),
        ('avance_client', 'Avance client'),
        ('escompte', 'Escompte'),
        ('autre', 'Autre'),
    ], string='Type de financement', required=True,
       default='credit_bancaire', tracking=True,
    )
    description = fields.Char(
        string='Description', required=True,
    )

    # -- Contract link --
    contract_id = fields.Many2one(
        'telecom.contract', string='Contrat',
        tracking=True, ondelete='set null',
    )

    # -- Amount --
    montant = fields.Monetary(
        string='Montant principal', required=True,
        currency_field='currency_id', tracking=True,
    )
    currency_id = fields.Many2one(
        'res.currency', string='Devise', required=True,
        default=lambda self: (
            self.env.ref('base.MAD', raise_if_not_found=False)
            or self.env['res.currency'].search([('name', '=', 'MAD')], limit=1)
            or self.env.company.currency_id
        ),
    )
    taux_interet = fields.Float(
        string='Taux interet (%)', digits=(5, 2),
        help='Taux annuel en pourcentage.',
    )

    # -- Duration --
    date_debut = fields.Date(string='Date debut')
    date_fin = fields.Date(string='Date fin')

    # -- Computed interest --
    montant_interets = fields.Monetary(
        string='Montant des interets',
        compute='_compute_montant_interets', store=True,
        currency_field='currency_id',
    )

    # -- Link to cost entry --
    cost_entry_id = fields.Many2one(
        'telecom.cost.entry', string='Ecriture de cout',
        readonly=True, ondelete='set null', copy=False,
    )

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
        required=True, index=True,
    )

    # -- Computed --
    @api.depends('montant', 'taux_interet', 'date_debut', 'date_fin')
    def _compute_montant_interets(self):
        for rec in self:
            if rec.montant and rec.taux_interet and rec.date_debut and rec.date_fin:
                # Duration in years (approximate: days / 365)
                d_start = rec.date_debut
                d_end = rec.date_fin
                if d_end > d_start:
                    duration_days = (d_end - d_start).days
                    duration_years = duration_days / 365.0
                    rec.montant_interets = rec.montant * (rec.taux_interet / 100.0) * duration_years
                else:
                    rec.montant_interets = 0.0
            else:
                rec.montant_interets = 0.0

    # -- Constraints --
    @api.constrains('montant')
    def _check_montant(self):
        for rec in self:
            if rec.montant <= 0:
                raise ValidationError(
                    _('Le montant doit etre strictement positif.')
                )

    @api.constrains('date_debut', 'date_fin')
    def _check_dates(self):
        for rec in self:
            if rec.date_debut and rec.date_fin and rec.date_fin < rec.date_debut:
                raise ValidationError(
                    _('La date de fin doit etre posterieure a la date de debut.')
                )

    # -- Auto-create cost entry on create --
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._create_cost_entry()
        return records

    def _create_cost_entry(self):
        """Create a telecom.cost.entry linked to this financial cost."""
        CostEntry = self.env['telecom.cost.entry']
        # Find the financier cost type
        cost_type = self.env.ref(
            'telecom_cost.cost_type_financier', raise_if_not_found=False
        )
        if not cost_type:
            cost_type = self.env['telecom.cost.type'].search(
                [('category', '=', 'financier')], limit=1,
            )
        # Use total including interest if available
        total = self.montant + (self.montant_interets or 0.0)
        vals = {
            'date': self.date,
            'cost_type_id': cost_type.id if cost_type else False,
            'description': _('Cout financier — %s') % self.description,
            'project_id': self.project_id.id,
            'lot_id': self.lot_id.id if self.lot_id else False,
            'montant': total,
            'currency_id': self.currency_id.id,
            'source': 'manual',
            'company_id': self.company_id.id,
        }
        entry = CostEntry.create(vals)
        self.cost_entry_id = entry.id
