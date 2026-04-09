# -*- coding: utf-8 -*-
"""
telecom_site_inherit
====================
Extends telecom.site with intervention-related computed fields.

Overrides the placeholder _compute_intervention_count defined in
telecom_site, adds last_intervention_date, and provides a smart-button
action to open interventions filtered by site.
"""

from odoo import api, fields, models


class TelecomSite(models.Model):
    """Extend telecom.site with real intervention statistics."""

    _inherit = 'telecom.site'

    # ------------------------------------------------------------------
    # Fields added / overridden
    # ------------------------------------------------------------------

    intervention_ids = fields.One2many(
        'telecom.intervention',
        'site_id',
        string='Interventions',
    )
    # Override the placeholder field defined in telecom_site with store=True
    intervention_count = fields.Integer(
        string='Nb interventions',
        compute='_compute_intervention_count',
        store=True,
    )
    last_intervention_date = fields.Datetime(
        string='Dernière intervention',
        compute='_compute_last_intervention',
        store=True,
        help="Date of the most recent completed intervention on this site",
    )

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------

    @api.depends('intervention_ids')
    def _compute_intervention_count(self):
        """Count all interventions linked to each site (any state)."""
        for site in self:
            site.intervention_count = len(site.intervention_ids)

    @api.depends('intervention_ids.date_fin_reel')
    def _compute_last_intervention(self):
        """Most recent date_fin_reel among finished interventions."""
        for site in self:
            finished = site.intervention_ids.filtered('date_fin_reel')
            if finished:
                site.last_intervention_date = max(
                    finished.mapped('date_fin_reel')
                )
            else:
                site.last_intervention_date = False

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_view_interventions(self):
        """Smart-button: open the list of interventions for this site."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Interventions — {self.name}',
            'res_model': 'telecom.intervention',
            'view_mode': 'list,form,kanban',
            'domain': [('site_id', '=', self.id)],
            'context': {
                'default_site_id': self.id,
                'default_operateur_id': (
                    self.operateur_ids[0].id if self.operateur_ids else False
                ),
            },
        }
