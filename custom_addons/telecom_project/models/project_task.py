# -*- coding: utf-8 -*-
"""
project.task — telecom extension
==================================
Adds telecom-specific fields to native Odoo project.task:
- Link to a project site (telecom.project.site)
- Link to an intervention (telecom.intervention)
- Task category for telecom work type classification
"""

from odoo import fields, models


class ProjectTask(models.Model):
    """Inherit project.task to add telecom deployment context."""

    _inherit = 'project.task'

    # ------------------------------------------------------------------
    # Telecom context
    # ------------------------------------------------------------------

    project_site_id = fields.Many2one(
        'telecom.project.site',
        string='Site de projet',
        domain="[('project_id', '=', project_id)]",
        index=True,
        tracking=True,
        help="Site de projet auquel cette tâche est rattachée",
    )
    intervention_id = fields.Many2one(
        'telecom.intervention',
        string='Bon d\'Intervention',
        ondelete='set null',
        index=True,
        tracking=True,
        help="Bon d'intervention terrain associé à cette tâche",
    )
    task_telecom_type = fields.Selection(
        selection=[
            ('etude', 'Étude / Conception'),
            ('autorisation', 'Gestion autorisation'),
            ('travaux', 'Travaux terrain'),
            ('recette', 'Recette / Tests'),
            ('admin', 'Administratif'),
            ('autre', 'Autre'),
        ],
        string='Catégorie télécom',
        help="Type de tâche dans le contexte d'un projet télécom",
    )
