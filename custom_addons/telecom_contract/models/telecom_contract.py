# -*- coding: utf-8 -*-
"""
telecom.contract — Main contract model.

Covers framework contracts (contrats-cadres), maintenance contracts,
deployment markets, sub-contracting, and site leases.
Includes SLA tracking and automated expiry detection.
"""

from datetime import date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


# ---------------------------------------------------------------------------
# Contract type selection (module-level constant)
# ---------------------------------------------------------------------------
CONTRACT_TYPE_SELECTION = [
    ('cadre_operateur', "Contrat-cadre opérateur"),
    ('maintenance',     "Contrat maintenance"),
    ('deploiement',     "Marché déploiement"),
    ('sous_traitance',  "Sous-traitance"),
    ('bail_site',       "Bail site (avec bailleur)"),
]

CONTRACT_STATE_SELECTION = [
    ('brouillon', 'Brouillon'),
    ('actif',     'Actif'),
    ('expire',    'Expiré'),
    ('resilie',   'Résilié'),
    ('suspendu',  'Suspendu'),
]


class TelecomContract(models.Model):
    """Telecom contract with SLA management and bank guarantee tracking."""

    _name = 'telecom.contract'
    _description = 'Contrat télécom'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_debut desc, id desc'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    name = fields.Char(
        string='Titre contrat',
        required=True,
        tracking=True,
    )
    reference = fields.Char(
        string='Référence contrat',
        copy=False,
        readonly=True,
        default=lambda self: _('Nouveau'),
        tracking=True,
    )
    contract_type = fields.Selection(
        selection=CONTRACT_TYPE_SELECTION,
        string='Type de contrat',
        required=True,
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
    partenaire_id = fields.Many2one(
        comodel_name='res.partner',
        string='Opérateur / Client',
        required=True,
        tracking=True,
        index=True,
    )
    responsable_id = fields.Many2one(
        comodel_name='res.users',
        string="Chargé d'affaires",
        tracking=True,
        default=lambda self: self.env.user,
    )

    # ------------------------------------------------------------------
    # Contract period
    # ------------------------------------------------------------------
    date_debut = fields.Date(
        string='Date de début',
        required=True,
        tracking=True,
    )
    date_fin = fields.Date(
        string='Date de fin',
        tracking=True,
        help="Laisser vide pour un contrat à durée indéterminée.",
    )
    tacite_reconduction = fields.Boolean(
        string='Tacite reconduction',
        default=False,
    )
    preavis_resiliation_mois = fields.Integer(
        string='Préavis résiliation (mois)',
        default=3,
    )

    # ------------------------------------------------------------------
    # Financial
    # ------------------------------------------------------------------
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Devise',
        required=True,
        default=lambda self: self.env.ref('base.MAD', raise_if_not_found=False)
                             or self.env['res.currency'].search([('name', '=', 'MAD')], limit=1),
    )
    montant_total = fields.Monetary(
        string='Montant total HT',
        currency_field='currency_id',
        tracking=True,
    )

    # ------------------------------------------------------------------
    # SLA
    # ------------------------------------------------------------------
    sla_delai_intervention_h = fields.Integer(
        string='Délai intervention SLA (h)',
        default=48,
        help="Délai maximal d'intervention contractuel en heures.",
    )
    sla_delai_reparation_h = fields.Integer(
        string='Délai réparation SLA (h)',
        default=72,
        help="Délai maximal de réparation contractuel en heures.",
    )
    sla_disponibilite_pct = fields.Float(
        string='Disponibilité contractuelle (%)',
        default=99.5,
        digits=(5, 2),
    )
    penalite_sla = fields.Char(
        string='Pénalités SLA',
        help="Description des pénalités en cas de non-respect des SLA.",
    )

    # ------------------------------------------------------------------
    # Related records
    # ------------------------------------------------------------------
    sites_couverts = fields.Many2many(
        comodel_name='telecom.site',
        relation='telecom_contract_site_rel',
        column1='contract_id',
        column2='site_id',
        string='Sites couverts',
    )
    ao_id = fields.Many2one(
        comodel_name='telecom.ao',
        string="AO d'origine",
        tracking=True,
        help="Appel d'offres dont est issu ce contrat, si applicable.",
    )
    caution_bancaire_ids = fields.One2many(
        comodel_name='telecom.caution.bancaire',
        inverse_name='contract_id',
        string='Cautions bancaires',
        copy=False,
    )
    document_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='telecom_contract_attachment_rel',
        column1='contract_id',
        column2='attachment_id',
        string='Documents contractuels',
    )

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=CONTRACT_STATE_SELECTION,
        string='État',
        required=True,
        default='brouillon',
        tracking=True,
        copy=False,
    )

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------
    notes = fields.Text(
        string='Notes',
    )

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------
    nb_sites = fields.Integer(
        string='Nb sites',
        compute='_compute_nb_sites',
        store=False,
    )
    caution_count = fields.Integer(
        string='Nb cautions',
        compute='_compute_caution_count',
        store=False,
    )
    jours_avant_expiration = fields.Integer(
        string="Jours avant expiration",
        compute='_compute_jours_avant_expiration',
        store=False,
    )
    expiry_warning = fields.Boolean(
        string='Alerte expiration',
        compute='_compute_expiry_warning',
        store=True,
        help="True si le contrat expire dans les 90 jours.",
    )

    # ------------------------------------------------------------------
    # SQL constraints
    # ------------------------------------------------------------------
    _sql_constraints = [
        ('reference_uniq', 'UNIQUE(reference)',
         "Cette référence contrat est déjà utilisée."),
    ]

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign sequence number on creation."""
        for vals in vals_list:
            if vals.get('reference', _('Nouveau')) == _('Nouveau'):
                vals['reference'] = (
                    self.env['ir.sequence'].next_by_code('telecom.contract')
                    or _('Nouveau')
                )
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends('sites_couverts')
    def _compute_nb_sites(self):
        for rec in self:
            rec.nb_sites = len(rec.sites_couverts)

    @api.depends('caution_bancaire_ids')
    def _compute_caution_count(self):
        for rec in self:
            rec.caution_count = len(rec.caution_bancaire_ids)

    @api.depends('date_fin')
    def _compute_jours_avant_expiration(self):
        today = date.today()
        for rec in self:
            if rec.date_fin:
                rec.jours_avant_expiration = (rec.date_fin - today).days
            else:
                rec.jours_avant_expiration = 0

    @api.depends('date_fin', 'state')
    def _compute_expiry_warning(self):
        """Flag contracts expiring within 90 days (active contracts only)."""
        today = date.today()
        threshold = today + timedelta(days=90)
        for rec in self:
            if rec.state == 'actif' and rec.date_fin and rec.date_fin <= threshold:
                rec.expiry_warning = True
            else:
                rec.expiry_warning = False

    # ------------------------------------------------------------------
    # State transition actions
    # ------------------------------------------------------------------
    def action_activer(self):
        """Activate the contract."""
        for rec in self:
            if rec.state not in ('brouillon', 'suspendu'):
                raise UserError(
                    _("Seul un contrat en brouillon ou suspendu peut être activé.")
                )
        self.write({'state': 'actif'})

    def action_resilier(self):
        """Terminate the contract."""
        for rec in self:
            if rec.state not in ('actif', 'suspendu'):
                raise UserError(
                    _("Seul un contrat actif ou suspendu peut être résilié.")
                )
        self.write({'state': 'resilie'})

    def action_suspendre(self):
        """Suspend the contract."""
        for rec in self:
            if rec.state != 'actif':
                raise UserError(
                    _("Seul un contrat actif peut être suspendu.")
                )
        self.write({'state': 'suspendu'})

    def action_reactiver(self):
        """Reactivate a suspended contract."""
        for rec in self:
            if rec.state != 'suspendu':
                raise UserError(
                    _("Seul un contrat suspendu peut être réactivé.")
                )
        self.write({'state': 'actif'})

    # ------------------------------------------------------------------
    # Cron action
    # ------------------------------------------------------------------
    def action_view_cautions(self):
        """Open bank guarantees for this contract (smart button)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cautions bancaires',
            'res_model': 'telecom.caution.bancaire',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id},
        }

    def action_view_sites_covered(self):
        """Open a dialog/list of sites covered by this contract."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sites couverts',
            'res_model': 'telecom.site',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.sites_couverts.ids)],
            'context': dict(self.env.context),
        }

    def action_view_expiry_info(self):
        """Return self (no-op, used for the stat button click)."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contrat',
            'res_model': 'telecom.contract',
            'view_mode': 'form',
            'res_id': self.id,
        }

    @api.model
    def _check_expiry(self):
        """
        Cron job: mark contracts as expired when their end date has passed.
        Called by the scheduled action defined in data files.
        """
        today = date.today()
        expired = self.search([
            ('state', '=', 'actif'),
            ('date_fin', '<', today),
        ])
        if expired:
            expired.write({'state': 'expire'})
        # Recompute expiry warnings for all active contracts
        active = self.search([('state', '=', 'actif')])
        active._compute_expiry_warning()
