# -*- coding: utf-8 -*-
"""
telecom_intervention models
============================
Core model for field work orders (Bons d'Intervention — BI).

Models defined here:
- telecom.intervention       : main BI model
- telecom.intervention.photo : photos attached to a BI
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


# ---------------------------------------------------------------------------
# Selection constants — referenced by model and views
# ---------------------------------------------------------------------------

INTERVENTION_TYPE_SELECTION = [
    ('preventive', 'Préventive'),
    ('corrective', 'Corrective (dépannage)'),
    ('installation', 'Installation / Mise en service'),
    ('audit', 'Audit technique'),
    ('depose', 'Dépose équipement'),
]

STATE_SELECTION = [
    ('draft', 'Brouillon'),
    ('planifie', 'Planifié'),
    ('en_cours', 'En cours'),
    ('termine', 'Terminé (terrain)'),
    ('valide', 'Validé (chef)'),
    ('facture', 'Facturé'),
    ('annule', 'Annulé'),
]

PRIORITY_SELECTION = [
    ('0', 'Normal'),
    ('1', 'Urgent'),
    ('2', 'Très urgent'),
]

PHOTO_TYPE_SELECTION = [
    ('avant', 'Avant intervention'),
    ('pendant', 'Pendant intervention'),
    ('apres', 'Après intervention'),
    ('anomalie', 'Anomalie constatée'),
    ('autre', 'Autre'),
]


# ---------------------------------------------------------------------------
# telecom.intervention — Bon d'Intervention
# ---------------------------------------------------------------------------

class TelecomIntervention(models.Model):
    """
    Bon d'Intervention (BI).

    Tracks the full lifecycle of a field work order: from initial creation
    (draft) through planning, execution, chef validation, and invoicing.
    Inherits mail.thread for full audit trail and mail.activity.mixin for
    scheduled reminders.
    """

    _name = 'telecom.intervention'
    _description = "Bon d'Intervention télécom"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_planifiee desc, name desc'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------

    name = fields.Char(
        string="N° Bon d'Intervention",
        required=True,
        copy=False,
        readonly=True,
        default='Nouveau',
        tracking=True,
        help="Numéro généré automatiquement : BI/AAAA/XXXX",
    )
    intervention_type = fields.Selection(
        selection=INTERVENTION_TYPE_SELECTION,
        string="Type d'intervention",
        required=True,
        tracking=True,
        default='corrective',
    )
    priority = fields.Selection(
        selection=PRIORITY_SELECTION,
        string='Priorité',
        default='0',
        tracking=True,
    )
    state = fields.Selection(
        selection=STATE_SELECTION,
        string='État',
        default='draft',
        required=True,
        copy=False,
        tracking=True,
    )
    active = fields.Boolean(
        default=True,
    )
    color = fields.Integer(
        string='Couleur kanban',
        default=0,
    )

    # ------------------------------------------------------------------
    # Site and operator
    # ------------------------------------------------------------------

    site_id = fields.Many2one(
        'telecom.site',
        string='Site',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
    )
    operateur_id = fields.Many2one(
        'res.partner',
        string='Opérateur',
        domain="[('partner_type', '=', 'operator')]",
        tracking=True,
        help="Opérateur concerné — rempli automatiquement depuis le site",
    )

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------

    date_planifiee = fields.Datetime(
        string='Date planifiée',
        required=True,
        tracking=True,
    )
    duree_estimee = fields.Float(
        string='Durée estimée (h)',
        digits=(4, 2),
        help="Durée prévisionnelle en heures",
    )
    chef_chantier_id = fields.Many2one(
        'hr.employee',
        string='Chef de chantier',
        tracking=True,
        help="Chef de chantier responsable de cette intervention",
    )
    technician_ids = fields.Many2many(
        'hr.employee',
        'telecom_intervention_technician_rel',
        'intervention_id',
        'employee_id',
        string='Techniciens affectés',
        help="Techniciens terrain affectés à cette intervention",
    )
    habilitations_requises_text = fields.Text(
        string='Habilitations requises',
        help="Describe required qualifications and certifications for this intervention",
    )

    # ------------------------------------------------------------------
    # Execution timestamps
    # ------------------------------------------------------------------

    date_debut_reel = fields.Datetime(
        string='Début réel',
        copy=False,
        tracking=True,
    )
    date_fin_reel = fields.Datetime(
        string='Fin réelle',
        copy=False,
        tracking=True,
    )
    duree_reelle = fields.Float(
        string='Durée réelle (h)',
        digits=(4, 2),
        compute='_compute_duree_reelle',
        store=True,
        help="Computed from actual start/end timestamps",
    )

    # ------------------------------------------------------------------
    # SLA
    # ------------------------------------------------------------------

    sla_delai_heures = fields.Integer(
        string='Délai SLA (heures)',
        default=48,
        help="Délai contractuel SLA en heures à compter de la date planifiée",
    )
    sla_echeance = fields.Datetime(
        string='Échéance SLA',
        compute='_compute_sla_echeance',
        store=True,
        help="date_planifiee + sla_delai_heures",
    )
    sla_depasse = fields.Boolean(
        string='SLA dépassé',
        compute='_compute_sla_depasse',
        store=True,
        help="True when current datetime exceeds sla_echeance and BI is not yet validated",
    )
    sla_couleur = fields.Integer(
        string='Couleur SLA',
        compute='_compute_sla_couleur',
        help="Kanban color indicator: 0=ok, 1=warning, 2=overdue",
    )

    # ------------------------------------------------------------------
    # Rapport d'intervention
    # ------------------------------------------------------------------

    description_travaux = fields.Text(
        string='Description des travaux effectués',
    )
    problemes_rencontres = fields.Text(
        string='Problèmes rencontrés',
    )
    travaux_restants = fields.Text(
        string='Travaux restants / Réserves',
    )

    # ------------------------------------------------------------------
    # Related records
    # ------------------------------------------------------------------

    photo_ids = fields.One2many(
        'telecom.intervention.photo',
        'intervention_id',
        string='Photos',
    )
    photo_count = fields.Integer(
        string='Nb photos',
        compute='_compute_photo_count',
    )
    materiel_consomme_ids = fields.One2many(
        'telecom.materiel.consomme',
        'intervention_id',
        string='Matériels consommés',
    )
    materiel_count = fields.Integer(
        string='Nb matériels',
        compute='_compute_materiel_count',
    )

    # ------------------------------------------------------------------
    # Signature
    # ------------------------------------------------------------------

    signature_technicien = fields.Binary(
        string='Signature technicien',
        attachment=True,
        help="Electronic signature of the lead technician",
    )
    signature_client = fields.Binary(
        string='Signature client',
        attachment=True,
        help="Electronic signature of the client representative",
    )
    nom_signataire_client = fields.Char(
        string='Nom représentant client',
    )
    date_signature = fields.Datetime(
        string='Date de signature',
        copy=False,
    )

    # ------------------------------------------------------------------
    # Financial link
    # ------------------------------------------------------------------

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Commande client',
        copy=False,
        help="Commande client liée si facturation à l'acte",
    )
    invoice_ids = fields.Many2many(
        'account.move',
        'telecom_intervention_invoice_rel',
        'intervention_id',
        'invoice_id',
        string='Factures liées',
        copy=False,
        domain="[('move_type', 'in', ['out_invoice', 'out_refund'])]",
    )
    invoice_count = fields.Integer(
        string='Nb factures',
        compute='_compute_invoice_count',
    )

    # ------------------------------------------------------------------
    # Company / tracking
    # ------------------------------------------------------------------

    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Créé par',
        default=lambda self: self.env.user,
        index=True,
    )

    # ------------------------------------------------------------------
    # SQL constraints
    # ------------------------------------------------------------------

    _sql_constraints = [
        (
            'name_company_uniq',
            'UNIQUE(name, company_id)',
            "Ce numéro de Bon d'Intervention existe déjà pour cette société.",
        ),
    ]

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------

    @api.depends('date_debut_reel', 'date_fin_reel')
    def _compute_duree_reelle(self):
        """Compute actual duration in hours from real start/end timestamps."""
        for rec in self:
            if rec.date_debut_reel and rec.date_fin_reel:
                delta = rec.date_fin_reel - rec.date_debut_reel
                rec.duree_reelle = delta.total_seconds() / 3600.0
            else:
                rec.duree_reelle = 0.0

    @api.depends('date_planifiee', 'sla_delai_heures')
    def _compute_sla_echeance(self):
        """SLA deadline = planned date + contractual delay in hours."""
        from datetime import timedelta
        for rec in self:
            if rec.date_planifiee and rec.sla_delai_heures:
                rec.sla_echeance = rec.date_planifiee + timedelta(
                    hours=rec.sla_delai_heures
                )
            else:
                rec.sla_echeance = False

    @api.depends('sla_echeance', 'state')
    def _compute_sla_depasse(self):
        """SLA is breached when now > sla_echeance and the BI is not yet validated."""
        now = fields.Datetime.now()
        terminal_states = {'valide', 'facture', 'annule'}
        for rec in self:
            if (
                rec.sla_echeance
                and rec.state not in terminal_states
                and now > rec.sla_echeance
            ):
                rec.sla_depasse = True
            else:
                rec.sla_depasse = False

    def _compute_sla_couleur(self):
        """
        Return a kanban color integer for the SLA status.
        0 = on track (green), 1 = warning within 24 h (orange), 2 = overdue (red).
        """
        from datetime import timedelta
        now = fields.Datetime.now()
        for rec in self:
            if not rec.sla_echeance or rec.state in ('valide', 'facture', 'annule'):
                rec.sla_couleur = 0
            elif now > rec.sla_echeance:
                rec.sla_couleur = 2
            elif now > rec.sla_echeance - timedelta(hours=24):
                rec.sla_couleur = 1
            else:
                rec.sla_couleur = 0

    def _compute_photo_count(self):
        for rec in self:
            rec.photo_count = len(rec.photo_ids)

    def _compute_materiel_count(self):
        for rec in self:
            rec.materiel_count = len(rec.materiel_consomme_ids)

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------

    @api.onchange('site_id')
    def _onchange_site_id(self):
        """Auto-fill operator from the first operator linked to the site."""
        if self.site_id and self.site_id.operateur_ids:
            self.operateur_id = self.site_id.operateur_ids[0]
        elif not self.site_id:
            self.operateur_id = False

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """Generate BI number from ir.sequence on creation."""
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'telecom.intervention'
                ) or 'Nouveau'
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------

    def action_planifier(self):
        """Transition draft → planifie."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    _("Seuls les bons en brouillon peuvent être planifiés.")
                )
            if not rec.date_planifiee:
                raise UserError(
                    _("Veuillez renseigner la date planifiée avant de planifier le bon.")
                )
        self.write({'state': 'planifie'})

    def action_demarrer(self):
        """Transition planifie → en_cours; record actual start time."""
        for rec in self:
            if rec.state != 'planifie':
                raise UserError(
                    _("Seuls les bons planifiés peuvent être démarrés.")
                )
        self.write({
            'state': 'en_cours',
            'date_debut_reel': fields.Datetime.now(),
        })

    def action_terminer(self):
        """Transition en_cours → termine; record actual end time."""
        for rec in self:
            if rec.state != 'en_cours':
                raise UserError(
                    _("Seuls les bons en cours peuvent être terminés.")
                )
        self.write({
            'state': 'termine',
            'date_fin_reel': fields.Datetime.now(),
        })

    def action_valider(self):
        """
        Transition termine → valide.
        Only users in the chef de chantier or higher security groups may validate.
        """
        chef_group = self.env.ref('telecom_base.group_telecom_chef_chantier', raise_if_not_found=False)
        resp_group = self.env.ref('telecom_base.group_telecom_responsable', raise_if_not_found=False)
        admin_group = self.env.ref('telecom_base.group_telecom_admin', raise_if_not_found=False)

        allowed_groups = [g for g in [chef_group, resp_group, admin_group] if g]
        user_groups = self.env.user.groups_id

        if not any(g in user_groups for g in allowed_groups):
            raise UserError(
                _("Seul un chef de chantier, responsable ou administrateur "
                  "peut valider un bon d'intervention.")
            )
        for rec in self:
            if rec.state != 'termine':
                raise UserError(
                    _("Seuls les bons terminés peuvent être validés.")
                )
        self.write({'state': 'valide'})

    def action_annuler(self):
        """Transition any active state → annule."""
        for rec in self:
            if rec.state == 'facture':
                raise UserError(
                    _("Un bon déjà facturé ne peut pas être annulé.")
                )
        self.write({'state': 'annule'})

    def action_reset_draft(self):
        """Transition annule → draft."""
        for rec in self:
            if rec.state != 'annule':
                raise UserError(
                    _("Seuls les bons annulés peuvent être remis en brouillon.")
                )
        self.write({'state': 'draft'})

    def action_view_invoices(self):
        """Smart-button: open invoices linked to this BI."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Factures',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'context': {'default_move_type': 'out_invoice'},
        }

    def action_view_photos(self):
        """Smart-button: open photos for this BI."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Photos',
            'res_model': 'telecom.intervention.photo',
            'view_mode': 'list,form',
            'domain': [('intervention_id', '=', self.id)],
            'context': {'default_intervention_id': self.id},
        }

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains('date_debut_reel', 'date_fin_reel')
    def _check_dates_reel(self):
        for rec in self:
            if rec.date_debut_reel and rec.date_fin_reel:
                if rec.date_fin_reel < rec.date_debut_reel:
                    raise ValidationError(
                        _("La date de fin réelle doit être postérieure à la date de début réelle.")
                    )


# ---------------------------------------------------------------------------
# telecom.intervention.photo — photos attached to a BI
# ---------------------------------------------------------------------------

class TelecomInterventionPhoto(models.Model):
    """
    Photo linked to a field work order.

    Stores an image with a caption, type (before/during/after/anomaly)
    and the timestamp when it was taken.
    """

    _name = 'telecom.intervention.photo'
    _description = "Photo d'intervention"
    _order = 'photo_type, date_prise'
    _rec_name = 'name'

    intervention_id = fields.Many2one(
        'telecom.intervention',
        string='Bon d\'Intervention',
        required=True,
        ondelete='cascade',
        index=True,
    )
    name = fields.Char(
        string='Légende',
        required=True,
    )
    photo = fields.Binary(
        string='Photo',
        required=True,
        attachment=True,
    )
    photo_filename = fields.Char(
        string='Nom du fichier',
    )
    photo_type = fields.Selection(
        selection=PHOTO_TYPE_SELECTION,
        string='Type de photo',
        default='autre',
        required=True,
    )
    date_prise = fields.Datetime(
        string='Date de prise',
        default=fields.Datetime.now,
    )
