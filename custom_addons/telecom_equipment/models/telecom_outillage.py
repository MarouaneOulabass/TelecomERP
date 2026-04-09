# -*- coding: utf-8 -*-
"""
telecom_outillage
=================
Field measurement tools and instruments used by telecom technicians.

Tracks calibration cycles, assignment to technicians, and availability
for planning field missions.

Examples: OTDR Yokogawa AQ7275, Rohde & Schwarz spectrum analyzer,
          Anritsu Site Master antenna analyzer, Fluke multimeter.
"""

from datetime import date, timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


# ---------------------------------------------------------------------------
# Selection constants
# ---------------------------------------------------------------------------

OUTILLAGE_TYPE_SELECTION = [
    ('otdr', 'OTDR (réflectomètre fibre)'),
    ('analyseur_spectre', 'Analyseur de spectre'),
    ('testeur_fibre', 'Testeur puissance fibre'),
    ('multimetre', 'Multimètre'),
    ('analyseur_antenne', 'Analyseur antenne / Site Master'),
    ('testeur_cable', 'Testeur câble'),
    ('autre', 'Autre'),
]

STATE_SELECTION = [
    ('disponible', 'Disponible'),
    ('en_mission', 'En mission (affecté)'),
    ('en_etalonnage', 'En étalonnage / calibration'),
    ('en_reparation', 'En réparation'),
    ('hors_service', 'Hors service'),
]


# ---------------------------------------------------------------------------
# telecom.outillage
# ---------------------------------------------------------------------------

