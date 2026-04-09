# -*- coding: utf-8 -*-
"""
telecom.bpu.ligne — BPU (Bordereau de Prix Unitaires) line model.

Each line belongs to a telecom.ao (Appel d'Offres) and describes
a unit-priced work item in the commercial pricing grid.
"""

from odoo import api, fields, models


class TelecomBpuLigne(models.Model):
    """One line item in a Bordereau de Prix Unitaires (BPU)."""

    _name = 'telecom.bpu.ligne'
    _description = 'Ligne BPU'
    _order = 'ao_id, sequence, id'

    # ------------------------------------------------------------------
    # Relational
    # ------------------------------------------------------------------
    ao_id = fields.Many2one(
        comodel_name='telecom.ao',
        string="Appel d'Offres",
        required=True,
        ondelete='cascade',
        index=True,
    )

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------
    sequence = fields.Integer(
        string='Séq.',
        default=10,
    )
    code = fields.Char(
        string='Code poste',
        size=32,
    )
    section = fields.Char(
        string='Section / Rubrique',
    )
    designation = fields.Char(
        string='Désignation',
        required=True,
    )

    # ------------------------------------------------------------------
    # Quantities and pricing
    # ------------------------------------------------------------------
    unite = fields.Char(
        string='Unité',
        required=True,
        help="Ex : m, u, forfait, km, ml…",
    )
    quantite = fields.Float(
        string='Quantité',
        required=True,
        default=1.0,
        digits=(12, 3),
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Devise',
        related='ao_id.currency_id',
        store=True,
        readonly=True,
    )
    prix_unitaire = fields.Monetary(
        string='Prix unitaire HT',
        currency_field='currency_id',
        default=0.0,
    )
    montant_ht = fields.Monetary(
        string='Montant HT',
        currency_field='currency_id',
        compute='_compute_montant_ht',
        store=True,
        readonly=True,
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
    @api.depends('quantite', 'prix_unitaire')
    def _compute_montant_ht(self):
        """Calculate line total: quantity × unit price."""
        for line in self:
            line.montant_ht = line.quantite * line.prix_unitaire
