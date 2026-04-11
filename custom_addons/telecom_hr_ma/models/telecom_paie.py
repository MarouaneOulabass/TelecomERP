# -*- coding: utf-8 -*-
"""
telecom_paie.py
===============
telecom.paie.bulletin: Custom Moroccan payslip model (no dependency on Enterprise hr_payroll).

Implements 2024 Moroccan payroll rules:
- CNSS salarié  : 4.48% (base plafonnée à 6 000 MAD/mois)
- CNSS patronal : 10.64% (same base)
- AMO salarié   : 2.26% (base = salaire brut)
- AMO patronal  : 3.96%
- CIMR          : taux variable par employé
- Frais professionnels : 20%, plafonné 2 500 MAD/mois (30 000/an)
- IR (barème 2024)     : see _compute_ir_annuel()
- Déduction IR enfants : 30 MAD/mois par charge au-delà de la 1ère part
"""

from datetime import date
import calendar
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class TelecomPaieBulletin(models.Model):
    """Custom Moroccan payslip — standalone, no dependency on Enterprise hr_payroll."""

    _name = 'telecom.paie.bulletin'
    _description = 'Bulletin de paie (Maroc)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc, employee_id'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------

    name = fields.Char(
        string='Référence',
        compute='_compute_name',
        store=True,
    )

    sequence_number = fields.Char(
        string='N° Bulletin',
        readonly=True,
        copy=False,
        help='Numéro séquentiel attribué à la confirmation.',
    )

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employé',
        required=True,
        ondelete='restrict',
        tracking=True,
        index=True,
    )

    date_from = fields.Date(
        string='Du',
        required=True,
        default=lambda self: date.today().replace(day=1),
        tracking=True,
    )

    date_to = fields.Date(
        string='Au',
        required=True,
        default=lambda self: TelecomPaieBulletin._last_day_of_month(date.today()),
        tracking=True,
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Société',
        default=lambda self: self.env.company,
        required=True,
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Devise',
        default=lambda self: self.env['res.currency'].search([('name', '=', 'MAD')], limit=1).id
            or self.env.company.currency_id.id,
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Brouillon'),
            ('confirme', 'Confirmé'),
            ('valide', 'Validé'),
            ('paye', 'Payé'),
        ],
        string='Statut',
        default='draft',
        required=True,
        tracking=True,
        copy=False,
    )

    # ------------------------------------------------------------------
    # Salary base elements
    # ------------------------------------------------------------------

    salaire_base = fields.Monetary(
        string='Salaire de base (MAD)',
        required=True,
        currency_field='currency_id',
        tracking=True,
    )

    nbr_jours_travailles = fields.Float(
        string='Jours théoriques',
        default=26.0,
        digits=(4, 1),
        help='Nombre de jours ouvrables théoriques dans le mois.',
    )

    nbr_jours_presents = fields.Float(
        string='Jours présents',
        compute='_compute_from_pointage',
        store=True,
        digits=(4, 1),
        help='Nombre de jours de présence chantier dans la période (depuis pointage).',
    )

    nbr_heures_sup = fields.Float(
        string='Heures supplémentaires',
        compute='_compute_from_pointage',
        store=True,
        digits=(4, 2),
        help='Total heures supplémentaires depuis les pointages chantier.',
    )

    indemnite_deplacement = fields.Monetary(
        string='Indemnités de déplacement',
        currency_field='currency_id',
        compute='_compute_from_pointage',
        store=True,
        readonly=False,  # allow manual override
        help='Cumul des primes de déplacement depuis les pointages validés.',
    )

    avantages_nature = fields.Monetary(
        string='Avantages en nature',
        currency_field='currency_id',
        default=0.0,
    )

    prime_anciennete = fields.Monetary(
        string='Prime d\'ancienneté',
        currency_field='currency_id',
        compute='_compute_prime_anciennete',
        store=True,
        help='Prime d\'ancienneté calculée selon le barème marocain.',
    )

    # ------------------------------------------------------------------
    # Cotisations salariales
    # ------------------------------------------------------------------

    cnss_base = fields.Monetary(
        string='Base CNSS',
        currency_field='currency_id',
        compute='_compute_cotisations',
        store=True,
        help='Base de calcul CNSS plafonnée à 6 000 MAD/mois.',
    )

    cnss_salarie = fields.Monetary(
        string='CNSS salarié (4.48%)',
        currency_field='currency_id',
        compute='_compute_cotisations',
        store=True,
    )

    amo_salarie = fields.Monetary(
        string='AMO salarié (2.26%)',
        currency_field='currency_id',
        compute='_compute_cotisations',
        store=True,
    )

    cimr_salarie = fields.Monetary(
        string='CIMR salarié',
        currency_field='currency_id',
        compute='_compute_cotisations',
        store=True,
    )

    # ------------------------------------------------------------------
    # Cotisations patronales
    # ------------------------------------------------------------------

    cnss_patronal = fields.Monetary(
        string='CNSS patronal (10.64%)',
        currency_field='currency_id',
        compute='_compute_cotisations',
        store=True,
    )

    amo_patronal = fields.Monetary(
        string='AMO patronal (3.96%)',
        currency_field='currency_id',
        compute='_compute_cotisations',
        store=True,
    )

    cimr_patronal = fields.Monetary(
        string='CIMR patronal',
        currency_field='currency_id',
        compute='_compute_cotisations',
        store=True,
    )

    # ------------------------------------------------------------------
    # IR calculation
    # ------------------------------------------------------------------

    salaire_net_imposable = fields.Monetary(
        string='Salaire net imposable',
        currency_field='currency_id',
        compute='_compute_ir',
        store=True,
        help='Salaire brut - cotisations salariales + avantages en nature.',
    )

    frais_pro = fields.Monetary(
        string='Frais professionnels (20%, plaf. 2 500)',
        currency_field='currency_id',
        compute='_compute_ir',
        store=True,
        help='20% du salaire net imposable, plafonné à 2 500 MAD/mois.',
    )

    salaire_imposable_ir = fields.Monetary(
        string='Salaire imposable IR',
        currency_field='currency_id',
        compute='_compute_ir',
        store=True,
        help='Base IR = salaire net imposable - frais pro - indemnités de déplacement.',
    )

    ir_annuel_brut = fields.Monetary(
        string='IR annuel brut (barème)',
        currency_field='currency_id',
        compute='_compute_ir',
        store=True,
    )

    ir_mensuel = fields.Monetary(
        string='IR mensuel (après déductions)',
        currency_field='currency_id',
        compute='_compute_ir',
        store=True,
        help='IR annuel / 12 - (nbr_parts - 1) × 30 MAD/mois par charge de famille.',
    )

    # ------------------------------------------------------------------
    # Net à payer
    # ------------------------------------------------------------------

    salaire_net_a_payer = fields.Monetary(
        string='NET À PAYER',
        currency_field='currency_id',
        compute='_compute_net',
        store=True,
    )

    # ------------------------------------------------------------------
    # Static helper
    # ------------------------------------------------------------------

    @staticmethod
    def _last_day_of_month(d):
        """Return the last day of the month for a given date."""
        last_day = calendar.monthrange(d.year, d.month)[1]
        return d.replace(day=last_day)

    # ------------------------------------------------------------------
    # Computed display name
    # ------------------------------------------------------------------

    @api.depends('employee_id', 'date_from')
    def _compute_name(self):
        MONTH_FR = {
            1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
            5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
            9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre',
        }
        for rec in self:
            if rec.employee_id and rec.date_from:
                month_label = MONTH_FR.get(rec.date_from.month, '')
                year = rec.date_from.year
                rec.name = f"Bulletin de paie — {rec.employee_id.name} — {month_label} {year}"
            else:
                rec.name = 'Nouveau bulletin'

    # ------------------------------------------------------------------
    # Compute: aggregate from validated pointage records
    # ------------------------------------------------------------------

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_from_pointage(self):
        Pointage = self.env['telecom.pointage.chantier']
        for rec in self:
            if not rec.employee_id or not rec.date_from or not rec.date_to:
                rec.nbr_jours_presents = 0.0
                rec.nbr_heures_sup = 0.0
                rec.indemnite_deplacement = 0.0
                continue
            pointages = Pointage.search([
                ('employee_id', '=', rec.employee_id.id),
                ('date', '>=', rec.date_from),
                ('date', '<=', rec.date_to),
                ('state', '=', 'valide'),
            ])
            rec.nbr_jours_presents = len(pointages)
            rec.nbr_heures_sup = sum(pointages.mapped('heures_supplementaires'))
            rec.indemnite_deplacement = sum(pointages.mapped('prime_deplacement'))

    # ------------------------------------------------------------------
    # Compute: prime d'ancienneté (barème marocain)
    # ------------------------------------------------------------------

    @api.depends('salaire_base', 'employee_id', 'date_from')
    def _compute_prime_anciennete(self):
        """
        Moroccan ancienneté rates:
        0-2 ans   : 0%
        2-5 ans   : 5%
        5-12 ans  : 10%
        12-20 ans : 15%
        > 20 ans  : 20%
        """
        for rec in self:
            if not rec.employee_id or not rec.date_from:
                rec.prime_anciennete = 0.0
                continue
            emp = rec.employee_id
            date_embauche = emp.first_contract_date  # Odoo 17 hr.employee field
            if not date_embauche:
                rec.prime_anciennete = 0.0
                continue
            anciennete_annees = (rec.date_from - date_embauche).days / 365.25
            if anciennete_annees < 2:
                taux = 0.0
            elif anciennete_annees < 5:
                taux = 0.05
            elif anciennete_annees < 12:
                taux = 0.10
            elif anciennete_annees < 20:
                taux = 0.15
            else:
                taux = 0.20
            rec.prime_anciennete = round(rec.salaire_base * taux, 2)

    # ------------------------------------------------------------------
    # Compute: social contributions (CNSS, AMO, CIMR)
    # ------------------------------------------------------------------

    CNSS_PLAFOND_MENSUEL = 6000.0
    CNSS_SALARIE_TAUX = 0.0448
    CNSS_PATRONAL_TAUX = 0.1064
    AMO_SALARIE_TAUX = 0.0226
    AMO_PATRONAL_TAUX = 0.0396

    @api.depends('salaire_base', 'employee_id', 'employee_id.cimr_taux', 'employee_id.cimr_taux_patronal')
    def _compute_cotisations(self):
        for rec in self:
            base = rec.salaire_base or 0.0
            # CNSS base plafonned
            cnss_base = min(base, self.CNSS_PLAFOND_MENSUEL)
            rec.cnss_base = round(cnss_base, 2)
            rec.cnss_salarie = round(cnss_base * self.CNSS_SALARIE_TAUX, 2)
            rec.cnss_patronal = round(cnss_base * self.CNSS_PATRONAL_TAUX, 2)
            # AMO on full gross
            rec.amo_salarie = round(base * self.AMO_SALARIE_TAUX, 2)
            rec.amo_patronal = round(base * self.AMO_PATRONAL_TAUX, 2)
            # CIMR
            cimr_sal_taux = (rec.employee_id.cimr_taux or 0.0) / 100.0
            cimr_pat_taux = (rec.employee_id.cimr_taux_patronal or 0.0) / 100.0
            rec.cimr_salarie = round(base * cimr_sal_taux, 2)
            rec.cimr_patronal = round(base * cimr_pat_taux, 2)

    # ------------------------------------------------------------------
    # Compute: IR (barème annuel 2024)
    # ------------------------------------------------------------------

    FRAIS_PRO_TAUX = 0.20
    FRAIS_PRO_PLAFOND_MENSUEL = 2500.0

    @api.depends(
        'salaire_base', 'cnss_salarie', 'amo_salarie', 'cimr_salarie',
        'avantages_nature', 'indemnite_deplacement', 'employee_id.nbr_parts_ir',
    )
    def _compute_ir(self):
        for rec in self:
            base = rec.salaire_base or 0.0
            # 1. Salaire net imposable
            sni = base - rec.cnss_salarie - rec.amo_salarie - rec.cimr_salarie + rec.avantages_nature
            rec.salaire_net_imposable = round(sni, 2)
            # 2. Frais professionnels (20%, plaf. 2500/mois)
            frais_pro = min(sni * self.FRAIS_PRO_TAUX, self.FRAIS_PRO_PLAFOND_MENSUEL)
            rec.frais_pro = round(frais_pro, 2)
            # 3. Salaire imposable IR
            sir = sni - frais_pro - (rec.indemnite_deplacement or 0.0)
            sir = max(0.0, sir)
            rec.salaire_imposable_ir = round(sir, 2)
            # 4. IR annuel brut (barème on annualized base)
            sir_annuel = sir * 12.0
            ir_annuel = self._compute_ir_annuel(sir_annuel)
            rec.ir_annuel_brut = round(ir_annuel, 2)
            # 5. IR mensuel (after family charge deductions)
            parts = rec.employee_id.nbr_parts_ir if rec.employee_id else 1.0
            deduction_famille = max(0.0, parts - 1.0) * 30.0  # 30 MAD/mois per charge
            ir_mensuel = max(0.0, (ir_annuel / 12.0) - deduction_famille)
            rec.ir_mensuel = round(ir_mensuel, 2)

    @staticmethod
    def _compute_ir_annuel(salaire_annuel_imposable):
        """
        IR barème annuel 2024 (Maroc).

        Tranches:
          0        – 30 000  : 0%
          30 001   – 50 000  : 10%
          50 001   – 60 000  : 20%
          60 001   – 80 000  : 30%
          80 001   – 180 000 : 34%
          > 180 000          : 38%

        Returns IR annuel brut (before family-charge deductions).
        """
        s = salaire_annuel_imposable
        if s <= 0:
            return 0.0
        if s <= 30000:
            return 0.0
        elif s <= 50000:
            return (s - 30000) * 0.10
        elif s <= 60000:
            return 20000 * 0.10 + (s - 50000) * 0.20
        elif s <= 80000:
            return 20000 * 0.10 + 10000 * 0.20 + (s - 60000) * 0.30
        elif s <= 180000:
            return 20000 * 0.10 + 10000 * 0.20 + 20000 * 0.30 + (s - 80000) * 0.34
        else:
            return 20000 * 0.10 + 10000 * 0.20 + 20000 * 0.30 + 100000 * 0.34 + (s - 180000) * 0.38

    # ------------------------------------------------------------------
    # Compute: net à payer
    # ------------------------------------------------------------------

    @api.depends(
        'salaire_base', 'indemnite_deplacement',
        'cnss_salarie', 'amo_salarie', 'cimr_salarie', 'ir_mensuel',
    )
    def _compute_net(self):
        for rec in self:
            net = (
                (rec.salaire_base or 0.0)
                + (rec.indemnite_deplacement or 0.0)
                - (rec.cnss_salarie or 0.0)
                - (rec.amo_salarie or 0.0)
                - (rec.cimr_salarie or 0.0)
                - (rec.ir_mensuel or 0.0)
            )
            rec.salaire_net_a_payer = round(max(0.0, net), 2)

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------

    def action_confirmer(self):
        """Move bulletin from draft to confirmed, assign sequence number."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    _("Le bulletin '%s' est déjà confirmé ou dans un état ultérieur.") % rec.name
                )
            if not rec.sequence_number:
                seq = self.env['ir.sequence'].next_by_code('telecom.paie.bulletin') or '/'
                rec.sequence_number = seq
            rec.state = 'confirme'
        return True

    def action_valider(self):
        """Move bulletin from confirmed to validated."""
        for rec in self:
            if rec.state != 'confirme':
                raise UserError(
                    _("Le bulletin doit être confirmé avant d'être validé.")
                )
            rec.state = 'valide'
        return True

    def action_marquer_paye(self):
        """Mark a validated bulletin as paid."""
        for rec in self:
            if rec.state != 'valide':
                raise UserError(
                    _("Le bulletin doit être validé avant d'être marqué payé.")
                )
            rec.state = 'paye'
        return True

    def action_remettre_brouillon(self):
        """Reset to draft (only from confirme)."""
        for rec in self:
            if rec.state not in ('confirme',):
                raise UserError(
                    _("Seul un bulletin confirmé peut être remis en brouillon.")
                )
            rec.state = 'draft'
        return True

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                if rec.date_to < rec.date_from:
                    raise ValidationError(
                        _("La date de fin doit être postérieure à la date de début.")
                    )

    @api.constrains('salaire_base')
    def _check_salaire_base(self):
        for rec in self:
            if rec.salaire_base < 0:
                raise ValidationError(_("Le salaire de base ne peut pas être négatif."))

    _sql_constraints = [
        (
            'uniq_employee_period',
            'UNIQUE(employee_id, date_from)',
            'Un seul bulletin de paie par employé et par période de début est autorisé.',
        ),
    ]
