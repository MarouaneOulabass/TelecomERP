# -*- coding: utf-8 -*-
"""
telecom.ao — Appel d'Offres (Tender) main model.

Manages the full tender pipeline from detection to contract transformation,
including BPU lines, bank guarantee tracking, and state transitions.
"""

from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


# ---------------------------------------------------------------------------
# State selection (module-level constant for reuse)
# ---------------------------------------------------------------------------
AO_STATE_SELECTION = [
    ('detecte',   'Détecté'),
    ('etude',     'En étude'),
    ('soumis',    'Soumis'),
    ('gagne',     'Gagné'),
    ('perdu',     'Perdu'),
    ('projet',    'Transformé en projet'),
    ('abandonne', 'Abandonné'),
]


class TelecomAo(models.Model):
    """Appel d'Offres — tender dossier with full lifecycle management."""

    _name = 'telecom.ao'
    _description = "Appel d'Offres"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_remise asc, id desc'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Identity / Header
    # ------------------------------------------------------------------
    name = fields.Char(
        string="Titre AO",
        required=True,
        tracking=True,
    )
    numero_ao = fields.Char(
        string='Numéro AO',
        copy=False,
        readonly=True,
        default=lambda self: _('Nouveau'),
        tracking=True,
    )
    reference_dao = fields.Char(
        string='Référence DAO',
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company,
    )

    # ------------------------------------------------------------------
    # Partners
    # ------------------------------------------------------------------
    maitre_ouvrage_id = fields.Many2one(
        comodel_name='res.partner',
        string="Maître d'ouvrage",
        required=True,
        tracking=True,
        domain="[('partner_type', 'in', ['operator', 'public_org'])]",
        index=True,
    )
    responsable_id = fields.Many2one(
        comodel_name='res.users',
        string="Chargé d'affaires",
        tracking=True,
        default=lambda self: self.env.user,
    )

    # ------------------------------------------------------------------
    # Dates
    # ------------------------------------------------------------------
    date_reception_dao = fields.Date(
        string='Date réception DAO',
    )
    date_remise = fields.Date(
        string='Date limite remise offre',
        tracking=True,
    )
    date_ouverture_plis = fields.Date(
        string='Date ouverture des plis',
    )

    # ------------------------------------------------------------------
    # Lots
    # ------------------------------------------------------------------
    lots_vises = fields.Char(
        string='Lots visés',
        help="Exemple : Lot 1, Lot 2",
    )

    # ------------------------------------------------------------------
    # Amounts
    # ------------------------------------------------------------------
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Devise',
        required=True,
        default=lambda self: self.env.ref('base.MAD', raise_if_not_found=False)
                             or self.env['res.currency'].search([('name', '=', 'MAD')], limit=1),
    )
    montant_estimatif = fields.Monetary(
        string='Montant estimatif HT',
        currency_field='currency_id',
    )
    montant_soumis = fields.Monetary(
        string='Montant soumissionné HT',
        currency_field='currency_id',
        tracking=True,
    )
    montant_bpu_total = fields.Monetary(
        string='Total BPU HT',
        currency_field='currency_id',
        compute='_compute_montant_bpu_total',
        store=True,
        readonly=True,
    )

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=AO_STATE_SELECTION,
        string='État',
        required=True,
        default='detecte',
        tracking=True,
        copy=False,
    )
    motif_perte = fields.Text(
        string='Motif de perte',
    )

    # ------------------------------------------------------------------
    # Cautions bancaires
    # ------------------------------------------------------------------
    caution_provisoire_montant = fields.Monetary(
        string='Caution provisoire (1,5%)',
        currency_field='currency_id',
        compute='_compute_cautions',
        store=True,
        readonly=True,
    )
    caution_definitif_montant = fields.Monetary(
        string='Caution définitive (3%)',
        currency_field='currency_id',
        compute='_compute_cautions',
        store=True,
        readonly=True,
    )
    caution_provisoire_fournie = fields.Boolean(
        string='Caution provisoire fournie',
        default=False,
    )
    caution_provisoire_date = fields.Date(
        string='Date remise caution provisoire',
    )
    caution_provisoire_banque = fields.Char(
        string='Banque émettrice',
    )

    # ------------------------------------------------------------------
    # Relations
    # ------------------------------------------------------------------
    bpu_ids = fields.One2many(
        comodel_name='telecom.bpu.ligne',
        inverse_name='ao_id',
        string='Lignes BPU',
        copy=True,
    )
    document_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='telecom_ao_attachment_rel',
        column1='ao_id',
        column2='attachment_id',
        string='Documents',
    )
    contract_id = fields.Many2one(
        comodel_name='telecom.contract',
        string='Contrat résultant',
        readonly=True,
        copy=False,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------
    notes = fields.Text(
        string='Notes',
    )
    priority = fields.Selection(
        selection=[('0', 'Normal'), ('1', 'Urgent'), ('2', 'Très urgent')],
        string='Priorité',
        default='0',
    )

    # ------------------------------------------------------------------
    # Computed / helper fields
    # ------------------------------------------------------------------
    jours_avant_remise = fields.Integer(
        string='Jours avant remise',
        compute='_compute_jours_avant_remise',
        store=False,
    )
    bpu_count = fields.Integer(
        string='Nb lignes BPU',
        compute='_compute_bpu_count',
        store=False,
    )

    # ------------------------------------------------------------------
    # SQL constraints
    # ------------------------------------------------------------------
    _sql_constraints = [
        ('numero_ao_uniq', 'UNIQUE(numero_ao)',
         "Ce numéro AO est déjà utilisé."),
    ]

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign sequence number on creation."""
        for vals in vals_list:
            if vals.get('numero_ao', _('Nouveau')) == _('Nouveau'):
                vals['numero_ao'] = self.env['ir.sequence'].next_by_code('telecom.ao') or _('Nouveau')
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends('bpu_ids.montant_ht')
    def _compute_montant_bpu_total(self):
        """Sum all BPU line totals."""
        for rec in self:
            rec.montant_bpu_total = sum(rec.bpu_ids.mapped('montant_ht'))

    @api.depends('montant_soumis')
    def _compute_cautions(self):
        """Compute provisional (1.5%) and definitive (3%) bank guarantee amounts."""
        for rec in self:
            rec.caution_provisoire_montant = rec.montant_soumis * 0.015
            rec.caution_definitif_montant = rec.montant_soumis * 0.03

    @api.depends('date_remise')
    def _compute_jours_avant_remise(self):
        """Calculate calendar days remaining until submission deadline."""
        today = date.today()
        for rec in self:
            if rec.date_remise:
                rec.jours_avant_remise = (rec.date_remise - today).days
            else:
                rec.jours_avant_remise = 0

    @api.depends('bpu_ids')
    def _compute_bpu_count(self):
        for rec in self:
            rec.bpu_count = len(rec.bpu_ids)

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------
    @api.onchange('montant_soumis')
    def _onchange_montant_soumis(self):
        """Trigger caution recomputation when submitted amount changes."""
        self._compute_cautions()

    # ------------------------------------------------------------------
    # State transition actions
    # ------------------------------------------------------------------
    def action_view_contract(self):
        """Open the resulting contract record (smart button)."""
        self.ensure_one()
        if not self.contract_id:
            return {}
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contrat',
            'res_model': 'telecom.contract',
            'view_mode': 'form',
            'res_id': self.contract_id.id,
        }

    def action_telecom_bpu_ligne(self):
        """Open BPU lines for this AO (smart button)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lignes BPU',
            'res_model': 'telecom.bpu.ligne',
            'view_mode': 'list,form',
            'domain': [('ao_id', '=', self.id)],
            'context': {'default_ao_id': self.id},
        }

    def action_etude(self):
        """Move AO to 'En étude' state."""
        self._check_state_transition('detecte', 'etude')
        self.write({'state': 'etude'})

    def action_soumettre(self):
        """Mark AO as submitted (soumis)."""
        for rec in self:
            if not rec.date_remise:
                raise UserError(_("Veuillez saisir la date limite de remise avant de soumettre."))
        self._check_state_transition('etude', 'soumis')
        self.write({'state': 'soumis'})

    def action_gagner(self):
        """Mark AO as won."""
        self._check_state_transition('soumis', 'gagne')
        self.write({'state': 'gagne'})

    def action_perdre(self):
        """Mark AO as lost. motif_perte should be filled in by the user."""
        self._check_state_transition('soumis', 'perdu')
        self.write({'state': 'perdu'})

    def action_transformer_projet(self):
        """Mark AO as transformed into a project/contract."""
        for rec in self:
            if rec.state != 'gagne':
                raise UserError(_("Seul un AO gagné peut être transformé en projet."))
        self.write({'state': 'projet'})

    def action_abandonner(self):
        """Abandon the AO."""
        self.write({'state': 'abandonne'})

    def _check_state_transition(self, expected_from, to_state):
        """Validate that all records are in the expected source state."""
        for rec in self:
            if rec.state != expected_from:
                raise UserError(
                    _("Impossible de passer à l'état '%(to)s' depuis '%(from)s'.",
                      to=dict(AO_STATE_SELECTION).get(to_state, to_state),
                      from_=dict(AO_STATE_SELECTION).get(rec.state, rec.state))
                )
