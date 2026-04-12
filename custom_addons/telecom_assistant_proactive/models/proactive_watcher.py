"""Proactive watcher model — configurable alert monitors."""

import logging
from datetime import timedelta

from odoo import api, fields, models
from odoo.tools.translate import _

from odoo.addons.telecom_feature_flags.utils.feature_flag import (
    feature_flag,
    is_flag_active,
)

_logger = logging.getLogger(__name__)

WATCHER_TYPE_SELECTION = [
    ('marge_sous_seuil', 'Marge sous seuil'),
    ('caution_expirant', 'Caution expirant'),
    ('pointage_manquant', 'Pointage manquant'),
    ('facture_impayee', 'Facture impayée'),
    ('habilitation_expirant', 'Habilitation expirant'),
    ('derive_marge_hebdo', 'Dérive marge hebdomadaire'),
    ('sla_depasse', 'SLA dépassé'),
]

# Mapping from watcher_type to feature flag code
WATCHER_FLAG_MAP = {
    'marge_sous_seuil': 'assistant_proactive.watcher_marge_sous_seuil',
    'caution_expirant': 'assistant_proactive.watcher_caution_expirant',
    'pointage_manquant': 'assistant_proactive.watcher_pointage_manquant',
    'facture_impayee': 'assistant_proactive.watcher_facture_impayee',
    'habilitation_expirant': 'assistant_proactive.watcher_habilitation_expirant',
    'derive_marge_hebdo': 'assistant_proactive.watcher_derive_marge_hebdo',
    'sla_depasse': 'assistant_proactive.watcher_sla_depasse',
}


