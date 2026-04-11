# -*- coding: utf-8 -*-
"""
telecom.plein.carburant — Fuel fill-up tracking per vehicle and project
========================================================================
Each fill-up automatically creates a telecom.cost.entry with
cost_type = carburant for the associated project/lot.
"""
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TelecomPleinCarburant(models.Model):
    _name = 'telecom.plein.carburant'
    _description = 'Plein carburant'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'display_name'

    # -- Identification --
    display_name = fields.Char(
        compute='_compute_display_name', store=True,
    )
    date = fields.Date(
        string='Date', required=True,
        default=fields.Date.today, tracking=True,
    )
    vehicle_id = fields.Many2one(
        'telecom.vehicle', string='Vehicule',
        required=True, tracking=True, index=True,
        ondelete='restrict',
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Conducteur',
        tracking=True,
        help='Employe ayant effectue le plein.',
    )

    # -- Project allocation (mandatory) --
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

    # -- Fill-up details --
    station = fields.Char(
        string='Station-service',
        help='Nom ou enseigne de la station.',
    )
    litres = fields.Float(
        string='Litres', required=True, digits=(10, 2),
    )
    prix_litre = fields.Float(
        string='Prix / litre (MAD)', digits=(10, 3),
    )
    amount = fields.Monetary(
        string='Montant HT', compute='_compute_amount',
        store=True, currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency', string='Devise', required=True,
        default=lambda self: (
            self.env.ref('base.MAD', raise_if_not_found=False)
            or self.env['res.currency'].search([('name', '=', 'MAD')], limit=1)
            or self.env.company.currency_id
        ),
    )
    kilometrage = fields.Integer(
        string='Kilometrage',
        help='Releve compteur au moment du plein.',
    )

    # -- Attachments --
    justificatif = fields.Binary(
        string='Justificatif', attachment=True,
    )
    justificatif_filename = fields.Char(string='Nom fichier')

    notes = fields.Text(string='Notes')

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
    @api.depends('litres', 'prix_litre')
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.litres * rec.prix_litre

    @api.depends('date', 'vehicle_id', 'amount')
    def _compute_display_name(self):
        for rec in self:
            parts = []
            if rec.date:
                parts.append(str(rec.date))
            if rec.vehicle_id:
                parts.append(rec.vehicle_id.display_name or '')
            if rec.amount:
                parts.append(f'{rec.amount:,.0f} MAD')
            rec.display_name = ' — '.join(parts) or _('Nouveau plein')

    # -- Constraints --
    @api.constrains('litres')
    def _check_litres(self):
        for rec in self:
            if rec.litres <= 0:
                raise ValidationError(
                    _('Le nombre de litres doit etre strictement positif.')
                )

    @api.constrains('prix_litre')
    def _check_prix_litre(self):
        for rec in self:
            if rec.prix_litre < 0:
                raise ValidationError(
                    _('Le prix au litre ne peut pas etre negatif.')
                )

    # -- Auto-create cost entry on create --
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._create_cost_entry()
        return records

    def _create_cost_entry(self):
        """Create a telecom.cost.entry linked to this fill-up."""
        CostEntry = self.env['telecom.cost.entry']
        # Find the carburant cost type
        cost_type = self.env.ref(
            'telecom_cost.cost_type_carburant', raise_if_not_found=False
        )
        if not cost_type:
            cost_type = self.env['telecom.cost.type'].search(
                [('category', '=', 'carburant')], limit=1,
            )
        vals = {
            'date': self.date,
            'cost_type_id': cost_type.id if cost_type else False,
            'description': _('Plein carburant — %s') % (
                self.vehicle_id.display_name or ''
            ),
            'project_id': self.project_id.id,
            'lot_id': self.lot_id.id if self.lot_id else False,
            'amount': self.amount or 0.0,
            'currency_id': self.currency_id.id,
            'source': 'fuel',
            'vehicle_id': self.vehicle_id.id,
            'employee_id': self.employee_id.id if self.employee_id else False,
            'company_id': self.company_id.id,
        }
        entry = CostEntry.create(vals)
        self.cost_entry_id = entry.id
