# -*- coding: utf-8 -*-
"""
telecom.situation — Situation de travaux
========================================
Moroccan public-works progress-billing document (situation d'avancement).

Each situation covers a period of works and bills the client for the
incremental progress achieved since the previous situation.  The net
amount takes into account:

  - TVA (default 20 %)
  - Retenue de garantie (RG, default 10 %)
  - Remboursement partiel de l'avance de démarrage

Workflow: draft → soumis → approuve → facture → paye

The 60-day payment deadline is tracked per loi 69-21 (délai de paiement
légal pour les marchés publics de travaux).
"""

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TelecomSituationLine(models.Model):
    """Detail line of a situation, broken down by lot and/or site."""

    _name = 'telecom.situation.line'
    _description = 'Ligne de situation de travaux'
    _order = 'sequence, id'

    # ------------------------------------------------------------------
    # Parent link
    # ------------------------------------------------------------------

    situation_id = fields.Many2one(
        comodel_name='telecom.situation',
        string='Situation',
        required=True,
        ondelete='cascade',
        index=True,
    )

    sequence = fields.Integer(
        string='Séq.',
        default=10,
    )

    # ------------------------------------------------------------------
    # Grouping
    # ------------------------------------------------------------------

    lot_id = fields.Many2one(
        comodel_name='telecom.lot',
        string='Lot',
    )
    site_id = fields.Many2one(
        comodel_name='telecom.site',
        string='Site',
    )
    description = fields.Char(
        string='Description',
        required=True,
    )

    # ------------------------------------------------------------------
    # Currency (propagated from parent)
    # ------------------------------------------------------------------

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Devise',
        related='situation_id.currency_id',
        store=True,
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Financial
    # ------------------------------------------------------------------

    montant_marche_lot = fields.Monetary(
        string='Montant marché lot HT',
        currency_field='currency_id',
    )
    taux_avancement_cumul = fields.Float(
        string='Avancement cumulé (%)',
        digits=(5, 2),
    )
    montant_cumul = fields.Monetary(
        string='Montant cumulé HT',
        compute='_compute_montant_cumul',
        store=True,
        currency_field='currency_id',
    )
    montant_precedent = fields.Monetary(
        string='Situation précédente HT',
        currency_field='currency_id',
        help="Montant cumulé réglé lors des situations précédentes pour ce lot.",
    )
    montant_periode = fields.Monetary(
        string='Montant période HT',
        compute='_compute_montant_periode',
        store=True,
        currency_field='currency_id',
        help="Montant de cette situation pour ce lot = cumulé - précédent.",
    )

    # ------------------------------------------------------------------
    # Computed methods
    # ------------------------------------------------------------------

    @api.depends('montant_marche_lot', 'taux_avancement_cumul')
    def _compute_montant_cumul(self):
        for line in self:
            line.montant_cumul = (
                line.montant_marche_lot * line.taux_avancement_cumul / 100.0
            )

    @api.depends('montant_cumul', 'montant_precedent')
    def _compute_montant_periode(self):
        for line in self:
            line.montant_periode = line.montant_cumul - line.montant_precedent