class TelecomOutillage(models.Model):
    """
    Field measurement tool / instrument.

    Manages the full lifecycle of precision measurement equipment:
    calibration scheduling, technician assignment, and repair tracking.
    Inherits mail.thread for change tracking.
    """

    _name = 'telecom.outillage'
    _description = 'Outillage terrain télécom'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'outillage_type, name'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------

    name = fields.Char(
        string='Désignation',
        required=True,
        tracking=True,
        help='Ex: "OTDR Yokogawa AQ7275"',
    )
    outillage_type = fields.Selection(
        selection=OUTILLAGE_TYPE_SELECTION,
        string="Type d'outillage",
        required=True,
        tracking=True,
        default='autre',
    )
    numero_serie = fields.Char(
        string='Numéro de série',
        required=True,
        copy=False,
        tracking=True,
        index=True,
    )
    marque = fields.Char(
        string='Marque',
    )
    modele = fields.Char(
        string='Modèle',
    )

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    state = fields.Selection(
        selection=STATE_SELECTION,
        string='État',
        required=True,
        default='disponible',
        copy=False,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Assignment
    # ------------------------------------------------------------------

    affecte_a = fields.Many2one(
        'hr.employee',
        string='Technicien affecté',
        tracking=True,
        ondelete='set null',
        help="Technicien auquel l'outil est actuellement affecté",
    )
    date_affectation = fields.Date(
        string="Date d'affectation",
        tracking=True,
    )
    date_retour_prevu = fields.Date(
        string='Date de retour prévue',
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    date_dernier_etalonnage = fields.Date(
        string='Date du dernier étalonnage',
        tracking=True,
    )
    periodicite_etalonnage_mois = fields.Integer(
        string='Périodicité étalonnage (mois)',
        default=12,
        help="Interval in months between mandatory calibrations",
    )
    date_prochain_etalonnage = fields.Date(
        string='Date du prochain étalonnage',
        compute='_compute_date_prochain_etalonnage',
        store=True,
        help="Computed: date_dernier_etalonnage + periodicite_etalonnage_mois",
    )
    etalonnage_expiring = fields.Boolean(
        string='Étalonnage expire bientôt',
        compute='_compute_etalonnage_expiring',
        store=True,
        help="True when next calibration date is within the next 60 days",
    )
    organisme_etalonnage = fields.Char(
        string="Organisme d'étalonnage",
        help="Laboratoire ou organisme accrédité réalisant l'étalonnage",
    )
    document_etalonnage = fields.Binary(
        string="Certificat d'étalonnage",
        attachment=True,
        help="Scan or PDF of the latest calibration certificate",
    )
    document_etalonnage_filename = fields.Char(
        string="Nom du fichier certificat",
    )

    # ------------------------------------------------------------------
    # Miscellaneous
    # ------------------------------------------------------------------

    notes = fields.Text(
        string='Notes',
    )
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
            'Ce numéro de série d\'outillage existe déjà pour cette société.',
        ),
    ]

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------

    @api.depends('date_dernier_etalonnage', 'periodicite_etalonnage_mois')
    def _compute_date_prochain_etalonnage(self):
        """
        Next calibration date = last calibration date + periodicity in months.
        Uses a simple 30-day-per-month approximation for stability.
        """
        for tool in self:
            if tool.date_dernier_etalonnage and tool.periodicite_etalonnage_mois:
                delta_days = tool.periodicite_etalonnage_mois * 30
                tool.date_prochain_etalonnage = (
                    tool.date_dernier_etalonnage + timedelta(days=delta_days)
                )
            else:
                tool.date_prochain_etalonnage = False

    @api.depends('date_prochain_etalonnage')
    def _compute_etalonnage_expiring(self):
        """Flag tools whose calibration expires within the next 60 days."""
        today = date.today()
        threshold = today + timedelta(days=60)
        for tool in self:
            if (
                tool.date_prochain_etalonnage
                and today <= tool.date_prochain_etalonnage <= threshold
            ):
                tool.etalonnage_expiring = True
            else:
                tool.etalonnage_expiring = False

    # ------------------------------------------------------------------
    # State transition actions
    # ------------------------------------------------------------------

    def action_affecter(self):
        """Transition to 'en_mission' — tool assigned to a technician."""
        for tool in self:
            if tool.state != 'disponible':
                raise UserError(
                    "Seul un outillage disponible peut être affecté à un technicien."
                )
            if not tool.affecte_a:
                raise UserError(
                    "Veuillez renseigner le technicien avant d'affecter l'outillage."
                )
        self.write({
            'state': 'en_mission',
            'date_affectation': fields.Date.today(),
        })

    def action_retourner(self):
        """Transition back to 'disponible' — tool returned from mission."""
        for tool in self:
            if tool.state != 'en_mission':
                raise UserError(
                    "Seul un outillage en mission peut être retourné."
                )
        self.write({
            'state': 'disponible',
            'affecte_a': False,
            'date_retour_prevu': False,
        })

    def action_envoyer_etalonnage(self):
        """Transition to 'en_etalonnage'."""
        for tool in self:
            if tool.state not in ('disponible', 'en_mission'):
                raise UserError(
                    "L'outillage doit être disponible ou en mission pour être envoyé en étalonnage."
                )
        self.write({'state': 'en_etalonnage'})

    def action_retour_etalonnage(self):
        """Return from calibration — update last calibration date."""
        self.write({
            'state': 'disponible',
            'date_dernier_etalonnage': fields.Date.today(),
        })

    def action_envoyer_reparation(self):
        """Transition to 'en_reparation'."""
        self.write({'state': 'en_reparation'})

    def action_mettre_hors_service(self):
        """Transition to 'hors_service'."""
        self.write({'state': 'hors_service'})

    def action_remettre_disponible(self):
        """Force back to 'disponible' (e.g. after repair)."""
        self.write({'state': 'disponible'})

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains('date_affectation', 'date_retour_prevu')
    def _check_dates_affectation(self):
        for tool in self:
            if tool.date_affectation and tool.date_retour_prevu:
                if tool.date_retour_prevu < tool.date_affectation:
                    raise ValidationError(
                        "La date de retour prévue doit être postérieure à la date d'affectation."
                    )

    @api.constrains('periodicite_etalonnage_mois')
    def _check_periodicite(self):
        for tool in self:
            if tool.periodicite_etalonnage_mois <= 0:
                raise ValidationError(
                    "La périodicité d'étalonnage doit être strictement positive."
                )
