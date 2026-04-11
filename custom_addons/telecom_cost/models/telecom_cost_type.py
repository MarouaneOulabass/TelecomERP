# -*- coding: utf-8 -*-
from odoo import fields, models


class TelecomCostType(models.Model):
    """Taxonomy of cost types — configurable per tenant."""

    _name = 'telecom.cost.type'
    _description = 'Type de coût'
    _order = 'sequence, name'

    name = fields.Char(string='Type de coût', required=True)
    code = fields.Char(string='Code', size=10)
    category = fields.Selection([
        ('main_oeuvre', "Main d'oeuvre"),
        ('materiel', 'Matériel et fournitures'),
        ('sous_traitance', 'Sous-traitance'),
        ('carburant', 'Carburant et déplacements'),
        ('location', 'Location matériel / engins'),
        ('frais_generaux', 'Frais généraux'),
        ('financier', 'Frais financiers'),
        ('autre', 'Autre'),
    ], string='Catégorie', required=True, default='autre')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Ce type de coût existe déjà.'),
    ]
