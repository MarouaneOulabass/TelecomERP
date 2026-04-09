# -*- coding: utf-8 -*-
"""
telecom_vehicle_entretien.py
============================
Maintenance record model for fleet vehicles.
Each record captures:
  - Type and date of the intervention
  - Odometer reading at the time
  - Garage/provider and cost
  - Next recommended service (km + date)
  - Scanned garage invoice (binary attachment)

When a record is saved it can optionally update the parent vehicle's
last-service fields via _update_vehicle_maintenance().
"""

from odoo import api, fields, models


class TelecomVehicleEntretien(models.Model):
    """A single maintenance event for a fleet vehicle."""

    _name = 'telecom.vehicle.entretien'
    _description = 'Entretien Véhicule'
    _order = 'date desc, id desc'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Core fields
    # ------------------------------------------------------------------

    vehicle_id = fields.Many2one(
        comodel_name='telecom.vehicle',
        string='Véhicule',
        required=True,
        ondelete='cascade',
        index=True,
    )

    name = fields.Char(
        string='Libellé',
        required=True,
        help="Description courte, ex : 'Vidange + filtres', 'Révision 80 000 km'",
    )

    entretien_type = fields.Selection(
        selection=[
            ('vidange', 'Vidange / Filtres'),
            ('revision', 'Révision périodique'),
            ('pneus', 'Remplacement pneumatiques'),
            ('freins', 'Freins'),
            ('courroie', 'Distribution / Courroie'),
            ('carrosserie', 'Carrosserie / Peinture'),
            ('electrique', 'Électrique / Batterie'),
            ('autre', 'Autre'),
        ],
        string="Type d'entretien",
        default='vidange',
    )

    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
    )

    kilometrage = fields.Integer(
        string='Kilométrage',
        help='Relevé kilométrique au moment de l\'entretien.',
    )

    garage = fields.Char(
        string='Garage / Prestataire',
    )

    # ------------------------------------------------------------------
    # Cost
    # ------------------------------------------------------------------

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Devise',
        default=lambda self: self._default_currency_mad(),
    )

    cout = fields.Monetary(
        string='Coût (MAD)',
        currency_field='currency_id',
    )

    @api.model
    def _default_currency_mad(self):
        """Return MAD currency, fallback to company currency."""
        mad = self.env['res.currency'].search([('name', '=', 'MAD')], limit=1)
        return mad or self.env.company.currency_id

    # ------------------------------------------------------------------
    # Description and next service
    # ------------------------------------------------------------------

    description = fields.Text(string='Description / Observations')

    prochain_entretien_km = fields.Integer(
        string='Prochain entretien (km recommandé)',
    )

    prochain_entretien_date = fields.Date(
        string='Prochain entretien (date recommandée)',
    )

    # ------------------------------------------------------------------
    # Invoice attachment
    # ------------------------------------------------------------------

    facture = fields.Binary(
        string='Facture garage (scan)',
        attachment=True,
    )

    facture_filename = fields.Char(string='Nom fichier facture')

    # ------------------------------------------------------------------
    # Related fields for convenience in views
    # ------------------------------------------------------------------

    immatriculation = fields.Char(
        related='vehicle_id.immatriculation',
        string='Immatriculation',
        store=False,
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Post-save: propagate data to parent vehicle
    # ------------------------------------------------------------------

    def _update_vehicle_maintenance(self):
        """
        After saving, update the vehicle's last-service fields if this
        record is the most recent one (by date or km).
        This keeps vehicle.date_dernier_entretien and km_dernier_entretien
        in sync without requiring manual input on the vehicle form.
        """
        for rec in self:
            vehicle = rec.vehicle_id
            # Only update if this entry is the most recent
            latest = self.search(
                [('vehicle_id', '=', vehicle.id)],
                order='date desc, kilometrage desc',
                limit=1,
            )
            if latest.id == rec.id:
                vals = {}
                if rec.date:
                    vals['date_dernier_entretien'] = rec.date
                if rec.kilometrage:
                    vals['km_dernier_entretien'] = rec.kilometrage
                if rec.prochain_entretien_date:
                    vals['date_prochain_entretien'] = rec.prochain_entretien_date
                if vals:
                    vehicle.write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._update_vehicle_maintenance()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._update_vehicle_maintenance()
        return res
