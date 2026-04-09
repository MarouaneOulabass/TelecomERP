# -*- coding: utf-8 -*-
"""
project.project — telecom extension
=====================================
Adds telecom-specific fields to the native Odoo project.project model:
- Project type (FTTH, 4G, 5G, maintenance, etc.)
- Operator client link
- Lots and sites structure (One2many)
- PV de réception
- Budget tracking
- Computed KPIs: sites_total, sites_livres, taux_avancement
"""

from odoo import api, fields, models


class ProjectProject(models.Model):
    """Inherit project.project to add telecom deployment fields."""

    _inherit = 'project.project'

    # ------------------------------------------------------------------
    # Telecom classification
    # ------------------------------------------------------------------

    project_type = fields.Selection(
        selection=[
            ('deploiement_ftth', 'Déploiement FTTH'),
            ('rollout_4g', 'Rollout 4G'),
            ('rollout_5g', 'Rollout 5G'),
            ('maintenance_preventive', 'Maintenance préventive'),
            ('courant_fort', 'Courant fort'),
            ('courant_faible', 'Courant faible'),
            ('autre', 'Autre'),
        ],
        string='Type de projet',
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Operator (client)
    # ------------------------------------------------------------------

    operateur_id = fields.Many2one(
        'res.partner',
        string='Opérateur client',
        domain=[('partner_type', '=', 'operator')],
        tracking=True,
        help="Opérateur télécom client pour lequel le projet est réalisé",
    )

    # ------------------------------------------------------------------
    # Telecom sub-structures
    # ------------------------------------------------------------------

    lot_ids = fields.One2many(
        'telecom.lot',
        'project_id',
        string='Lots du projet',
    )
    project_site_ids = fields.One2many(
        'telecom.project.site',
        'project_id',
        string='Sites du projet',
    )
    pv_reception_ids = fields.One2many(
        'telecom.pv.reception',
        'project_id',
        string='PV de réception',
    )

    # ------------------------------------------------------------------
    # Budget
    # ------------------------------------------------------------------

    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self: self.env.ref('base.MAD', raise_if_not_found=False)
                            or self.env.ref('base.EUR'),
    )
    budget_total = fields.Monetary(
        string='Budget total (MAD)',
        currency_field='currency_id',
        tracking=True,
    )
    cout_reel = fields.Monetary(
        string='Coût réel (MAD)',
        currency_field='currency_id',
        compute='_compute_cout_reel',
        store=True,
        help="Somme des coûts réels enregistrés (placeholder — sera enrichi par les modules comptables)",
    )

    # ------------------------------------------------------------------
    # Planning dates
    # ------------------------------------------------------------------

    date_debut_prevu = fields.Date(
        string='Date de début prévue',
        tracking=True,
    )
    date_fin_prevu = fields.Date(
        string='Date de fin prévue',
        tracking=True,
    )

    # ------------------------------------------------------------------
    # KPI counters — computed
    # ------------------------------------------------------------------

    sites_total = fields.Integer(
        string='Nb sites total',
        compute='_compute_sites_stats',
        store=True,
    )
    sites_livres = fields.Integer(
        string='Nb sites livrés',
        compute='_compute_sites_stats',
        store=True,
    )
    taux_avancement = fields.Float(
        string='Taux d\'avancement (%)',
        compute='_compute_sites_stats',
        store=True,
        digits=(5, 2),
    )
    lot_count = fields.Integer(
        string='Nb lots',
        compute='_compute_lot_count',
    )
    pv_count = fields.Integer(
        string='Nb PV',
        compute='_compute_pv_count',
    )

    # ------------------------------------------------------------------
    # Computed methods
    # ------------------------------------------------------------------

    @api.depends('project_site_ids', 'project_site_ids.state')
    def _compute_sites_stats(self):
        """Compute KPIs from project sites: total, delivered, advancement rate."""
        for project in self:
            total = len(project.project_site_ids)
            livres = len(
                project.project_site_ids.filtered(lambda s: s.state == 'livre')
            )
            project.sites_total = total
            project.sites_livres = livres
            project.taux_avancement = (livres / total * 100.0) if total else 0.0

    @api.depends('pv_reception_ids')
    def _compute_cout_reel(self):
        """
        Placeholder compute for actual cost.
        Will be extended by accounting/stock integration modules.
        """
        for project in self:
            project.cout_reel = 0.0

    def _compute_lot_count(self):
        """Count lots linked to this project."""
        for project in self:
            project.lot_count = len(project.lot_ids)

    def _compute_pv_count(self):
        """Count PV de réception linked to this project."""
        for project in self:
            project.pv_count = len(project.pv_reception_ids)

    # ------------------------------------------------------------------
    # Smart button actions
    # ------------------------------------------------------------------

    def action_view_lots(self):
        """Open the list of lots for this project."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lots',
            'res_model': 'telecom.lot',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_project_sites(self):
        """Open the list of project sites."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sites du projet',
            'res_model': 'telecom.project.site',
            'view_mode': 'list,kanban,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_pv_reception(self):
        """Open the list of PV de réception for this project."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'PV de réception',
            'res_model': 'telecom.pv.reception',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }
