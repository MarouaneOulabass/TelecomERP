# -*- coding: utf-8 -*-
"""
telecom.test.run — BDD test execution
=======================================
"""
import subprocess
import os
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Pytest binary inside the Odoo container
PYTEST_BIN = '/var/lib/odoo/.local/bin/pytest'
ADDONS_PATH = '/mnt/extra-addons'


class TelecomTestRun(models.Model):
    _name = 'telecom.test.run'
    _description = 'Exécution de tests BDD'
    _order = 'date_start desc'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)
    date_start = fields.Datetime(string='Début')
    date_end = fields.Datetime(string='Fin')
    duration = fields.Float(string='Durée (s)', digits=(8, 2))
    module_filter = fields.Char(
        string='Module',
        help='Vide = tous les modules. Sinon : telecom_site, telecom_hr_ma, etc.',
    )
    state = fields.Selection([
        ('draft', 'Prêt'),
        ('running', 'En cours...'),
        ('done', 'Terminé'),
        ('error', 'Erreur'),
    ], string='État', default='draft')

    total_tests = fields.Integer(string='Total')
    passed = fields.Integer(string='Passés')
    failed = fields.Integer(string='Échoués')
    errors = fields.Integer(string='Erreurs')
    pass_rate = fields.Float(
        string='Réussite (%)', digits=(5, 1),
        compute='_compute_pass_rate', store=True,
    )

    output = fields.Text(string='Résultat complet')
    failed_details = fields.Text(string='Tests échoués', compute='_compute_failed_details')
    launched_by = fields.Many2one('res.users', string='Lancé par', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.depends('date_start', 'module_filter', 'state', 'passed', 'total_tests')
    def _compute_display_name(self):
        for rec in self:
            module = rec.module_filter or 'Tous les modules'
            dt = rec.date_start.strftime('%d/%m %H:%M') if rec.date_start else 'Nouveau'
            if rec.state == 'draft':
                rec.display_name = f'{module} — Prêt'
            elif rec.state == 'running':
                rec.display_name = f'{module} — En cours...'
            else:
                rec.display_name = f'{module} — {rec.passed}/{rec.total_tests} ({dt})'

    @api.depends('passed', 'total_tests')
    def _compute_pass_rate(self):
        for rec in self:
            rec.pass_rate = (rec.passed / rec.total_tests * 100) if rec.total_tests else 0

    def _compute_failed_details(self):
        for rec in self:
            if rec.output and rec.failed > 0:
                lines = []
                for line in rec.output.split('\n'):
                    if line.startswith('FAILED'):
                        # Extract test name
                        clean = line.replace('FAILED mnt/extra-addons/', '').strip()
                        lines.append(clean)
                rec.failed_details = '\n'.join(lines) if lines else ''
            else:
                rec.failed_details = ''

    def action_run_tests(self):
        """Launch pytest and capture results."""
        self.ensure_one()

        if not os.path.exists(PYTEST_BIN):
            raise UserError(_(
                "pytest non trouvé sur le serveur.\n"
                "Installez-le : pip install pytest pytest-bdd freezegun"
            ))

        # Build command
        test_path = ADDONS_PATH
        if self.module_filter:
            module_path = os.path.join(ADDONS_PATH, self.module_filter)
            if os.path.isdir(module_path):
                test_path = module_path
            else:
                raise UserError(_("Module '%s' non trouvé dans %s") % (self.module_filter, ADDONS_PATH))

        cmd = [PYTEST_BIN, test_path, '--tb=line', '-q', '--no-header']

        self.write({
            'state': 'running',
            'date_start': fields.Datetime.now(),
            'output': '',
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'total_tests': 0,
        })
        # Removed: self.env.cr.commit() — anti-pattern, let Odoo manage transactions

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300,
                env={**os.environ, 'ODOO_RC': '/etc/odoo/odoo.conf', 'ODOO_DB': 'telecomerp'},
            )
            output = result.stdout + '\n' + result.stderr
            self._parse_results(output)
            self.write({
                'output': output[-15000:],
                'date_end': fields.Datetime.now(),
                'state': 'done',
            })
        except subprocess.TimeoutExpired:
            self.write({
                'output': 'Tests interrompus — timeout 5 minutes dépassé.',
                'state': 'error',
                'date_end': fields.Datetime.now(),
            })
        except Exception as e:
            self.write({
                'output': str(e),
                'state': 'error',
                'date_end': fields.Datetime.now(),
            })

        if self.date_start and self.date_end:
            self.duration = (self.date_end - self.date_start).total_seconds()

        self._update_feature_status()
        # Removed: self.env.cr.commit() — anti-pattern, let Odoo manage transactions

        return True

    def action_rerun(self):
        """Re-run the same test configuration."""
        self.ensure_one()
        self.write({'state': 'draft'})
        return self.action_run_tests()

    def _parse_results(self, output):
        passed = failed = errors = 0
        for line in output.split('\n'):
            m = re.search(r'(\d+)\s+passed', line)
            if m:
                passed = int(m.group(1))
            m = re.search(r'(\d+)\s+failed', line)
            if m:
                failed = int(m.group(1))
            m = re.search(r'(\d+)\s+error', line)
            if m:
                errors = int(m.group(1))
        self.passed = passed
        self.failed = failed
        self.errors = errors
        self.total_tests = passed + failed + errors

    def _update_feature_status(self):
        Feature = self.env['telecom.test.feature']
        features = Feature.search([])
        now = fields.Datetime.now()

        # Parse failed test names from output
        failed_tests = set()
        if self.output:
            for line in self.output.split('\n'):
                if line.startswith('FAILED'):
                    failed_tests.add(line)

        for feature in features:
            if self.module_filter and feature.module != self.module_filter:
                continue

            # Count failures for this feature by checking if any failed test contains the module name
            feat_failed = 0
            for ft in failed_tests:
                if feature.module in ft:
                    feat_failed += 1

            feature.write({
                'last_run_date': now,
                'last_run_passed': max(0, feature.scenario_count - feat_failed),
                'last_run_failed': feat_failed,
            })

            for scenario in feature.scenario_ids:
                # Check if this scenario failed
                scenario_failed = any(
                    scenario.name.lower()[:30] in ft.lower()
                    for ft in failed_tests
                    if feature.module in ft
                )
                scenario.write({
                    'last_run_date': now,
                    'last_status': 'failed' if scenario_failed else 'passed',
                })
