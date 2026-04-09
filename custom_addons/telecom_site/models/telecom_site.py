# -*- coding: utf-8 -*-
"""
telecom_site models
===================
Central entity for managing physical telecom sites:
pylons, rooftops, shelters, FTTH cabinets, datacenters, etc.

Models defined here:
- telecom.technologie  : reference table for radio/fibre technologies
- telecom.site         : main site model (inherits mail.thread)
- telecom.site.document: documents attached to a site
"""

from datetime import date, timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError


# ---------------------------------------------------------------------------
# telecom.technologie — reference model for deployed technologies
# ---------------------------------------------------------------------------

class TelecomTechnologie(models.Model):
    """Reference table: technologies deployable on a site (2G, 4G, FTTH…)."""

    _name = 'telecom.technologie'
    _description = 'Technologie télécom'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Technologie',
        required=True,
    )
    code = fields.Char(
        string='Code',
        size=10,
    )
    sequence = fields.Integer(
        string='Séquence',
        default=10,
    )
    active = fields.Boolean(
        default=True,
    )
    color = fields.Integer(
        string='Couleur',
        default=0,
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Cette technologie existe déjà.'),
        ('code_uniq', 'UNIQUE(code)', 'Ce code technologie est déjà utilisé.'),
    ]


# ---------------------------------------------------------------------------
# telecom.site — main model
# ---------------------------------------------------------------------------

# Selection values defined as module-level constants for reuse in views/reports
SITE_TYPE_SELECTION = [
    ('pylone_greenfield', 'Pylône Greenfield'),
    ('rooftop', 'Rooftop'),
    ('shelter', 'Shelter'),
    ('indoor_das', 'Indoor / DAS'),
    ('datacenter', 'Datacenter'),
    ('cabinet_ftth', 'Cabinet FTTH'),
    ('chambre_tirage', 'Chambre de tirage'),
    ('autre', 'Autre'),
]

STATE_SELECTION = [
    ('prospection', 'Prospection'),
    ('etude', 'Étude technique'),
    ('autorisation', 'En cours d\'autorisation'),
    ('deploiement', 'Déploiement'),
    ('livre', 'Livré / Opérationnel'),
    ('maintenance', 'En maintenance'),
    ('desactive', 'Désactivé'),
]

WILAYA_SELECTION = [
    ('casablanca_settat', 'Casablanca-Settat'),
    ('rabat_sale_kenitra', 'Rabat-Salé-Kénitra'),
    ('marrakech_safi', 'Marrakech-Safi'),
    ('fes_meknes', 'Fès-Meknès'),
    ('tanger_tetouan_alhoceima', 'Tanger-Tétouan-Al Hoceïma'),
    ('souss_massa', 'Souss-Massa'),
    ('draa_tafilalet', 'Drâa-Tafilalet'),
    ('beni_mellal_khenifra', 'Béni Mellal-Khénifra'),
    ('oriental', 'L\'Oriental'),
    ('guelmim_oued_noun', 'Guelmim-Oued Noun'),
    ('laayoune_sakia_el_hamra', 'Laâyoune-Sakia El Hamra'),
    ('dakhla_oued_ed_dahab', 'Dakhla-Oued Ed-Dahab'),
]

DOCUMENT_TYPE_SELECTION = [
    ('plan', 'Plan / Schéma'),
    ('pv_reception', 'PV de réception'),
    ('autorisation', 'Autorisation administrative'),
    ('photo', 'Photo'),
    ('rapport', 'Rapport technique'),
    ('contrat_bail', 'Contrat de bail'),
    ('autre', 'Autre'),
]


