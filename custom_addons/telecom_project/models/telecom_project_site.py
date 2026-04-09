# -*- coding: utf-8 -*-
"""
telecom.project.site
====================
Junction model linking a project (and optionally a lot) to a physical
telecom site (telecom.site). Tracks the deployment state and dates for
each site within its project context.

One physical site can participate in multiple projects (different operators,
different work packages) but within a single project it must appear only once.
"""

from odoo import api, fields, models


class TelecomProjectSite(models.Model):
    """
    Lien Projet–Site (et optionnellement Lot–Site).

    Chaque enregistrement représente l'engagement d'un site physique
    dans un projet donné : état d'avancement, responsable terrain,
    dates prévues/réelles et PV de réception associés.
    """

    _name = 'telecom.project.site'
    _description = 'Site de projet télécom'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'project_id, lot_id, site_id'
    _rec_name = 'display_name'

    # ------------------------------------------------------------------
    # Core links
    # ------------------------------------------------------------------

    project_id = fields.Many2one(
        'project.project',
        string='Projet',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    lot_id = fields.Many2one(
        'telecom.lot',
        string='Lot',
        ondelete='set null',
        index=True,
        tracking=True,
        domain="[('project_id', '=', project_id)]",
        help="Lot auquel ce site est rattaché (optionnel)",
    )
    site_id = fields.Many2one(
        'telecom.site',
        string='Site physique',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Responsibility
    # ------------------------------------------------------------------

    responsable_site_id = fields.Many2one(
        'hr.employee',
        string='Responsable terrain',
        tracking=True,
        help="Responsable terrain pour ce site dans le cadre de ce projet",
    )

    # ------------------------------------------------------------------
    # Deployment state
    # ------------------------------------------------------------------

    state = fields.Selection(
        selection=[
            ('prospection', 'Prospection'),
            ('etude', 'Étude technique'),
            ('autorisation', 'En cours d\'autorisation'),
            ('travaux_en_cours', 'Travaux en cours'),
            ('recette', 'Recette / Test'),
            ('livre', 'Livré'),
            ('suspendu', 'Suspendu'),
        ],
        string='État',
        default='prospection',
        required=True,
        tracking=True,
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
    date_livraison_reel = fields.Date(
        string='Date de livraison réelle',
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------

    notes_avancement = fields.Text(
        string='Notes d\'avancement',
    )

    # ------------------------------------------------------------------
    # PV de réception
    # ------------------------------------------------------------------

    pv_partiel_ids = fields.One2many(
        'telecom.pv.reception',
        'project_site_id',
        string='PV partiels',
        domain=[('pv_type', '=', 'partiel')],
    )
    pv_definitif_id = fields.Many2one(
        'telecom.pv.reception',
        string='PV définitif',
        domain="[('pv_type', '=', 'definitif'), ('project_site_id', '=', id)]",
        copy=False,
    )

    # ------------------------------------------------------------------
    # Related interventions (computed)
    # ------------------------------------------------------------------

    intervention_ids = fields.Many2many(
        'telecom.intervention',
        string='Interventions',
        compute='_compute_intervention_ids',
        help="Interventions réalisées sur ce site dans ce projet",
    )
    intervention_count = fields.Integer(
        string='Nb interventions',
        compute='_compute_intervention_ids',
    )

    # ------------------------------------------------------------------
    # Display name
    # ------------------------------------------------------------------

    display_name = fields.Char(
        string='Nom',
        compute='_compute_display_name',
        store=True,
    )

    # ------------------------------------------------------------------
    # Company (related for multi-company rules)
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
            'project_site_uniq',
            'UNIQUE(project_id, site_id)',
            'Ce site est déjà rattaché à ce projet.',
        ),
    ]

    # ------------------------------------------------------------------
    # Computed methods
    # ------------------------------------------------------------------

    @api.depends('project_id.name', 'site_id.name', 'site_id.code_interne')
    def _compute_display_name(self):
        """Build a readable display name: [code] site — project."""
        for rec in self:
            site_label = rec.site_id.code_interne or rec.site_id.name or ''
            project_label = rec.project_id.name or ''
            rec.display_name = f"[{site_label}] {project_label}" if project_label else site_label

    @api.depends('site_id')
    def _compute_intervention_ids(self):
        """Retrieve all interventions linked to this site."""
        for rec in self:
            if rec.site_id:
                interventions = self.env['telecom.intervention'].search(
                    [('site_id', '=', rec.site_id.id)]
                )
                rec.intervention_ids = interventions
                rec.intervention_count = len(interventions)
            else:
                rec.intervention_ids = self.env['telecom.intervention']
                rec.intervention_count = 0

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------

    def action_set_etude(self):
        self.write({'state': 'etude'})

    def action_set_autorisation(self):
        self.write({'state': 'autorisation'})

    def action_set_travaux(self):
        self.write({'state': 'travaux_en_cours'})

    def action_set_recette(self):
        self.write({'state': 'recette'})

    def action_set_livre(self):
        self.write({'state': 'livre'})

    def action_set_suspendu(self):
        self.write({'state': 'suspendu'})

    def action_view_interventions(self):
        """Smart-button action: open interventions on this site."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Interventions',
            'res_model': 'telecom.intervention',
            'view_mode': 'list,form',
            'domain': [('site_id', '=', self.site_id.id)],
            'context': {'default_site_id': self.site_id.id},
        }
