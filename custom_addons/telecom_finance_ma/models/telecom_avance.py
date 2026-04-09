# -*- coding: utf-8 -*-
"""
telecom.avance.demarrage — Avance de démarrage
===============================================
Tracks advance payments made to contractors at the start of a project.

Moroccan regulation allows:
  - 10 % advance for works markets
  - 15 % advance for larger markets (by contract)

Advances are recovered progressively on each situation/décompte.
This model tracks the full repayment history through
telecom.avance.remboursement child lines.

Workflow: en_attente → verse → en_cours_remboursement → rembourse
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TelecomAvanceRemboursement(models.Model):
    """One repayment instalment against an advance payment."""

    _name = 'telecom.avance.remboursement'
    _description = 'Remboursement d\'avance de démarrage'
    _order = 'date desc, id desc'

    # ------------------------------------------------------------------
    # Parent
    # ------------------------------------------------------------------

    avance_id = fields.Many2one(
        comodel_name='telecom.avance.demarrage',
        string='Avance',
        required=True,
        ondelete='cascade',
        index=True,
    )

    # ------------------------------------------------------------------
    # Currency (propagated from parent)
    # ------------------------------------------------------------------

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Devise',
        related='avance_id.currency_id',
        store=True,
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------

    situation_id = fields.Many2one(
        comodel_name='telecom.situation',
        string='Situation imputée',
        help="Situation de travaux sur laquelle ce remboursement est imputé.",
    )

    # ------------------------------------------------------------------
    # Repayment data
    # ------------------------------------------------------------------

    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today,
    )
    montant = fields.Monetary(
        string='Montant remboursé',
        currency_field='currency_id',
    )
    notes = fields.Char(
        string='Notes',
    )


class TelecomAvanceDemarrage(models.Model):
    """
    Avance de démarrage — advance payment to contractor at project start.

    Tracks the full lifecycle: award → disbursement → progressive recovery.
    """

    _name = 'telecom.avance.demarrage'
    _description = 'Avance de démarrage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_versement desc, id desc'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Auto-generated reference
    # ------------------------------------------------------------------

    name = fields.Char(
        string='N° Avance',
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
    )

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------

    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Projet',
        required=True,
        tracking=True,
        index=True,
    )
    contract_id = fields.Many2one(
        comodel_name='telecom.contract',
        string='Contrat',
        required=True,
        tracking=True,
    )
    client_id = fields.Many2one(
        comodel_name='res.partner',
        string='Client / Maître d\'ouvrage',
        required=True,
        tracking=True,
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    # ------------------------------------------------------------------
    # Currency
    # ------------------------------------------------------------------

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Devise',
        required=True,
        default=lambda self: (
            self.env.ref('base.MAD', raise_if_not_found=False)
            or self.env['res.currency'].search([('name', '=', 'MAD')], limit=1)
        ),
    )

    # ------------------------------------------------------------------
    # Financial
    # ------------------------------------------------------------------

    montant_marche = fields.Monetary(
        string='Montant marché HT',
        currency_field='currency_id',
        tracking=True,
        help="Montant total HT du marché sur lequel l'avance est calculée.",
    )
    taux_avance = fields.Float(
        string='Taux avance (%)',
        default=10.0,
        digits=(5, 2),
        tracking=True,
        help="Taux de l'avance de démarrage (10 % ou 15 % selon le marché).",
    )
    montant_avance = fields.Monetary(
        string='Montant avance théorique',
        compute='_compute_montant_avance',
        store=True,
        currency_field='currency_id',
        help="Montant théorique = montant marché × taux avance / 100.",
    )

    # ------------------------------------------------------------------
    # Versement
    # ------------------------------------------------------------------

    date_versement = fields.Date(
        string='Date de versement',
        tracking=True,
        help="Date effective du versement de l'avance par le client.",
    )
    montant_verse = fields.Monetary(
        string='Montant versé',
        currency_field='currency_id',
        tracking=True,
        help="Montant réellement versé (peut différer du théorique).",
    )

    # ------------------------------------------------------------------
    # Remboursements
    # ------------------------------------------------------------------

    remboursement_ids = fields.One2many(
        comodel_name='telecom.avance.remboursement',
        inverse_name='avance_id',
        string='Remboursements',
        copy=True,
    )
    total_rembourse = fields.Monetary(
        string='Total remboursé',
        compute='_compute_remboursement',
        store=True,
        currency_field='currency_id',
    )
    solde_restant = fields.Monetary(
        string='Solde restant',
        compute='_compute_remboursement',
        store=True,
        currency_field='currency_id',
        help="Montant versé − total remboursé.",
    )

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    state = fields.Selection(
        selection=[
            ('en_attente', 'En attente de versement'),
            ('verse', 'Versée'),
            ('en_cours_remboursement', 'En cours de remboursement'),
            ('rembourse', 'Entièrement remboursée'),
        ],
        string='État',
        required=True,
        default='en_attente',
        copy=False,
        tracking=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    notes = fields.Text(string='Notes internes')

    # ------------------------------------------------------------------
    # Computed name
    # ------------------------------------------------------------------

    @api.depends('sequence_number')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.sequence_number or _('Nouvelle avance')

    # ------------------------------------------------------------------
    # Financial computations
    # ------------------------------------------------------------------

    @api.depends('montant_marche', 'taux_avance')
    def _compute_montant_avance(self):
        for rec in self:
            rec.montant_avance = rec.montant_marche * rec.taux_avance / 100.0

    @api.depends('remboursement_ids', 'remboursement_ids.montant', 'montant_verse')
    def _compute_remboursement(self):
        for rec in self:
            total = sum(rec.remboursement_ids.mapped('montant'))
            rec.total_rembourse = total
            rec.solde_restant = rec.montant_verse - total

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """Assign sequence number on creation."""
        for vals in vals_list:
            if not vals.get('sequence_number'):
                vals['sequence_number'] = (
                    self.env['ir.sequence'].next_by_code('telecom.avance')
                    or _('Nouveau')
                )
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------

    def action_marquer_versee(self):
        """Mark the advance as disbursed."""
        for rec in self:
            if rec.state != 'en_attente':
                raise UserError(
                    _("Seule une avance en attente peut être marquée versée.")
                )
            if not rec.montant_verse:
                raise UserError(
                    _("Veuillez renseigner le montant versé avant de valider.")
                )
            if not rec.date_versement:
                raise UserError(
                    _("Veuillez renseigner la date de versement.")
                )
        self.write({'state': 'verse'})

    def action_demarrer_remboursement(self):
        """Transition verse → en_cours_remboursement."""
        for rec in self:
            if rec.state != 'verse':
                raise UserError(
                    _("L'avance doit être versée pour débuter les remboursements.")
                )
        self.write({'state': 'en_cours_remboursement'})

    def action_marquer_rembourse(self):
        """Mark the advance as fully repaid."""
        for rec in self:
            if rec.solde_restant > 0.01:
                raise UserError(
                    _(
                        "Le solde restant (%(solde)s) n'est pas encore soldé.",
                        solde=rec.solde_restant,
                    )
                )
        self.write({'state': 'rembourse'})

    def action_reset_attente(self):
        """Admin: reset to en_attente."""
        admin_group = self.env.ref(
            'telecom_base.group_telecom_admin', raise_if_not_found=False
        )
        if admin_group and admin_group not in self.env.user.groups_id:
            raise UserError(
                _("Seul un administrateur TelecomERP peut réinitialiser une avance.")
            )
        self.write({'state': 'en_attente'})
