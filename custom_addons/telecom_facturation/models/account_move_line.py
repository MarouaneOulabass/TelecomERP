# -*- coding: utf-8 -*-
"""Extend account.move.line with telecom-specific fields."""

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    """Add telecom references (project) to invoice lines.

    Soft-dependency fields (site, lot, situation) are NOT declared here
    because their comodels (telecom.site, telecom.lot, telecom.situation)
    live in optional modules. Those modules should extend account.move.line
    themselves when installed.
    """

    _inherit = 'account.move.line'

    telecom_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Projet',
        help="Projet télécom lié à cette ligne de facture.",
    )