class TelecomSituation(models.Model):
    """
    Situation de travaux — periodic progress-billing document.

    Represents one billing period for a public-works project.
    Linked to a project, a contract, and optionally generates
    a customer invoice in Odoo accounting.
    """

    _name = 'telecom.situation'
    _description = 'Situation de travaux'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_situation desc, numero_situation desc'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Auto-generated reference
    # ------------------------------------------------------------------

    name = fields.Char(
        string='N° Situation',
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
        tracking=True,
        domain="[('partenaire_id', '=', client_id)]",
    )
    client_id = fields.Many2one(
        comodel_name='res.partner',
        string='Client / Opérateur',
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
    # Period
    # ------------------------------------------------------------------

    numero_situation = fields.Integer(
        string='N° Situation',
        required=True,
        default=1,
        tracking=True,
    )
    date_situation = fields.Date(
        string='Date de situation',
        required=True,
        default=fields.Date.today,
        tracking=True,
    )
    periode_du = fields.Date(
        string='Période du',
        required=True,
        tracking=True,
    )
    periode_au = fields.Date(
        string='Période au',
        required=True,
        tracking=True,
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
    # Financial — base
    # ------------------------------------------------------------------

    montant_marche_ht = fields.Monetary(
        string='Montant marché HT',
        currency_field='currency_id',
        tracking=True,
        help="Montant total du marché hors taxes.",
    )
    taux_avancement_cumul = fields.Float(
        string='Avancement cumulé (%)',
        digits=(5, 2),
        tracking=True,
        help="Pourcentage d'avancement cumulé à la date de cette situation.",
    )
    montant_cumul_ht = fields.Monetary(
        string='Montant cumulé HT',
        compute='_compute_montant_cumul_ht',
        store=True,
        currency_field='currency_id',
        help="Montant HT correspondant à l'avancement cumulé.",
    )
    montant_situation_precedente = fields.Monetary(
        string='Situations précédentes HT',
        currency_field='currency_id',
        help="Total des montants HT réglés lors des situations précédentes.",
    )
    montant_situation_ht = fields.Monetary(
        string='Montant situation HT',
        compute='_compute_montant_situation_ht',
        store=True,
        currency_field='currency_id',
        help="Montant HT de cette situation = cumulé - situations précédentes.",
    )

    # ------------------------------------------------------------------
    # TVA
    # ------------------------------------------------------------------

    tva_taux = fields.Float(
        string='Taux TVA (%)',
        default=20.0,
        digits=(5, 2),
        tracking=True,
    )
    montant_tva = fields.Monetary(
        string='Montant TVA',
        compute='_compute_tva_ttc',
        store=True,
        currency_field='currency_id',
    )
    montant_ttc = fields.Monetary(
        string='Montant TTC',
        compute='_compute_tva_ttc',
        store=True,
        currency_field='currency_id',
    )

    # ------------------------------------------------------------------
    # Retenue de garantie
    # ------------------------------------------------------------------

    retenue_garantie_taux = fields.Float(
        string='Taux RG (%)',
        default=10.0,
        digits=(5, 2),
        help="Taux de la retenue de garantie (habituellement 10 %).",
    )
    retenue_garantie = fields.Monetary(
        string='Retenue de garantie',
        compute='_compute_retenue_garantie',
        store=True,
        currency_field='currency_id',
    )

    # ------------------------------------------------------------------
    # Avance remboursement
    # ------------------------------------------------------------------

    avance_remboursement = fields.Monetary(
        string='Remboursement avance',
        currency_field='currency_id',
        tracking=True,
        help="Montant de l'avance de démarrage à rembourser sur cette situation.",
    )

    # ------------------------------------------------------------------
    # Net
    # ------------------------------------------------------------------

    net_a_payer = fields.Monetary(
        string='Net à payer',
        compute='_compute_net_a_payer',
        store=True,
        currency_field='currency_id',
    )

    # ------------------------------------------------------------------
    # Lines
    # ------------------------------------------------------------------

    situation_line_ids = fields.One2many(
        comodel_name='telecom.situation.line',
        inverse_name='situation_id',
        string='Détail par lot / site',
        copy=True,
    )

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    state = fields.Selection(
        selection=[
            ('draft', 'Brouillon'),
            ('soumis', 'Soumis au client'),
            ('approuve', 'Approuvé'),
            ('facture', 'Facturé'),
            ('paye', 'Payé'),
        ],
        string='État',
        required=True,
        default='draft',
        copy=False,
        tracking=True,
        index=True,
    )
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Facture',
        copy=False,
        readonly=True,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # SLA / payment deadline — loi 69-21
    # ------------------------------------------------------------------

    date_soumission = fields.Date(
        string='Date de soumission',
        copy=False,
        tracking=True,
    )
    date_paiement_prevu = fields.Date(
        string='Date limite de paiement',
        compute='_compute_date_paiement_prevu',
        store=True,
        help="Date de soumission + 60 jours (loi 69-21).",
    )
    delai_depasse = fields.Boolean(
        string='Délai dépassé',
        compute='_compute_delai_depasse',
        store=True,
        help="True si le délai légal de 60 jours est dépassé sans paiement.",
    )

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    notes = fields.Text(
        string='Notes internes',
    )

    # ------------------------------------------------------------------
    # SQL constraints
    # ------------------------------------------------------------------

    _sql_constraints = [
        (
            'numero_project_uniq',
            'UNIQUE(project_id, numero_situation)',
            'Ce numéro de situation est déjà utilisé pour ce projet.',
        ),
    ]

    # ------------------------------------------------------------------
    # Computed name
    # ------------------------------------------------------------------

    @api.depends('sequence_number')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.sequence_number or _('Nouvelle situation')

    # ------------------------------------------------------------------
    # Financial computations
    # ------------------------------------------------------------------

    @api.depends('montant_marche_ht', 'taux_avancement_cumul')
    def _compute_montant_cumul_ht(self):
        for rec in self:
            rec.montant_cumul_ht = (
                rec.montant_marche_ht * rec.taux_avancement_cumul / 100.0
            )

    @api.depends('montant_cumul_ht', 'montant_situation_precedente')
    def _compute_montant_situation_ht(self):
        for rec in self:
            rec.montant_situation_ht = (
                rec.montant_cumul_ht - rec.montant_situation_precedente
            )

    @api.depends('montant_situation_ht', 'tva_taux')
    def _compute_tva_ttc(self):
        for rec in self:
            rec.montant_tva = rec.montant_situation_ht * rec.tva_taux / 100.0
            rec.montant_ttc = rec.montant_situation_ht + rec.montant_tva

    @api.depends('montant_situation_ht', 'retenue_garantie_taux')
    def _compute_retenue_garantie(self):
        for rec in self:
            rec.retenue_garantie = (
                rec.montant_situation_ht * rec.retenue_garantie_taux / 100.0
            )

    @api.depends('montant_ttc', 'retenue_garantie', 'avance_remboursement')
    def _compute_net_a_payer(self):
        for rec in self:
            rec.net_a_payer = (
                rec.montant_ttc
                - rec.retenue_garantie
                - rec.avance_remboursement
            )

    # ------------------------------------------------------------------
    # SLA computations
    # ------------------------------------------------------------------

    @api.depends('date_soumission')
    def _compute_date_paiement_prevu(self):
        for rec in self:
            if rec.date_soumission:
                rec.date_paiement_prevu = rec.date_soumission + timedelta(days=60)
            else:
                rec.date_paiement_prevu = False

    @api.depends('date_paiement_prevu', 'state')
    def _compute_delai_depasse(self):
        today = fields.Date.today()
        for rec in self:
            if (
                rec.date_paiement_prevu
                and rec.state not in ('paye',)
                and today > rec.date_paiement_prevu
            ):
                rec.delai_depasse = True
            else:
                rec.delai_depasse = False

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """Assign sequence number on creation."""
        for vals in vals_list:
            if not vals.get('sequence_number'):
                vals['sequence_number'] = (
                    self.env['ir.sequence'].next_by_code('telecom.situation')
                    or _('Nouveau')
                )
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------

    def action_soumettre(self):
        """Transition draft → soumis; record submission date."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    _("Seule une situation en brouillon peut être soumise.")
                )
        self.write({
            'state': 'soumis',
            'date_soumission': fields.Date.today(),
        })

    def action_approuver(self):
        """Transition soumis → approuve."""
        for rec in self:
            if rec.state != 'soumis':
                raise UserError(
                    _("Seule une situation soumise peut être approuvée.")
                )
        self.write({'state': 'approuve'})

    def action_creer_facture(self):
        """
        Transition approuve → facture.
        Creates a customer invoice (account.move) summarising this situation.
        """
        self.ensure_one()
        if self.state != 'approuve':
            raise UserError(
                _("La situation doit être approuvée avant de créer la facture.")
            )
        if self.invoice_id:
            raise UserError(
                _("Une facture existe déjà pour cette situation.")
            )

        # Resolve the account income line (use default customer income account)
        company = self.company_id or self.env.company
        account = self.env['account.account'].search([
            ('account_type', 'in', ('income', 'income_other')),
            ('company_id', '=', company.id),
            ('deprecated', '=', False),
        ], limit=1)

        invoice_line_vals = []

        # One line per situation line; fallback to a global line
        if self.situation_line_ids:
            for line in self.situation_line_ids:
                invoice_line_vals.append((0, 0, {
                    'name': line.description,
                    'quantity': 1.0,
                    'price_unit': line.montant_periode,
                    'account_id': account.id if account else False,
                }))
        else:
            invoice_line_vals.append((0, 0, {
                'name': _(
                    'Situation n° %(num)s — %(proj)s — Période %(du)s au %(au)s',
                    num=self.numero_situation,
                    proj=self.project_id.name,
                    du=self.periode_du,
                    au=self.periode_au,
                ),
                'quantity': 1.0,
                'price_unit': self.montant_situation_ht,
                'account_id': account.id if account else False,
            }))

        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.client_id.id,
            'invoice_date': fields.Date.today(),
            'ref': self.name,
            'company_id': company.id,
            'situation_id': self.id,
            'invoice_line_ids': invoice_line_vals,
        })

        self.write({
            'state': 'facture',
            'invoice_id': move.id,
        })

        # Return action to open the newly created invoice
        return {
            'type': 'ir.actions.act_window',
            'name': _('Facture situation'),
            'res_model': 'account.move',
            'res_id': move.id,
            'view_mode': 'form',
        }

    def action_marquer_paye(self):
        """Transition facture → paye."""
        for rec in self:
            if rec.state != 'facture':
                raise UserError(
                    _("La situation doit être à l'état 'Facturé' pour être marquée payée.")
                )
        self.write({'state': 'paye'})

    def action_reset_draft(self):
        """Admin reset to draft."""
        admin_group = self.env.ref(
            'telecom_base.group_telecom_admin', raise_if_not_found=False
        )
        if admin_group and admin_group not in self.env.user.groups_id:
            raise UserError(
                _("Seul un administrateur TelecomERP peut remettre une situation en brouillon.")
            )
        self.write({'state': 'draft'})

    # ------------------------------------------------------------------
    # Smart-button helpers
    # ------------------------------------------------------------------

    def action_view_invoice(self):
        """Open the linked customer invoice."""
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_("Aucune facture liée à cette situation."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Facture'),
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
        }