class TelecomSite(models.Model):
    """
    Physical telecom site.

    Central entity linking sites to interventions, projects, equipment
    and all operational data. Inherits mail.thread for chatter/tracking
    and mail.activity.mixin for scheduled activities.
    """

    _name = 'telecom.site'
    _description = 'Site télécom'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code_interne asc'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------

    name = fields.Char(
        string='Nom du site',
        required=True,
        tracking=True,
    )
    code_interne = fields.Char(
        string='Code interne',
        required=True,
        copy=False,
        tracking=True,
        help="Code interne unique par société (ex : TLM-001)",
    )
    code_operateur = fields.Char(
        string='Code opérateur',
        tracking=True,
        help="Code attribué par l'opérateur hébergeur (ex : IAM-CASA-001)",
    )
    site_type = fields.Selection(
        selection=SITE_TYPE_SELECTION,
        string='Type de site',
        required=True,
        default='pylone_greenfield',
        tracking=True,
    )
    state = fields.Selection(
        selection=STATE_SELECTION,
        string='État',
        required=True,
        default='prospection',
        tracking=True,
    )
    active = fields.Boolean(
        default=True,
    )
    color = fields.Integer(
        string='Couleur kanban',
        default=0,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    # ------------------------------------------------------------------
    # Geographical location
    # ------------------------------------------------------------------

    wilaya = fields.Selection(
        selection=WILAYA_SELECTION,
        string='Région (Wilaya)',
        tracking=True,
    )
    commune = fields.Char(
        string='Commune / Ville',
    )
    adresse = fields.Char(
        string='Adresse complète',
    )
    gps_lat = fields.Float(
        string='Latitude GPS',
        digits=(10, 6),
        help="Latitude décimale (WGS84). Ex : 33.589886",
    )
    gps_lng = fields.Float(
        string='Longitude GPS',
        digits=(10, 6),
        help="Longitude décimale (WGS84). Ex : -7.603869",
    )

    # ------------------------------------------------------------------
    # Operators and lessor
    # ------------------------------------------------------------------

    operateur_ids = fields.Many2many(
        'res.partner',
        'telecom_site_operator_rel',
        'site_id',
        'partner_id',
        string='Opérateurs hébergés',
        domain="[('partner_type', '=', 'operator')]",
        help="Opérateurs télécom hébergeant des équipements sur ce site",
    )
    bailleur_id = fields.Many2one(
        'res.partner',
        string='Bailleur',
        domain="[('partner_type', '=', 'lessor')]",
        tracking=True,
        help="Propriétaire du terrain ou du bâtiment",
    )

    # ------------------------------------------------------------------
    # Lease (bail)
    # ------------------------------------------------------------------

    bail_reference = fields.Char(
        string='Référence contrat de bail',
    )
    bail_date_debut = fields.Date(
        string='Début du bail',
    )
    bail_date_fin = fields.Date(
        string='Fin du bail',
        tracking=True,
    )
    loyer_mensuel = fields.Monetary(
        string='Loyer mensuel (MAD)',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        required=True,
        default=lambda self: self.env.ref('base.MAD', raise_if_not_found=False)
                            or self.env.ref('base.EUR'),
    )
    bail_expiration_warning = fields.Boolean(
        string='Bail expire bientôt',
        compute='_compute_bail_expiration_warning',
        store=True,
        help="True when lease expires within 3 months",
    )

    # ------------------------------------------------------------------
    # Access & security
    # ------------------------------------------------------------------

    acces_instructions = fields.Text(
        string="Instructions d'accès",
        help="Itinéraire, code cadenas, contact gardien, etc.",
    )
    contact_local = fields.Char(
        string='Contact local',
        help="Nom et numéro de téléphone du contact sur place",
    )
    acces_h24 = fields.Boolean(
        string='Accès 24h/24',
        default=False,
    )
    autorisation_prealable = fields.Boolean(
        string='Autorisation préalable requise',
        default=True,
    )

    # ------------------------------------------------------------------
    # Technical characteristics
    # ------------------------------------------------------------------

    hauteur_pylone = fields.Float(
        string='Hauteur pylône (m)',
        digits=(6, 2),
    )
    puissance_electrique = fields.Float(
        string='Puissance électrique (kVA)',
        digits=(6, 2),
    )
    groupe_electrogene = fields.Boolean(
        string='Groupe électrogène',
        default=False,
    )
    batterie_backup = fields.Boolean(
        string='Batterie de secours',
        default=False,
    )
    climatisation = fields.Boolean(
        string='Climatisation',
        default=False,
    )
    technologie_ids = fields.Many2many(
        'telecom.technologie',
        'telecom_site_technologie_rel',
        'site_id',
        'technologie_id',
        string='Technologies déployées',
    )

    # ------------------------------------------------------------------
    # Related records
    # ------------------------------------------------------------------

    document_ids = fields.One2many(
        'telecom.site.document',
        'site_id',
        string='Documents',
    )
    document_count = fields.Integer(
        string='Nb documents',
        compute='_compute_document_count',
    )

    # Placeholder — actual compute will be overridden by telecom_intervention
    intervention_count = fields.Integer(
        string='Nb interventions',
        compute='_compute_intervention_count',
    )

    # ------------------------------------------------------------------
    # Miscellaneous
    # ------------------------------------------------------------------

    notes = fields.Text(
        string='Observations générales',
    )

    # ------------------------------------------------------------------
    # SQL constraints
    # ------------------------------------------------------------------

    _sql_constraints = [
        (
            'code_interne_company_uniq',
            'UNIQUE(code_interne, company_id)',
            'Le code interne doit être unique par société.',
        ),
    ]

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------

    @api.depends('bail_date_fin')
    def _compute_bail_expiration_warning(self):
        """Flag sites whose lease expires within 90 days."""
        today = date.today()
        threshold = today + timedelta(days=90)
        for site in self:
            if site.bail_date_fin and today <= site.bail_date_fin <= threshold:
                site.bail_expiration_warning = True
            else:
                site.bail_expiration_warning = False

    def _compute_document_count(self):
        """Count documents linked to each site."""
        for site in self:
            site.document_count = len(site.document_ids)

    def _compute_intervention_count(self):
        """
        Placeholder compute for intervention count.
        The telecom_intervention module will override this method
        with a proper search against telecom.intervention records.
        """
        for site in self:
            site.intervention_count = 0

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains('bail_date_debut', 'bail_date_fin')
    def _check_bail_dates(self):
        for site in self:
            if site.bail_date_debut and site.bail_date_fin:
                if site.bail_date_fin < site.bail_date_debut:
                    raise ValidationError(
                        "La date de fin de bail doit être postérieure à la date de début."
                    )

    @api.constrains('gps_lat')
    def _check_gps_lat(self):
        for site in self:
            if site.gps_lat and not (-90.0 <= site.gps_lat <= 90.0):
                raise ValidationError(
                    "La latitude GPS doit être comprise entre -90 et 90."
                )

    @api.constrains('gps_lng')
    def _check_gps_lng(self):
        for site in self:
            if site.gps_lng and not (-180.0 <= site.gps_lng <= 180.0):
                raise ValidationError(
                    "La longitude GPS doit être comprise entre -180 et 180."
                )

    # ------------------------------------------------------------------
    # Business actions
    # ------------------------------------------------------------------

    def action_set_etude(self):
        self.write({'state': 'etude'})

    def action_set_autorisation(self):
        self.write({'state': 'autorisation'})

    def action_set_deploiement(self):
        self.write({'state': 'deploiement'})

    def action_set_livre(self):
        self.write({'state': 'livre'})

    def action_set_maintenance(self):
        self.write({'state': 'maintenance'})

    def action_set_desactive(self):
        self.write({'state': 'desactive'})

    def action_view_documents(self):
        """Smart-button action: open documents linked to this site."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents du site',
            'res_model': 'telecom.site.document',
            'view_mode': 'list,form',
            'domain': [('site_id', '=', self.id)],
            'context': {'default_site_id': self.id},
        }

    def action_open_in_maps(self):
        """Open GPS coordinates in Google Maps (client-side URL action)."""
        self.ensure_one()
        if not self.gps_lat or not self.gps_lng:
            raise ValidationError(
                "Les coordonnées GPS de ce site ne sont pas renseignées."
            )
        url = f"https://maps.google.com/?q={self.gps_lat},{self.gps_lng}"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }


# ---------------------------------------------------------------------------
# telecom.site.document — documents linked to a site
# ---------------------------------------------------------------------------

class TelecomSiteDocument(models.Model):
    """Documents and attachments associated with a telecom site."""

    _name = 'telecom.site.document'
    _description = 'Document de site télécom'
    _order = 'date desc, name'
    _rec_name = 'name'

    site_id = fields.Many2one(
        'telecom.site',
        string='Site',
        required=True,
        ondelete='cascade',
        index=True,
    )
    name = fields.Char(
        string='Titre du document',
        required=True,
    )
    document_type = fields.Selection(
        selection=DOCUMENT_TYPE_SELECTION,
        string='Type de document',
        default='autre',
    )
    date = fields.Date(
        string='Date',
        default=fields.Date.today,
    )
    file = fields.Binary(
        string='Fichier',
        required=True,
        attachment=True,
    )
    filename = fields.Char(
        string='Nom du fichier',
    )
    description = fields.Text(
        string='Description',
    )
