# -*- coding: utf-8 -*-
"""
telecom_materiel_consomme
=========================
Tracks materials and equipment consumed during a field intervention.

A line can reference an Odoo product (stock item) or carry a free-text
designation for non-catalogued parts.  The stock_move_id field is a
placeholder for future automated stock movement generation.
"""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TelecomMaterielConsomme(models.Model):
    """
    Consumed material line for a Bon d'Intervention.

    Each line records a part or piece of equipment used on site,
    with optional product reference, serial number, and stock movement link.
    """

    _name = 'telecom.materiel.consomme'
    _description = 'Matériel consommé (intervention)'
    _order = 'intervention_id, id'
    _rec_name = 'designation'

    # ------------------------------------------------------------------
    # Relations
    # ------------------------------------------------------------------

    intervention_id = fields.Many2one(
        'telecom.intervention',
        string="Bon d'Intervention",
        required=True,
        ondelete='cascade',
        index=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Article (stock)',
        ondelete='restrict',
        help="Odoo product record — leave blank for non-catalogued parts",
    )

    # ------------------------------------------------------------------
    # Description
    # ------------------------------------------------------------------

    designation = fields.Char(
        string='Désignation',
        required=True,
        help="Free-text designation; auto-filled from product name when a product is selected",
    )
    quantite = fields.Float(
        string='Quantité',
        required=True,
        default=1.0,
        digits=(10, 3),
    )
    unite = fields.Char(
        string='Unité',
        default='unité',
    )

    # ------------------------------------------------------------------
    # Traceability
    # ------------------------------------------------------------------

    numero_serie = fields.Char(
        string='N° Série',
        help="Serial or asset number for tracked equipment",
    )
    stock_move_id = fields.Many2one(
        'stock.move',
        string='Mouvement de stock',
        copy=False,
        readonly=True,
        help="Stock move generated automatically (placeholder for future integration)",
    )
    notes = fields.Char(
        string='Notes',
    )

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Auto-fill designation and unit from the selected product."""
        if self.product_id:
            self.designation = self.product_id.name
            if self.product_id.uom_id:
                self.unite = self.product_id.uom_id.name

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains('quantite')
    def _check_quantite(self):
        for rec in self:
            if rec.quantite <= 0:
                raise ValidationError(
                    _("La quantité doit être strictement positive.")
                )
