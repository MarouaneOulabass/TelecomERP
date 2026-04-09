# -*- coding: utf-8 -*-
"""
telecom_equipment_category
===========================
Hierarchical reference table for equipment categories.

Examples:
- Antennes > Antenne sectorielle 4G LTE
- Équipements radio > eNodeB 4G (LTE)
- Shelter & infrastructure > Groupe électrogène
"""

from odoo import api, fields, models


class TelecomEquipmentCategory(models.Model):
    """Equipment category with unlimited depth hierarchy."""

    _name = 'telecom.equipment.category'
    _description = "Catégorie d'équipement télécom"
    _order = 'complete_name'
    _rec_name = 'complete_name'
    _parent_store = True

    # ------------------------------------------------------------------
    # Fields
    # ------------------------------------------------------------------

    name = fields.Char(
        string='Catégorie',
        required=True,
    )
    complete_name = fields.Char(
        string='Nom complet',
        compute='_compute_complete_name',
        store=True,
        recursive=True,
    )
    code = fields.Char(
        string='Code',
        size=10,
    )
    parent_id = fields.Many2one(
        'telecom.equipment.category',
        string='Catégorie parente',
        ondelete='restrict',
        index=True,
    )
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many(
        'telecom.equipment.category',
        'parent_id',
        string='Sous-catégories',
    )
    description = fields.Text(
        string='Description',
    )
    active = fields.Boolean(
        default=True,
    )
    equipment_count = fields.Integer(
        string='Nb équipements',
        compute='_compute_equipment_count',
    )

    # ------------------------------------------------------------------
    # SQL constraints
    # ------------------------------------------------------------------

    _sql_constraints = [
        ('name_parent_uniq', 'UNIQUE(name, parent_id)',
         'Une catégorie avec ce nom existe déjà dans cette catégorie parente.'),
    ]

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        """Build full path: Parent / Child / Grandchild."""
        for cat in self:
            if cat.parent_id:
                cat.complete_name = f'{cat.parent_id.complete_name} / {cat.name}'
            else:
                cat.complete_name = cat.name

    def _compute_equipment_count(self):
        """Count equipment directly under each category."""
        Equipment = self.env['telecom.equipment']
        for cat in self:
            cat.equipment_count = Equipment.search_count(
                [('category_id', 'child_of', cat.id)]
            )

    # ------------------------------------------------------------------
    # Name search override for hierarchical display in dropdowns
    # ------------------------------------------------------------------

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            records = self.search(
                [('complete_name', operator, name)] + args, limit=limit
            )
        else:
            records = self.search(args, limit=limit)
        return [(r.id, r.complete_name) for r in records]

    def name_get(self):
        return [(r.id, r.complete_name) for r in self]
