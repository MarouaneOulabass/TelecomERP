# -*- coding: utf-8 -*-
"""
telecom_equipment / telecom_equipment_historique
=================================================
Core models for telecom equipment lifecycle management.

Models defined here:
- telecom.equipment           : individual physical equipment asset
- telecom.equipment.historique: immutable event log for each asset
"""

from datetime import date, timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


# ---------------------------------------------------------------------------
# Selection constants
# ---------------------------------------------------------------------------

STATE_SELECTION = [
    ('en_stock', 'En stock'),
    ('installe', 'Installé'),
    ('en_panne', 'En panne'),
    ('en_reparation', 'En réparation / SAV'),
    ('retire', 'Retiré du service'),
    ('mis_au_rebut', 'Mis au rebut'),
]

EVENT_TYPE_SELECTION = [
    ('installation', 'Installation'),
    ('panne', 'Panne'),
    ('reparation', 'Réparation / SAV'),
    ('maintenance', 'Maintenance préventive'),
    ('retrait', 'Retrait du service'),
    ('autre', 'Autre'),
]


# ---------------------------------------------------------------------------
# telecom.equipment
# ---------------------------------------------------------------------------

class TelecomEquipment(models.Model):
    """
    Physical telecom equipment asset.

    Tracks the full lifecycle of an asset — from purchase and stock through
    field installation, breakdowns, repair, and decommissioning.
    Inherits mail.thread for a full chatter audit trail.
    """

    _name = 'telecom.equipment'
    _description = 'Équipement télécom'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code asc, name asc'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------

    name = fields.Char(
        string='Désignation',
        required=True,
        tracking=True,
    )
    code = fields.Char(
        string='Code équipement',
        compute='_compute_code',
        store=True,
        copy=False,
        readonly=True,
        help="Auto-generated: EQ/<CAT_CODE>/<sequence> e.g. EQ/ANT/0001",
    )
    category_id = fields.Many2one(
        'telecom.equipment.category',
        string="Catégorie",
        required=True,
        tracking=True,
        ondelete='restrict',
        index=True,
    )
    marque = fields.Char(
        string='Marque / Fabricant',
        tracking=True,
    )
    modele = fields.Char(
        string='Modèle',
        tracking=True,
    )
    numero_serie = fields.Char(
        string='Numéro de série',
        required=True,
        copy=False,
        tracking=True,
        index=True,
    )
    reference_fabricant = fields.Char(
        string='Référence fabricant',
    )
    fournisseur_id = fields.Many2one(
        'res.partner',
        string='Fournisseur',
        domain=[('supplier_rank', '>', 0)],
        tracking=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Article Odoo lié',
        ondelete='restrict',
        help="Odoo product.product record corresponding to this equipment type",
    )

    # ------------------------------------------------------------------
    # State & lifecycle
    # ------------------------------------------------------------------

    state = fields.Selection(
        selection=STATE_SELECTION,
        string='État',
        required=True,
        default='en_stock',
        copy=False,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Location
    # ------------------------------------------------------------------

    site_id = fields.Many2one(
        'telecom.site',
        string="Site d'installation",
        tracking=True,
        ondelete='restrict',
        index=True,
    )
    emplacement = fields.Char(
        string='Emplacement précis',
        help='Emplacement précis sur le site, ex: "Mât secteur Nord"',
    )
    date_installation = fields.Date(
        string="Date d'installation",
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Purchase & warranty
    # ------------------------------------------------------------------

    date_achat = fields.Date(
        string="Date d'achat",
    )
    prix_achat = fields.Monetary(
        string="Prix d'achat",
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        required=True,
        default=lambda self: self.env.ref('base.MAD', raise_if_not_found=False)
                            or self.env.ref('base.EUR'),
    )
    date_fin_garantie = fields.Date(
        string='Fin de garantie fournisseur',
        tracking=True,
    )
    garantie_expiring = fields.Boolean(
        string='Garantie expire bientôt',
        compute='_compute_garantie_expiring',
        store=True,
        help="True when the supplier warranty expires within 60 days",
    )

    # ------------------------------------------------------------------
    # Maintenance contract
    # ------------------------------------------------------------------

    contrat_maintenance_fournisseur = fields.Char(
        string='Réf. contrat maintenance fournisseur',
    )
    date_fin_contrat_maintenance = fields.Date(
        string='Fin contrat maintenance',
        tracking=True,
    )

    # ------------------------------------------------------------------
    # History & notes
    # ------------------------------------------------------------------

    historique_ids = fields.One2many(
        'telecom.equipment.historique',
        'equipment_id',
        string='Historique',
    )
    historique_count = fields.Integer(
        string="Nb événements",
        compute='_compute_historique_count',
    )
    notes = fields.Text(
        string='Notes',
    )

    # ------------------------------------------------------------------
    # System fields
    # ------------------------------------------------------------------

    active = fields.Boolean(
        default=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    # ------------------------------------------------------------------
    # SQL constraints
    # ------------------------------------------------------------------

    _sql_constraints = [
        (
            'numero_serie_company_uniq',
            'UNIQUE(numero_serie, company_id)',
            'Ce numéro de série existe déjà pour cette société.',
        ),
    ]

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------

    @api.depends('category_id', 'category_id.code')
    def _compute_code(self):
        """
        Generate a code of the form EQ/<CAT_CODE>/<5-digit-id>.
        Falls back to EQ/GEN/<id> when the category has no code.
        Only set once (on first save) — never overwritten.
        """
        for eq in self:
            if eq.code:
                # Already assigned — do not overwrite
                continue
            if eq.id:
                cat_code = (
                    (eq.category_id.code or 'GEN').upper().replace(' ', '_')
                )
                eq.code = f'EQ/{cat_code}/{eq.id:05d}'
            else:
                eq.code = False

    @api.depends('date_fin_garantie')
    def _compute_garantie_expiring(self):
        """Flag equipment whose warranty expires within the next 60 days."""
        today = date.today()
        threshold = today + timedelta(days=60)
        for eq in self:
            if eq.date_fin_garantie and today <= eq.date_fin_garantie <= threshold:
                eq.garantie_expiring = True
            else:
                eq.garantie_expiring = False

    def _compute_historique_count(self):
        for eq in self:
            eq.historique_count = len(eq.historique_ids)

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """Create equipment and recompute code after IDs are assigned."""
        records = super().create(vals_list)
        # Recompute code now that IDs are available
        records._compute_code()
        return records

    def write(self, vals):
        """
        Override write to automatically create a historique entry
        whenever the equipment state changes.
        """
        old_states = {eq.id: eq.state for eq in self}
        result = super().write(vals)

        if 'state' in vals:
            new_state = vals['state']
            state_labels = dict(STATE_SELECTION)
            event_map = {
                'installe': 'installation',
                'en_panne': 'panne',
                'en_reparation': 'reparation',
                'retire': 'retrait',
                'mis_au_rebut': 'retrait',
                'en_stock': 'autre',
            }
            for eq in self:
                old_state = old_states.get(eq.id, '')
                if old_state != new_state:
                    old_label = state_labels.get(old_state, old_state)
                    new_label = state_labels.get(new_state, new_state)
                    self.env['telecom.equipment.historique'].create({
                        'equipment_id': eq.id,
                        'event_type': event_map.get(new_state, 'autre'),
                        'description': (
                            f'Changement d\'état : {old_label} → {new_label}'
                        ),
                        'site_id': eq.site_id.id if eq.site_id else False,
                    })
        return result

    # ------------------------------------------------------------------
    # State transition actions
    # ------------------------------------------------------------------

    def action_installer(self):
        """
        Transition to 'installe' state.
        Requires a site to be set on the equipment.
        """
        for eq in self:
            if not eq.site_id:
                raise UserError(
                    "Veuillez renseigner le site d'installation avant d'installer l'équipement."
                )
        self.write({'state': 'installe'})
        if not self[0].date_installation:
            self.write({'date_installation': fields.Date.today()})

    def action_declarer_panne(self):
        """Transition to 'en_panne' state."""
        for eq in self:
            if eq.state not in ('installe',):
                raise UserError(
                    "Seul un équipement installé peut être déclaré en panne."
                )
        self.write({'state': 'en_panne'})

    def action_envoyer_reparation(self):
        """Transition to 'en_reparation' state."""
        for eq in self:
            if eq.state not in ('en_panne', 'installe'):
                raise UserError(
                    "L'équipement doit être en panne ou installé pour être envoyé en réparation."
                )
        self.write({'state': 'en_reparation'})

    def action_remettre_service(self):
        """Transition to 'installe' after repair."""
        for eq in self:
            if eq.state not in ('en_reparation', 'en_stock'):
                raise UserError(
                    "L'équipement doit être en réparation ou en stock pour être remis en service."
                )
            if not eq.site_id:
                raise UserError(
                    "Veuillez renseigner le site d'installation avant de remettre en service."
                )
        self.write({'state': 'installe'})

    def action_retirer(self):
        """Transition to 'retire' state."""
        for eq in self:
            if eq.state in ('mis_au_rebut',):
                raise UserError(
                    "Un équipement mis au rebut ne peut pas être retiré du service."
                )
        self.write({'state': 'retire'})

    def action_rebuter(self):
        """Transition to 'mis_au_rebut' state — irreversible."""
        self.write({'state': 'mis_au_rebut'})

    # ------------------------------------------------------------------
    # Smart button actions
    # ------------------------------------------------------------------

    def action_view_historique(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Historique — {self.name}',
            'res_model': 'telecom.equipment.historique',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id},
        }

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains('date_achat', 'date_installation')
    def _check_dates(self):
        for eq in self:
            if eq.date_achat and eq.date_installation:
                if eq.date_installation < eq.date_achat:
                    raise ValidationError(
                        "La date d'installation ne peut pas être antérieure à la date d'achat."
                    )

    @api.constrains('date_achat', 'date_fin_garantie')
    def _check_garantie(self):
        for eq in self:
            if eq.date_achat and eq.date_fin_garantie:
                if eq.date_fin_garantie < eq.date_achat:
                    raise ValidationError(
                        "La date de fin de garantie doit être postérieure à la date d'achat."
                    )


# ---------------------------------------------------------------------------
# telecom.equipment.historique
# ---------------------------------------------------------------------------

class TelecomEquipmentHistorique(models.Model):
    """
    Immutable event log for a telecom equipment asset.

    Records state changes, maintenance events, breakdowns, repairs, and
    any other significant event in the equipment lifecycle.
    Entries are created automatically on state change (via write() override)
    and can also be added manually by technicians.
    """

    _name = 'telecom.equipment.historique'
    _description = "Historique d'événement équipement"
    _order = 'date desc, id desc'
    _rec_name = 'description'

    # ------------------------------------------------------------------
    # Fields
    # ------------------------------------------------------------------

    equipment_id = fields.Many2one(
        'telecom.equipment',
        string='Équipement',
        required=True,
        ondelete='cascade',
        index=True,
    )
    date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now,
    )
    event_type = fields.Selection(
        selection=EVENT_TYPE_SELECTION,
        string="Type d'événement",
        required=True,
        default='autre',
    )
    description = fields.Text(
        string='Description',
        required=True,
    )
    technicien_id = fields.Many2one(
        'hr.employee',
        string='Technicien',
        ondelete='set null',
    )
    site_id = fields.Many2one(
        'telecom.site',
        string='Site concerné',
        ondelete='set null',
    )
    cout = fields.Monetary(
        string='Coût (MAD)',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        required=True,
        default=lambda self: self.env.ref('base.MAD', raise_if_not_found=False)
                            or self.env.ref('base.EUR'),
    )
