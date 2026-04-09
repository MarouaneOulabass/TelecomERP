# -*- coding: utf-8 -*-
"""
telecom.decompte — Décompte provisoire / définitif
====================================================
Official CCAG Travaux financial settlement document.

A décompte summarises the total financial position of a project at a
given point in time:

  Provisoire : issued after each significant phase or upon request.
  Définitif  : final settlement — triggers release of retenue de garantie
               if liberation_retenue is enabled.

Naming:
  Provisoire → DC/YYYY/NNN
  Définitif  → DDF/YYYY/NNN

Workflow: draft → soumis → approuve → contradictoire → signe → paye
"""

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TelecomDecompte(models.Model):
    """Décompte de travaux (CCAG Travaux format)."""

    _name = 'telecom.decompte'
    _description = 'Décompte de travaux'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_decompte desc, numero_decompte desc'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Auto-generated reference
    # ------------------------------------------------------------------

    name = fields.Char(
        string='N° Décompte',
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
    # Classification
    # ------------------------------------------------------------------

    decompte_type = fields.Selection(
        selection=[
            ('provisoire', 'Décompte provisoire'),
            ('definitif', 'Décompte définitif'),
        ],
        string='Type de décompte',
        required=True,
        default='provisoire',
        tracking=True,
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
    numero_decompte = fields.Integer(
        string='N° Décompte',
        tracking=True,
    )
    date_decompte = fields.Date(
        string='Date du décompte',
        required=True,
        default=fields.Date.today,
        tracking=True,
    )
    pv_id = fields.Many2one(
        comodel_name='telecom.pv.reception',
        string='PV de réception',
        tracking=True,
        help="PV de réception associé à ce décompte.",
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
    # Contract amount
    # ------------------------------------------------------------------

    montant_marche_ht = fields.Monetary(
        string='Montant marché initial HT',
        currency_field='currency_id',
        tracking=True,
    )

    # ------------------------------------------------------------------
    # SECTION I — Cumul travaux
    # ------------------------------------------------------------------

    montant_travaux_ht = fields.Monetary(
        string='Travaux cumulés HT',
        currency_field='currency_id',
        tracking=True,
        help="Montant total des travaux réalisés cumulés hors taxes.",
    )
    montant_travaux_supplementaires = fields.Monetary(
        string='Travaux supplémentaires HT',
        currency_field='currency_id',
        help="Travaux supplémentaires acceptés par avenant.",
    )
    montant_revisions_prix = fields.Monetary(
        string='Révisions de prix',
        currency_field='currency_id',
        help="Montant des révisions de prix appliquées (formule de révision contractuelle).",
    )
    total_ht_cumul = fields.Monetary(
        string='Total HT cumulé',
        compute='_compute_total_ht_cumul',
        store=True,
        currency_field='currency_id',
    )

    # ------------------------------------------------------------------
    # SECTION II — Déductions
    # ------------------------------------------------------------------

    retenue_garantie_taux = fields.Float(
        string='Taux RG (%)',
        default=10.0,
        digits=(5, 2),
    )
    retenue_garantie_cumul = fields.Monetary(
        string='Retenue de garantie cumulée',
        compute='_compute_retenue_garantie_cumul',
        store=True,
        currency_field='currency_id',
    )
    avances_versees = fields.Monetary(
        string='Total avances versées',
        currency_field='currency_id',
        help="Cumul des avances de démarrage versées à l'entreprise.",
    )
    avances_remboursees = fields.Monetary(
        string='Avances remboursées antérieurement',
        currency_field='currency_id',
        help="Montant des avances déjà remboursé dans les décomptes précédents.",
    )
    avance_periode = fields.Monetary(
        string='Remboursement avance cette période',
        currency_field='currency_id',
        help="Montant de l'avance à rembourser sur ce décompte.",
    )
    situations_anterieures = fields.Monetary(
        string='Situations antérieures réglées',
        currency_field='currency_id',
        help="Total des montants déjà réglés au titre des situations précédentes.",
    )

    # ------------------------------------------------------------------
    # SECTION III — TVA
    # ------------------------------------------------------------------

    tva_taux = fields.Float(
        string='Taux TVA (%)',
        default=20.0,
        digits=(5, 2),
    )
    base_tva = fields.Monetary(
        string='Base TVA',
        compute='_compute_base_tva',
        store=True,
        currency_field='currency_id',
        help="Assiette soumise à la TVA après déductions.",
    )
    tva_montant = fields.Monetary(
        string='Montant TVA',
        compute='_compute_tva_ras_net',
        store=True,
        currency_field='currency_id',
    )

    # ------------------------------------------------------------------
    # SECTION IV — Net
    # ------------------------------------------------------------------

    net_a_regler = fields.Monetary(
        string='Net à régler',
        compute='_compute_tva_ras_net',
        store=True,
        currency_field='currency_id',
    )
    ras_montant = fields.Monetary(
        string='RAS (10 %)',
        compute='_compute_tva_ras_net',
        store=True,
        currency_field='currency_id',
        help="Retenue à la source de 10 % sur le net HT.",
    )
    net_apres_ras = fields.Monetary(
        string='Net après RAS',
        compute='_compute_tva_ras_net',
        store=True,
        currency_field='currency_id',
    )

    # ------------------------------------------------------------------
    # SECTION V — Libération retenue de garantie (définitif only)
    # ------------------------------------------------------------------

    liberation_retenue = fields.Boolean(
        string='Libérer la retenue de garantie',
        default=False,
        tracking=True,
        help="Cocher pour inclure la libération de la RG dans ce décompte (définitif uniquement).",
    )
    montant_liberation_rg = fields.Monetary(
        string='Montant RG libérée',
        currency_field='currency_id',
        help="Montant de la retenue de garantie libéré sur ce décompte.",
    )

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    state = fields.Selection(
        selection=[
            ('draft', 'Brouillon'),
            ('soumis', 'Soumis'),
            ('approuve', 'Approuvé'),
            ('contradictoire', 'En phase contradictoire'),
            ('signe', 'Signé'),
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
    # SLA / payment deadline
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
    )

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    notes = fields.Text(string='Notes internes')

    # ------------------------------------------------------------------
    # Computed name
    # ------------------------------------------------------------------

    @api.depends('sequence_number', 'decompte_type')
    def _compute_name(self):
        for rec in self:
            if rec.sequence_number:
                rec.name = rec.sequence_number
            else:
                prefix = 'DDF' if rec.decompte_type == 'definitif' else 'DC'
                rec.name = _('Nouveau %(prefix)s', prefix=prefix)

    # ------------------------------------------------------------------
    # Financial computations
    # ------------------------------------------------------------------

    @api.depends('montant_travaux_ht', 'montant_travaux_supplementaires', 'montant_revisions_prix')
    def _compute_total_ht_cumul(self):
        for rec in self:
            rec.total_ht_cumul = (
                rec.montant_travaux_ht
                + rec.montant_travaux_supplementaires
                + rec.montant_revisions_prix
            )

    @api.depends('total_ht_cumul', 'retenue_garantie_taux')
    def _compute_retenue_garantie_cumul(self):
        for rec in self:
            rec.retenue_garantie_cumul = (
                rec.total_ht_cumul * rec.retenue_garantie_taux / 100.0
            )

    @api.depends(
        'total_ht_cumul',
        'retenue_garantie_cumul',
        'avance_periode',
        'avances_remboursees',
        'situations_anterieures',
    )
    def _compute_base_tva(self):
        """
        Base TVA = total HT cumulé
                   − retenue de garantie cumulée
                   − avances remboursées cette période
                   − situations antérieures réglées
        """
        for rec in self:
            rec.base_tva = (
                rec.total_ht_cumul
                - rec.retenue_garantie_cumul
                - rec.avance_periode
                - rec.situations_anterieures
            )

    @api.depends('base_tva', 'tva_taux', 'total_ht_cumul')
    def _compute_tva_ras_net(self):
        """
        Computes:
          - tva_montant
          - net_a_regler   (base_tva + TVA)
          - ras_montant    (10 % of base_tva, applied before TVA in MA practice)
          - net_apres_ras  (net_a_regler − ras_montant)
        """
        for rec in self:
            tva = rec.base_tva * rec.tva_taux / 100.0
            rec.tva_montant = tva
            net = rec.base_tva + tva
            rec.net_a_regler = net
            rec.ras_montant = rec.base_tva * 0.10
            rec.net_apres_ras = net - rec.ras_montant

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
        """Assign the correct sequence on creation depending on decompte_type."""
        for vals in vals_list:
            if not vals.get('sequence_number'):
                dtype = vals.get('decompte_type', 'provisoire')
                seq_code = (
                    'telecom.decompte.definitif'
                    if dtype == 'definitif'
                    else 'telecom.decompte.provisoire'
                )
                vals['sequence_number'] = (
                    self.env['ir.sequence'].next_by_code(seq_code) or _('Nouveau')
                )
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------

    def action_soumettre(self):
        """Transition draft → soumis."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Seul un décompte en brouillon peut être soumis."))
        self.write({
            'state': 'soumis',
            'date_soumission': fields.Date.today(),
        })

    def action_approuver(self):
        """Transition soumis → approuve."""
        for rec in self:
            if rec.state != 'soumis':
                raise UserError(_("Seul un décompte soumis peut être approuvé."))
        self.write({'state': 'approuve'})

    def action_contradictoire(self):
        """Transition approuve → contradictoire (phase contradictoire)."""
        for rec in self:
            if rec.state not in ('approuve', 'soumis'):
                raise UserError(
                    _("Le décompte doit être soumis ou approuvé pour passer en phase contradictoire.")
                )
        self.write({'state': 'contradictoire'})

    def action_signer(self):
        """Transition (approuve | contradictoire) → signe."""
        for rec in self:
            if rec.state not in ('approuve', 'contradictoire'):
                raise UserError(
                    _("Le décompte doit être approuvé ou en phase contradictoire pour être signé.")
                )
        self.write({'state': 'signe'})

    def action_creer_facture(self):
        """
        Transition signe → crée une facture client et passe à l'état 'signe'
        (la facture reflète le net_apres_ras).
        """
        self.ensure_one()
        if self.state != 'signe':
            raise UserError(
                _("Le décompte doit être signé avant de créer la facture.")
            )
        if self.invoice_id:
            raise UserError(_("Une facture existe déjà pour ce décompte."))

        company = self.company_id or self.env.company
        account = self.env['account.account'].search([
            ('account_type', 'in', ('income', 'income_other')),
            ('company_id', '=', company.id),
            ('deprecated', '=', False),
        ], limit=1)

        description = _(
            'Décompte %(type)s n° %(num)s — %(proj)s',
            type=dict(self._fields['decompte_type'].selection).get(self.decompte_type, ''),
            num=self.numero_decompte or '',
            proj=self.project_id.name,
        )

        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.client_id.id,
            'invoice_date': fields.Date.today(),
            'ref': self.name,
            'company_id': company.id,
            'decompte_id': self.id,
            'invoice_line_ids': [(0, 0, {
                'name': description,
                'quantity': 1.0,
                'price_unit': self.net_apres_ras,
                'account_id': account.id if account else False,
            })],
        })

        self.write({'invoice_id': move.id})

        return {
            'type': 'ir.actions.act_window',
            'name': _('Facture décompte'),
            'res_model': 'account.move',
            'res_id': move.id,
            'view_mode': 'form',
        }

    def action_marquer_paye(self):
        """Mark as paid."""
        for rec in self:
            if rec.state not in ('signe',):
                raise UserError(
                    _("Le décompte doit être signé pour être marqué payé.")
                )
        self.write({'state': 'paye'})

    def action_reset_draft(self):
        """Admin reset to draft."""
        admin_group = self.env.ref(
            'telecom_base.group_telecom_admin', raise_if_not_found=False
        )
        if admin_group and admin_group not in self.env.user.groups_id:
            raise UserError(
                _("Seul un administrateur TelecomERP peut remettre un décompte en brouillon.")
            )
        self.write({'state': 'draft'})

    # ------------------------------------------------------------------
    # Smart-button helpers
    # ------------------------------------------------------------------

    def action_print_decompte(self):
        """Generate the CCAG Travaux PDF report."""
        self.ensure_one()
        return self.env.ref(
            'telecom_finance_ma.action_report_telecom_decompte'
        ).report_action(self)

    def action_view_invoice(self):
        """Open the linked customer invoice."""
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_("Aucune facture liée à ce décompte."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Facture'),
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
        }