class ProactiveWatcher(models.Model):
    """Configurable watcher that monitors business conditions and creates notifications."""

    _name = 'telecom.proactive.watcher'
    _description = 'Proactive Watcher'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
    )
    code = fields.Char(
        string='Code',
        required=True,
        index=True,
    )
    description = fields.Text(
        string='Description',
        translate=True,
    )
    watcher_type = fields.Selection(
        selection=WATCHER_TYPE_SELECTION,
        string='Watcher Type',
        required=True,
    )
    threshold_value = fields.Float(
        string='Threshold Value',
        help="Configurable threshold for this watcher",
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    last_run = fields.Datetime(
        string='Last Run',
        readonly=True,
    )
    notification_count = fields.Integer(
        string='Notifications',
        compute='_compute_notification_count',
    )
    notification_ids = fields.One2many(
        'telecom.proactive.notification',
        'watcher_id',
        string='Notifications',
    )

    def _compute_notification_count(self):
        for record in self:
            record.notification_count = self.env['telecom.proactive.notification'].search_count([
                ('watcher_id', '=', record.id),
            ])

    def run_all_watchers(self):
        """Cron entry point: run all active watchers."""
        watchers = self.search([('active', '=', True)])
        for watcher in watchers:
            flag_code = WATCHER_FLAG_MAP.get(watcher.watcher_type)
            if flag_code and not is_flag_active(flag_code, self.env):
                _logger.debug(
                    "Watcher %s skipped: flag %s is inactive",
                    watcher.code, flag_code,
                )
                continue
            try:
                method_name = '_run_watcher_%s' % watcher.watcher_type
                method = getattr(self, method_name, None)
                if method:
                    method(watcher)
                watcher.write({'last_run': fields.Datetime.now()})
            except Exception:
                _logger.exception("Error running watcher %s", watcher.code)

    def _create_notification(self, watcher, user, title, message, severity='warning',
                             record_model=None, record_id=None):
        """Create a notification, respecting channel flags."""
        # Only create in-app notifications if channel flag is active
        if not is_flag_active('assistant_proactive.channel_in_app', self.env):
            return

        self.env['telecom.proactive.notification'].create({
            'watcher_id': watcher.id,
            'user_id': user.id,
            'title': title,
            'message': message,
            'severity': severity,
            'record_model': record_model or '',
            'record_id': record_id or 0,
            'channel': 'in_app',
        })

    # ----- Watcher implementations -----

    @feature_flag('assistant_proactive.watcher_marge_sous_seuil')
    def _run_watcher_marge_sous_seuil(self, watcher):
        """Check margin thresholds on active projects."""
        # Margin model from telecom_margin
        MarginSnapshot = self.env.get('telecom.margin.snapshot')
        if MarginSnapshot is None:
            return

        threshold = watcher.threshold_value or 10.0  # default 10%
        projects = self.env['telecom.project'].search([('state', '!=', 'done')])
        responsables = self.env.ref(
            'telecom_base.group_telecom_responsable', raise_if_not_found=False
        )
        if not responsables:
            return

        for project in projects:
            snapshot = MarginSnapshot.search([
                ('project_id', '=', project.id),
            ], order='create_date desc', limit=1)
            if snapshot and snapshot.margin_percent < threshold:
                for user in responsables.users:
                    self._create_notification(
                        watcher, user,
                        title=_("Marge sous seuil: %s") % project.name,
                        message=_("La marge du projet %s est à %.1f%% (seuil: %.1f%%)") % (
                            project.name, snapshot.margin_percent, threshold,
                        ),
                        severity='critical' if snapshot.margin_percent < 0 else 'warning',
                        record_model='telecom.project',
                        record_id=project.id,
                    )

    @feature_flag('assistant_proactive.watcher_caution_expirant')
    def _run_watcher_caution_expirant(self, watcher):
        """Check caution expiration at J-30, J-15, J-7."""
        Caution = self.env.get('telecom.caution')
        if Caution is None:
            return

        today = fields.Date.today()
        alert_days = [30, 15, 7]
        responsables = self.env.ref(
            'telecom_base.group_telecom_responsable', raise_if_not_found=False
        )
        if not responsables:
            return

        for days in alert_days:
            target_date = today + timedelta(days=days)
            cautions = Caution.search([
                ('date_expiration', '=', target_date),
                ('state', '!=', 'released'),
            ])
            for caution in cautions:
                for user in responsables.users:
                    self._create_notification(
                        watcher, user,
                        title=_("Caution expire dans %d jours") % days,
                        message=_("La caution %s expire le %s") % (
                            caution.name, caution.date_expiration,
                        ),
                        severity='critical' if days <= 7 else 'warning',
                        record_model='telecom.caution',
                        record_id=caution.id,
                    )

    @feature_flag('assistant_proactive.watcher_pointage_manquant')
    def _run_watcher_pointage_manquant(self, watcher):
        """Check missing attendance at end of day."""
        Attendance = self.env.get('telecom.attendance')
        if Attendance is None:
            return

        today = fields.Date.today()
        # Find technicians who were supposed to work today but have no attendance
        employees = self.env['hr.employee'].search([
            ('active', '=', True),
        ])
        chefs = self.env.ref(
            'telecom_base.group_telecom_chef_chantier', raise_if_not_found=False
        )
        if not chefs:
            return

        for employee in employees:
            attendance = Attendance.search([
                ('employee_id', '=', employee.id),
                ('date', '=', today),
            ], limit=1)
            if not attendance:
                for user in chefs.users:
                    self._create_notification(
                        watcher, user,
                        title=_("Pointage manquant: %s") % employee.name,
                        message=_("L'employé %s n'a pas de pointage pour le %s") % (
                            employee.name, today,
                        ),
                        severity='info',
                    )

    @feature_flag('assistant_proactive.watcher_facture_impayee')
    def _run_watcher_facture_impayee(self, watcher):
        """Check invoices unpaid after 30 days."""
        threshold_days = int(watcher.threshold_value or 30)
        cutoff = fields.Date.today() - timedelta(days=threshold_days)
        invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('invoice_date', '<=', cutoff),
        ])
        responsables = self.env.ref(
            'telecom_base.group_telecom_responsable', raise_if_not_found=False
        )
        if not responsables:
            return

        for invoice in invoices:
            for user in responsables.users:
                self._create_notification(
                    watcher, user,
                    title=_("Facture impayée: %s") % invoice.name,
                    message=_("La facture %s de %s est impayée depuis plus de %d jours") % (
                        invoice.name, invoice.partner_id.name, threshold_days,
                    ),
                    severity='warning',
                    record_model='account.move',
                    record_id=invoice.id,
                )

    @feature_flag('assistant_proactive.watcher_habilitation_expirant')
    def _run_watcher_habilitation_expirant(self, watcher):
        """Check expiring habilitations."""
        Habilitation = self.env.get('telecom.habilitation')
        if Habilitation is None:
            return

        today = fields.Date.today()
        alert_date = today + timedelta(days=30)
        habilitations = Habilitation.search([
            ('date_expiration', '<=', alert_date),
            ('date_expiration', '>=', today),
        ])
        chefs = self.env.ref(
            'telecom_base.group_telecom_chef_chantier', raise_if_not_found=False
        )
        if not chefs:
            return

        for hab in habilitations:
            days_left = (hab.date_expiration - today).days
            for user in chefs.users:
                self._create_notification(
                    watcher, user,
                    title=_("Habilitation expire dans %d jours") % days_left,
                    message=_("L'habilitation %s de %s expire le %s") % (
                        hab.name, hab.employee_id.name, hab.date_expiration,
                    ),
                    severity='critical' if days_left <= 7 else 'warning',
                )

    @feature_flag('assistant_proactive.watcher_derive_marge_hebdo')
    def _run_watcher_derive_marge_hebdo(self, watcher):
        """Check weekly margin drift."""
        # Placeholder — requires margin snapshots comparison
        _logger.info("Watcher derive_marge_hebdo: not yet fully implemented")

    @feature_flag('assistant_proactive.watcher_sla_depasse')
    def _run_watcher_sla_depasse(self, watcher):
        """Check SLA breaches on interventions."""
        Intervention = self.env.get('telecom.intervention')
        if Intervention is None:
            return

        now = fields.Datetime.now()
        interventions = Intervention.search([
            ('state', 'in', ['planned', 'in_progress']),
            ('sla_deadline', '<', now),
        ])
        responsables = self.env.ref(
            'telecom_base.group_telecom_responsable', raise_if_not_found=False
        )
        if not responsables:
            return

        for intervention in interventions:
            for user in responsables.users:
                self._create_notification(
                    watcher, user,
                    title=_("SLA dépassé: %s") % intervention.name,
                    message=_("L'intervention %s a dépassé son délai SLA") % intervention.name,
                    severity='critical',
                    record_model='telecom.intervention',
                    record_id=intervention.id,
                )
