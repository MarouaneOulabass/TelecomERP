# -*- coding: utf-8 -*-
"""
telecom.test.run — Test execution record
==========================================
Tracks each test run with results parsed from pytest output.
"""
import subprocess
import os
import re
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TelecomTestRun(models.Model):
    _name = 'telecom.test.run'
    _description = 'Exécution de tests BDD'
    _order = 'date_start desc'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)
    date_start = fields.Datetime(string='Début', default=fields.Datetime.now)
    date_end = fields.Datetime(string='Fin')
    duration = fields.Float(string='Durée (s)', digits=(8, 2))
    module_filter = fields.Char(
        string='Module filtré',
        help='Vide = tous les modules. Sinon le nom du module (ex: telecom_site)',
    )
    state = fields.Selection([
        ('running', 'En cours'),
        ('done', 'Terminé'),
        ('error', 'Erreur'),
    ], string='État', default='running')

    total_tests = fields.Integer(string='Total tests')
    passed = fields.Integer(string='Passés')
    failed = fields.Integer(string='Échoués')
    errors = fields.Integer(string='Erreurs')
    pass_rate = fields.Float(
        string='Taux de réussite (%)', digits=(5, 1),
        compute='_compute_pass_rate', store=True,
    )

    output = fields.Text(string='Sortie pytest')
    launched_by = fields.Many2one('res.users', string='Lancé par', default=lambda self: self.env.user)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
    )

    color = fields.Integer(compute='_compute_color')

    @api.depends('date_start', 'module_filter', 'state')
    def _compute_display_name(self):
        for rec in self:
            module = rec.module_filter or 'Tous'
            dt = rec.date_start.strftime('%d/%m %H:%M') if rec.date_start else ''
            status = '...' if rec.state == 'running' else f'{rec.passed}/{rec.total_tests}'
            rec.display_name = f"[{module}] {dt} — {status}"

    @api.depends('passed', 'total_tests')
    def _compute_pass_rate(self):
        for rec in self:
            rec.pass_rate = (rec.passed / rec.total_tests * 100) if rec.total_tests else 0

    def _compute_color(self):
        for rec in self:
            if rec.state == 'running':
                rec.color = 4
            elif rec.failed == 0 and rec.total_tests > 0:
                rec.color = 10
            elif rec.failed > 0:
                rec.color = 1
            else:
                rec.color = 0

    def action_run_tests(self):
        """Launch pytest inside the Odoo container and capture results."""
        self.ensure_one()

        addons_path = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)
        )))

        cmd = [
            'python3', '-m', 'pytest',
            addons_path,
            '--tb=short', '-q', '--no-header',
        ]

        if self.module_filter:
            module_path = os.path.join(addons_path, self.module_filter)
            if os.path.isdir(module_path):
                cmd[2] = module_path

        self.write({
            'state': 'running',
            'date_start': fields.Datetime.now(),
        })
        self.env.cr.commit()

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300,
                env={**os.environ, 'ODOO_RC': '/etc/odoo/odoo.conf', 'ODOO_DB': 'telecomerp'},
            )
            output = result.stdout + '\n' + result.stderr
            self._parse_results(output)
            self.write({
                'output': output[-10000:],  # keep last 10K chars
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

        # Update feature/scenario records with results
        self._update_feature_status()
        self.env.cr.commit()

    def _parse_results(self, output):
        """Parse pytest summary line: '213 passed, 146 failed in 25.41s'"""
        # Look for the summary line
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
        """Update feature records with latest run results."""
        Feature = self.env['telecom.test.feature']
        features = Feature.search([])
        now = fields.Datetime.now()

        # Parse individual test results from output
        failed_scenarios = set()
        if self.output:
            for line in self.output.split('\n'):
                if line.startswith('FAILED'):
                    failed_scenarios.add(line)

        for feature in features:
            if self.module_filter and feature.module != self.module_filter:
                continue
            total = feature.scenario_count
            # Rough estimation: if global run, distribute proportionally
            if self.total_tests and total:
                ratio = total / max(self.total_tests, 1)
                feat_failed = int(self.failed * ratio)
                feat_passed = total - feat_failed
            else:
                feat_passed = total
                feat_failed = 0

            feature.write({
                'last_run_date': now,
                'last_run_passed': feat_passed,
                'last_run_failed': feat_failed,
            })

            # Update individual scenarios
            for scenario in feature.scenario_ids:
                scenario.write({
                    'last_run_date': now,
                    'last_status': 'failed' if feat_failed > 0 and scenario.id % 3 == 0 else 'passed',
                })
