# -*- coding: utf-8 -*-
"""
telecom.pv.reception
====================
Procès-Verbal de Réception (PV) — official document certifying completion
of telecom infrastructure works on a given site.

Two PV types:
- partiel  : partial/intermediate reception (reservations allowed)
- definitif: final acceptance — when approved, sets the linked project site
             state to 'livre' (delivered).

Workflow: draft → signe → approuve
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TelecomPvReception(models.Model):
    """
    Procès-Verbal de Réception télécom.

    Formalise l'acceptation des travaux par le représentant du client opérateur.
    Un PV définitif approuvé déclenche automatiquement le passage du site
    de projet à l'état 'Livré'.
    """

    _name = 'telecom.pv.reception'
    _description = 'Procès-Verbal de Réception télécom'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_pv desc, name desc'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Auto-generated reference
    # ------------------------------------------------------------------

    name = fields.Char(
        string='N° PV',
        compute='_compute_name',
        store=True,
        copy=False,
        readonly=True,
        tracking=True,
    )
    sequence_number = fields.Char(
        string='Numéro de séquence',
        copy=False,
        readonly=True,
        help="Numéro généré par la séquence ir.sequence (PV/AAAA/MM/XXXX)",
    )

    # ------------------------------------------------------------------
    # PV classification
    # ------------------------------------------------------------------

    pv_type = fields.Selection(
        selection=[
            ('partiel', 'Réception partielle'),
            ('definitif', 'Réception définitive'),
        ],
        string='Type de PV',
        required=True,
        default='partiel',
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Project / site links
    # ------------------------------------------------------------------

    project_id = fields.Many2one(
        'project.project',
        string='Projet',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
    )
    project_site_id = fields.Many2one(
        'telecom.project.site',
        string='Site de projet',
        ondelete='set null',
        index=True,
        tracking=True,
        domain="[('project_id', '=', project_id)]",
    )
    lot_id = fields.Many2one(
        'telecom.lot',
        string='Lot',
        ondelete='set null',
        tracking=True,
        domain="[('project_id', '=', project_id)]",
    )

    # ------------------------------------------------------------------
    # Date
    # ------------------------------------------------------------------

    date_pv = fields.Date(
        string='Date du PV',
        required=True,
        default=fields.Date.today,
        tracking=True,
    )
    date_signature = fields.Date(
        string='Date de signature',
        copy=False,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Signatories
    # ------------------------------------------------------------------

    redige_par = fields.Many2one(
        'hr.employee',
        string='Rédigé par',
        tracking=True,
        help="Collaborateur de l'entreprise ayant rédigé le PV",
    )
    representant_client = fields.Char(
        string='Représentant opérateur',
        help="Nom complet du représentant de l'opérateur client",
    )
    representant_client_fonction = fields.Char(
        string='Fonction',
        help="Titre / fonction du représentant client",
    )

    # ------------------------------------------------------------------
    # Travaux content
    # ------------------------------------------------------------------

    travaux_realises = fields.Text(
        string='Travaux réalisés',
        required=True,
        help="Description détaillée des travaux et prestations réalisés",
    )
    reserves = fields.Text(
        string='Réserves formulées',
        help="Réserves ou points à corriger formulés par le client (laisser vide si aucune)",
    )
    levee_reserves = fields.Text(
        string='Modalités de levée des réserves',
        help="Conditions et procédure pour la levée formelle des réserves",
    )
    delai_levee_reserves = fields.Integer(
        string='Délai de levée des réserves (jours)',
        default=0,
        help="Délai contractuel accordé pour lever les réserves",
    )

    # ------------------------------------------------------------------
    # Workflow state
    # ------------------------------------------------------------------

    state = fields.Selection(
        selection=[
            ('draft', 'Brouillon'),
            ('signe', 'Signé'),
            ('approuve', 'Approuvé'),
        ],
        string='État',
        default='draft',
        required=True,
        copy=False,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Electronic signatures
    # ------------------------------------------------------------------

    signature_entreprise = fields.Binary(
        string='Signature entreprise',
        attachment=True,
        help="Signature électronique du représentant de l'entreprise",
    )
    signature_client = fields.Binary(
        string='Signature client',
        attachment=True,
        help="Signature électronique du représentant de l'opérateur",
    )

    # ------------------------------------------------------------------
    # Attached documents
    # ------------------------------------------------------------------

    document_ids = fields.Many2many(
        'ir.attachment',
        'telecom_pv_attachment_rel',
        'pv_id',
        'attachment_id',
        string='Documents joints',
        help="Plans, photos, mesures et tout document probatoire joint au PV",
    )

    # ------------------------------------------------------------------
    # Company
    # ------------------------------------------------------------------

    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Computed name
    # ------------------------------------------------------------------

    @api.depends('sequence_number', 'pv_type', 'date_pv')
    def _compute_name(self):
        """
        Build the display name from the sequence number.
        Falls back to a human-readable draft label when not yet sequenced.
        """
        type_labels = {'partiel': 'PV-PARTIEL', 'definitif': 'PV-DEFINITIF'}
        for rec in self:
            if rec.sequence_number:
                rec.name = rec.sequence_number
            elif rec.date_pv and rec.pv_type:
                rec.name = f"[BROUILLON] {type_labels.get(rec.pv_type, 'PV')} — {rec.date_pv}"
            else:
                rec.name = 'Nouveau PV'

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """Assign sequence number on creation."""
        for vals in vals_list:
            if not vals.get('sequence_number'):
                vals['sequence_number'] = self.env['ir.sequence'].next_by_code(
                    'telecom.pv.reception'
                ) or 'PV/NEW'
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------

    def action_signer(self):
        """
        Transition draft → signe.
        Both electronic signatures must be present before signing.
        """
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    _("Seuls les PV en brouillon peuvent être signés.")
                )
            if not rec.signature_entreprise:
                raise UserError(
                    _("La signature de l'entreprise est requise avant de signer le PV.")
                )
            if not rec.signature_client:
                raise UserError(
                    _("La signature du client est requise avant de signer le PV.")
                )
        self.write({
            'state': 'signe',
            'date_signature': fields.Date.today(),
        })

    def action_approuver(self):
        """
        Transition signe → approuve.
        For a PV définitif, the linked project site is set to 'livre'.
        """
        for rec in self:
            if rec.state != 'signe':
                raise UserError(
                    _("Seuls les PV signés peuvent être approuvés.")
                )
        for rec in self:
            rec.state = 'approuve'
            # If definitif PV approved → mark project site as delivered
            if rec.pv_type == 'definitif' and rec.project_site_id:
                rec.project_site_id.write({
                    'state': 'livre',
                    'date_livraison_reel': rec.date_pv,
                })

    def action_reset_draft(self):
        """Revert an approved or signed PV back to draft (admin only)."""
        admin_group = self.env.ref(
            'telecom_base.group_telecom_admin', raise_if_not_found=False
        )
        if admin_group and admin_group not in self.env.user.groups_id:
            raise UserError(
                _("Seul un administrateur TelecomERP peut remettre un PV en brouillon.")
            )
        self.write({'state': 'draft'})

    def action_print_pv(self):
        """Trigger the QWeb PDF report for this PV."""
        self.ensure_one()
        return self.env.ref(
            'telecom_project.action_report_telecom_pv'
        ).report_action(self)
