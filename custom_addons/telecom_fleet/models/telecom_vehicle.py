# -*- coding: utf-8 -*-
"""
telecom_vehicle.py
==================
Core model for the telecom fleet: company-owned field vehicles.
Each vehicle:
  - Is assigned to a terrain technician (hr.employee, telecom_technicien=True)
  - Has mandatory Moroccan legal documents (carte grise, assurance, vignette)
  - Tracks maintenance history and triggers km/date alerts
  - Can be linked to a mobile Odoo stock.warehouse (terrain stock)
  - Inherits mail.thread and mail.activity.mixin for chatter + activities
"""

from datetime import date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TelecomVehicle(models.Model):
    """Company fleet vehicle — independent of Odoo native fleet module."""

    _name = 'telecom.vehicle'
    _description = 'Véhicule Flotte Terrain'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'immatriculation asc'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # SQL constraints
    # ------------------------------------------------------------------

    _sql_constraints = [
        (
            'immatriculation_company_unique',
            'UNIQUE(immatriculation, company_id)',
            "Une immatriculation doit être unique par société.",
        ),
    ]

    # ------------------------------------------------------------------
    # Computed display name
    # ------------------------------------------------------------------

    name = fields.Char(
        string='Désignation',
        compute='_compute_name',
        store=True,
        readonly=True,
    )

    @api.depends('marque', 'modele', 'immatriculation')
    def _compute_name(self):
        for v in self:
            parts = ' '.join(filter(None, [v.marque, v.modele]))
            if v.immatriculation:
                parts = f"{parts} ({v.immatriculation})" if parts else v.immatriculation
            v.name = parts or _('Nouveau véhicule')

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------

    immatriculation = fields.Char(
        string='Immatriculation',
        required=True,
        tracking=True,
        help="Plaque d'immatriculation marocaine, ex : 12345-A-7",
    )

    marque = fields.Char(
        string='Marque',
        required=True,
        tracking=True,
        help='Marque constructeur, ex : Toyota, Renault…',
    )

    modele = fields.Char(
        string='Modèle',
        required=True,
        tracking=True,
        help='Modèle exact, ex : HiLux, Transit…',
    )

    annee = fields.Integer(
        string='Année de mise en circulation',
        tracking=True,
    )

    couleur = fields.Char(string='Couleur')

    carburant = fields.Selection(
        selection=[
            ('diesel', 'Diesel'),
            ('essence', 'Essence'),
            ('hybride', 'Hybride'),
            ('electrique', 'Électrique'),
        ],
        string='Carburant',
        tracking=True,
    )

    puissance_cv = fields.Integer(
        string='Puissance fiscale (CV)',
        help='Puissance fiscale en chevaux vapeur.',
    )

    kilometrage = fields.Integer(
        string='Kilométrage actuel',
        tracking=True,
        help='Relevé kilométrique actuel du compteur.',
    )

    vehicle_category = fields.Selection(
        selection=[
            ('camionnette', 'Camionnette / Pick-up'),
            ('utilitaire', 'Utilitaire léger'),
            ('van', 'Van / Fourgon'),
            ('berline', 'Berline / SUV'),
            ('moto', 'Moto'),
            ('autre', 'Autre'),
        ],
        string='Catégorie véhicule',
        default='camionnette',
    )

    photo = fields.Binary(
        string='Photo',
        attachment=True,
    )

    notes = fields.Text(string='Notes internes')

    active = fields.Boolean(
        string='Actif',
        default=True,
        tracking=True,
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    # ------------------------------------------------------------------
    # State / lifecycle
    # ------------------------------------------------------------------

    state = fields.Selection(
        selection=[
            ('disponible', 'Disponible'),
            ('en_mission', 'En mission'),
            ('en_entretien', 'En entretien'),
            ('hors_service', 'Hors service'),
            ('vendu', 'Vendu'),
        ],
        string='État',
        default='disponible',
        required=True,
        tracking=True,
        group_expand='_group_expand_states',
    )

    @api.model
    def _group_expand_states(self, states, domain, order):
        """Always display all states in grouped views."""
        return [s[0] for s in self._fields['state'].selection]

    # ------------------------------------------------------------------
    # Assignment
    # ------------------------------------------------------------------

    chauffeur_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Technicien assigné',
        domain=[('telecom_technicien', '=', True)],
        tracking=True,
        ondelete='set null',
    )

    date_affectation = fields.Date(
        string="Date d'affectation",
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Mandatory Moroccan legal documents
    # ------------------------------------------------------------------

    carte_grise_expiration = fields.Date(
        string='Expiration carte grise / visite technique',
        tracking=True,
        help='Date de validité de la visite technique / carte grise marocaine.',
    )

    assurance_expiration = fields.Date(
        string="Expiration assurance",
        tracking=True,
    )

    assurance_compagnie = fields.Char(string="Compagnie d'assurance")

    assurance_numero_police = fields.Char(string='Numéro de police')

    vignette_expiration = fields.Date(
        string='Expiration vignette fiscale',
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Maintenance scheduling
    # ------------------------------------------------------------------

    date_dernier_entretien = fields.Date(
        string='Date dernier entretien',
        tracking=True,
    )

    km_dernier_entretien = fields.Integer(
        string='Km au dernier entretien',
    )

    intervalle_entretien_km = fields.Integer(
        string='Intervalle entretien (km)',
        default=10000,
        help='Kilométrage entre deux entretiens (vidange, révision…)',
    )

    km_prochain_entretien = fields.Integer(
        string='Km prochain entretien',
        compute='_compute_km_prochain_entretien',
        store=True,
    )

    @api.depends('km_dernier_entretien', 'intervalle_entretien_km')
    def _compute_km_prochain_entretien(self):
        for v in self:
            v.km_prochain_entretien = (
                (v.km_dernier_entretien or 0) + (v.intervalle_entretien_km or 10000)
            )

    date_prochain_entretien = fields.Date(
        string='Date prochain entretien prévu',
        tracking=True,
    )

    entretien_ids = fields.One2many(
        comodel_name='telecom.vehicle.entretien',
        inverse_name='vehicle_id',
        string='Historique entretiens',
    )

    entretien_count = fields.Integer(
        string='Nb entretiens',
        compute='_compute_entretien_count',
    )

    @api.depends('entretien_ids')
    def _compute_entretien_count(self):
        for v in self:
            v.entretien_count = len(v.entretien_ids)

    # ------------------------------------------------------------------
    # Mobile stock warehouse
    # ------------------------------------------------------------------

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Entrepôt mobile',
        ondelete='set null',
        copy=False,
        help='Entrepôt Odoo lié à ce véhicule pour la gestion du stock terrain.',
    )

    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Emplacement stock',
        compute='_compute_location_id',
        store=False,
        help='Emplacement stock principal de l\'entrepôt mobile.',
    )

    @api.depends('warehouse_id')
    def _compute_location_id(self):
        for v in self:
            v.location_id = v.warehouse_id.lot_stock_id if v.warehouse_id else False

    # ------------------------------------------------------------------
    # Document expiry alerts (computed, stored — triggered by scheduler)
    # ------------------------------------------------------------------

    _ALERT_DAYS = 60  # warn 60 days before expiry

    assurance_expiring = fields.Boolean(
        string='Assurance expirant bientôt',
        compute='_compute_document_alerts',
        store=True,
        help='Vrai si l\'assurance expire dans les 60 prochains jours.',
    )

    visite_technique_expiring = fields.Boolean(
        string='Visite technique expirant bientôt',
        compute='_compute_document_alerts',
        store=True,
        help='Vrai si la carte grise/visite technique expire dans les 60 prochains jours.',
    )

    vignette_expiring = fields.Boolean(
        string='Vignette expirant bientôt',
        compute='_compute_document_alerts',
        store=True,
        help='Vrai si la vignette fiscale expire dans les 60 prochains jours.',
    )

    entretien_km_alerte = fields.Boolean(
        string='Alerte entretien km',
        compute='_compute_entretien_km_alerte',
        store=True,
        help='Vrai si le kilométrage actuel dépasse (km prochain entretien - 500).',
    )

    @api.depends(
        'assurance_expiration',
        'carte_grise_expiration',
        'vignette_expiration',
    )
    def _compute_document_alerts(self):
        """Flag documents expiring within _ALERT_DAYS calendar days."""
        today = date.today()
        threshold = today + timedelta(days=self._ALERT_DAYS)
        for v in self:
            # Assurance
            v.assurance_expiring = bool(
                v.assurance_expiration
                and today <= v.assurance_expiration <= threshold
            )
            # Visite technique / carte grise
            v.visite_technique_expiring = bool(
                v.carte_grise_expiration
                and today <= v.carte_grise_expiration <= threshold
            )
            # Vignette fiscale
            v.vignette_expiring = bool(
                v.vignette_expiration
                and today <= v.vignette_expiration <= threshold
            )

    @api.depends('kilometrage', 'km_prochain_entretien')
    def _compute_entretien_km_alerte(self):
        """Alert when current odometer is within 500 km of next service."""
        for v in self:
            if v.km_prochain_entretien and v.kilometrage:
                v.entretien_km_alerte = v.kilometrage >= (v.km_prochain_entretien - 500)
            else:
                v.entretien_km_alerte = False

    # ------------------------------------------------------------------
    # State transition actions (called from buttons)
    # ------------------------------------------------------------------

    def action_affecter_mission(self):
        """Set vehicle state to 'En mission'."""
        for v in self:
            if v.state not in ('disponible', 'en_entretien'):
                raise UserError(
                    _("Seul un véhicule disponible ou en entretien peut être mis en mission.")
                )
            v.write({'state': 'en_mission'})
            v.message_post(
                body=_("Véhicule affecté en mission."),
                subtype_xmlid='mail.mt_note',
            )
        return True

    def action_retour(self):
        """Return vehicle to 'Disponible' state."""
        for v in self:
            v.write({'state': 'disponible'})
            v.message_post(
                body=_("Véhicule retourné — disponible."),
                subtype_xmlid='mail.mt_note',
            )
        return True

    def action_entretien(self):
        """Set vehicle state to 'En entretien'."""
        for v in self:
            v.write({'state': 'en_entretien'})
            v.message_post(
                body=_("Véhicule mis en entretien."),
                subtype_xmlid='mail.mt_note',
            )
        return True

    def action_hors_service(self):
        """Set vehicle state to 'Hors service'."""
        for v in self:
            v.write({'state': 'hors_service'})
            v.message_post(
                body=_("Véhicule marqué hors service."),
                subtype_xmlid='mail.mt_note',
            )
        return True

    # ------------------------------------------------------------------
    # Mobile warehouse creation
    # ------------------------------------------------------------------

    def action_creer_entrepot_mobile(self):
        """
        Create a dedicated stock.warehouse for this vehicle.
        The warehouse name uses the immatriculation to remain unique.
        A short code is derived from the immatriculation (max 5 chars,
        alphanumeric only) to satisfy the stock.warehouse short_name constraint.
        """
        self.ensure_one()
        if self.warehouse_id:
            raise UserError(
                _("Cet entrepôt mobile existe déjà : %s") % self.warehouse_id.name
            )
        if not self.immatriculation:
            raise UserError(_("Veuillez renseigner l'immatriculation avant de créer l'entrepôt."))

        # Build a unique short code: keep alphanumeric chars, max 5, uppercase
        raw = ''.join(c for c in self.immatriculation if c.isalnum()).upper()
        short_code = raw[:5] or 'VEH'

        # Ensure short_code uniqueness
        existing_codes = self.env['stock.warehouse'].sudo().search([]).mapped('code')
        base = short_code
        idx = 1
        while short_code in existing_codes:
            suffix = str(idx)
            short_code = base[: 5 - len(suffix)] + suffix
            idx += 1

        warehouse = self.env['stock.warehouse'].sudo().create({
            'name': _('Véhicule %s') % self.immatriculation,
            'code': short_code,
            'company_id': self.company_id.id,
        })

        self.warehouse_id = warehouse
        self.message_post(
            body=_("Entrepôt mobile créé : %s") % warehouse.name,
            subtype_xmlid='mail.mt_note',
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Entrepôt créé'),
                'message': _("L'entrepôt mobile %s a été créé avec succès.") % warehouse.name,
                'sticky': False,
                'type': 'success',
            },
        }

    # ------------------------------------------------------------------
    # Smart button action: open maintenance records
    # ------------------------------------------------------------------

    def action_view_entretiens(self):
        """Open the maintenance history for this vehicle."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Entretiens — %s') % self.name,
            'res_model': 'telecom.vehicle.entretien',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
