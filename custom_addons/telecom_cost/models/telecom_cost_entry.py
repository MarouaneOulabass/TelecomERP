# -*- coding: utf-8 -*-
"""
telecom.cost.entry — Saisie de coût rattachée à un projet
===========================================================
Règle non-négociable : tout coût doit être rattaché à un Projet + Lot.
La tâche est optionnelle mais signalée comme "à rattacher" dans le cockpit.
"""
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TelecomCostEntry(models.Model):
    _name = 'telecom.cost.entry'
    _description = 'Saisie de coût projet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'display_name'

    # -- Identification --
    display_name = fields.Char(compute='_compute_display_name', store=True)
    date = fields.Date(
        string='Date', required=True, default=fields.Date.today,
        tracking=True, index=True,
    )
    cost_type_id = fields.Many2one(
        'telecom.cost.type', string='Type de coût',
        required=True, tracking=True, index=True,
    )
    category = fields.Selection(
        related='cost_type_id.category', store=True, readonly=True,
    )
    description = fields.Char(string='Description', required=True)

    # -- Rattachement obligatoire --
    project_id = fields.Many2one(
        'project.project', string='Projet',
        required=True, tracking=True, index=True,
        ondelete='restrict',
    )
    lot_id = fields.Many2one(
        'telecom.lot', string='Lot',
        required=True, tracking=True, index=True,
        domain="[('project_id', '=', project_id)]",
        ondelete='restrict',
    )
    task_id = fields.Many2one(
        'project.task', string='Tâche (optionnelle)',
        domain="[('project_id', '=', project_id)]",
        tracking=True, ondelete='set null',
    )
    task_missing = fields.Boolean(
        string='Tâche non rattachée',
        compute='_compute_task_missing', store=True,
        help='True si le coût n\'est pas rattaché à une tâche spécifique.',
    )

    # -- Montant --
    montant = fields.Monetary(
        string='Montant HT', required=True,
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

    # -- Source --
    source = fields.Selection([
        ('manual', 'Saisie manuelle'),
        ('timesheet', 'Pointage chantier'),
        ('invoice', 'Facture fournisseur'),
        ('fuel', 'Plein carburant'),
        ('payroll', 'Bulletin de paie'),
        ('import', 'Import fichier'),
    ], string='Source', default='manual', required=True)

    # -- Justificatif --
    justificatif = fields.Binary(string='Justificatif', attachment=True)
    justificatif_filename = fields.Char(string='Nom fichier')

    # -- Validation --
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('validated', 'Validé'),
    ], string='État', default='draft', tracking=True, index=True)

    # -- Context --
    employee_id = fields.Many2one(
        'hr.employee', string='Employé concerné',
        tracking=True,
    )
    vehicle_id = fields.Many2one(
        'telecom.vehicle', string='Véhicule',
        tracking=True,
    )
    site_id = fields.Many2one(
        'telecom.site', string='Site',
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner', string='Fournisseur / Sous-traitant',
        tracking=True,
    )

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
        required=True, index=True,
    )

    # -- Computed --
    @api.depends('date', 'cost_type_id', 'montant', 'project_id')
    def _compute_display_name(self):
        for rec in self:
            parts = []
            if rec.date:
                parts.append(str(rec.date))
            if rec.cost_type_id:
                parts.append(rec.cost_type_id.name)
            if rec.montant:
                parts.append(f'{rec.montant:,.0f} MAD')
            rec.display_name = ' — '.join(parts) or _('Nouveau coût')

    @api.depends('task_id')
    def _compute_task_missing(self):
        for rec in self:
            rec.task_missing = not rec.task_id

    # -- Constraints --
    @api.constrains('montant')
    def _check_montant(self):
        for rec in self:
            if rec.montant <= 0:
                raise ValidationError(_('Le montant doit être strictement positif.'))

    # -- Workflow --
    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'

    def action_validate(self):
        for rec in self:
            rec.state = 'validated'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'
