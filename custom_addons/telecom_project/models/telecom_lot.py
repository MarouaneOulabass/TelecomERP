# -*- coding: utf-8 -*-
"""
telecom.lot
===========
Lot — grouping of project sites within a telecom infrastructure project.

A project can be split into several lots (e.g., geographical zones or work
packages). Each lot is supervised by a chef de lot and contains a set of
telecom.project.site records.
"""

from odoo import api, fields, models


class TelecomLot(models.Model):
    """
    Lot (groupement de sites) d'un projet télécom.

    Permet de subdiviser un grand projet (ex: déploiement FTTH national)
    en zones géographiques ou lots contractuels distincts, chacun avec
    son propre responsable et son planning.
    """

    _name = 'telecom.lot'
    _description = 'Lot de projet télécom'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'project_id, code, name'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------

    name = fields.Char(
        string='Nom du lot',
        required=True,
        tracking=True,
        help="Ex : Lot 1 — Grand Casablanca",
    )
    code = fields.Char(
        string='Code',
        size=20,
        tracking=True,
        help="Code court du lot (ex : L01)",
    )
    description = fields.Text(
        string='Description',
    )

    # ------------------------------------------------------------------
    # Project link
    # ------------------------------------------------------------------

    project_id = fields.Many2one(
        'project.project',
        string='Projet',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Responsibility
    # ------------------------------------------------------------------

    chef_lot_id = fields.Many2one(
        'hr.employee',
        string='Responsable du lot',
        tracking=True,
        help="Chef de lot responsable de la coordination terrain",
    )

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------

    date_debut = fields.Date(
        string='Date de début',
        tracking=True,
    )
    date_fin_prevu = fields.Date(
        string='Date de fin prévue',
        tracking=True,
    )
    date_fin_reel = fields.Date(
        string='Date de fin réelle',
        tracking=True,
    )

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    state = fields.Selection(
        selection=[
            ('en_cours', 'En cours'),
            ('livre', 'Livré'),
            ('suspendu', 'Suspendu'),
        ],
        string='État',
        default='en_cours',
        required=True,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Sites
    # ------------------------------------------------------------------

    project_site_ids = fields.One2many(
        'telecom.project.site',
        'lot_id',
        string='Sites du lot',
    )

    # ------------------------------------------------------------------
    # KPIs — computed
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

    # ------------------------------------------------------------------
    # Company
    # ------------------------------------------------------------------

    company_id = fields.Many2one(
        'res.company',
        string='Société',
        related='project_id.company_id',
        store=True,
        readonly=True,
    )

    # ------------------------------------------------------------------
    # SQL constraints
    # ------------------------------------------------------------------

    _sql_constraints = [
        (
            'code_project_uniq',
            'UNIQUE(code, project_id)',
            'Ce code de lot est déjà utilisé dans ce projet.',
        ),
    ]

    # ------------------------------------------------------------------
    # Computed methods
    # ------------------------------------------------------------------

    @api.depends('project_site_ids', 'project_site_ids.state')
    def _compute_sites_stats(self):
        """Compute total/delivered site counts and advancement rate for each lot."""
        for lot in self:
            total = len(lot.project_site_ids)
            livres = len(lot.project_site_ids.filtered(lambda s: s.state == 'livre'))
            lot.sites_total = total
            lot.sites_livres = livres
            lot.taux_avancement = (livres / total * 100.0) if total else 0.0

    # ------------------------------------------------------------------
    # Business actions
    # ------------------------------------------------------------------

    def action_set_livre(self):
        """Mark the lot as delivered."""
        self.write({'state': 'livre'})

    def action_set_suspendu(self):
        """Suspend the lot."""
        self.write({'state': 'suspendu'})

    def action_set_en_cours(self):
        """Resume the lot."""
        self.write({'state': 'en_cours'})

    def action_view_sites(self):
        """Smart-button action: open the list of sites belonging to this lot."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sites du lot',
            'res_model': 'telecom.project.site',
            'view_mode': 'list,kanban,form',
            'domain': [('lot_id', '=', self.id)],
            'context': {
                'default_lot_id': self.id,
                'default_project_id': self.project_id.id,
            },
        }
