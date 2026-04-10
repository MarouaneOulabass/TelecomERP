# -*- coding: utf-8 -*-
"""
telecom.test.feature — Feature file representation
====================================================
Parses .feature files from custom_addons and stores them as Odoo records.
"""
import os
import re
import glob
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TelecomTestFeature(models.Model):
    _name = 'telecom.test.feature'
    _description = 'Fichier de test BDD (.feature)'
    _order = 'module, name'
    _rec_name = 'display_name'

    name = fields.Char(string='Nom du fichier', required=True)
    display_name = fields.Char(
        string='Nom complet',
        compute='_compute_display_name', store=True,
    )
    module = fields.Char(string='Module', required=True, index=True)
    feature_title = fields.Char(string='Titre de la fonctionnalité')
    description = fields.Text(string='Description (En tant que...)')
    file_path = fields.Char(string='Chemin du fichier')
    content = fields.Text(string='Contenu du fichier .feature')
    scenario_ids = fields.One2many(
        'telecom.test.scenario', 'feature_id', string='Scénarios',
    )
    scenario_count = fields.Integer(
        string='Nb scénarios', compute='_compute_scenario_count', store=True,
    )
    last_run_date = fields.Datetime(string='Dernière exécution')
    last_run_passed = fields.Integer(string='Passés')
    last_run_failed = fields.Integer(string='Échoués')
    last_run_status = fields.Selection([
        ('success', 'Tous passent'),
        ('partial', 'Échecs partiels'),
        ('fail', 'Tous échouent'),
        ('not_run', 'Jamais exécuté'),
    ], string='Statut', default='not_run', compute='_compute_run_status', store=True)

    color = fields.Integer(string='Couleur', compute='_compute_color')

    @api.depends('module', 'feature_title')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"[{rec.module}] {rec.feature_title or rec.name}"

    @api.depends('scenario_ids')
    def _compute_scenario_count(self):
        for rec in self:
            rec.scenario_count = len(rec.scenario_ids)

    @api.depends('last_run_passed', 'last_run_failed', 'last_run_date')
    def _compute_run_status(self):
        for rec in self:
            if not rec.last_run_date:
                rec.last_run_status = 'not_run'
            elif rec.last_run_failed == 0:
                rec.last_run_status = 'success'
            elif rec.last_run_passed == 0:
                rec.last_run_status = 'fail'
            else:
                rec.last_run_status = 'partial'

    def _compute_color(self):
        color_map = {'success': 10, 'partial': 3, 'fail': 1, 'not_run': 0}
        for rec in self:
            rec.color = color_map.get(rec.last_run_status, 0)

    def action_sync_features(self):
        """Scan custom_addons for .feature files and sync to database."""
        addons_path = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)
        )))
        pattern = os.path.join(addons_path, 'telecom_*/tests/features/*.feature')
        files = glob.glob(pattern)

        synced = 0
        for fpath in sorted(files):
            parts = fpath.replace('\\', '/').split('/')
            # Find the module name (telecom_*)
            module = None
            for p in parts:
                if p.startswith('telecom_'):
                    module = p
                    break
            if not module:
                continue

            fname = os.path.basename(fpath)
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse feature title
            feature_title = ''
            description_lines = []
            for line in content.split('\n'):
                stripped = line.strip()
                if stripped.startswith('Fonctionnalité:') or stripped.startswith('Feature:'):
                    feature_title = stripped.split(':', 1)[1].strip()
                elif stripped.startswith('En tant que') or stripped.startswith('Je veux') or stripped.startswith('Afin de'):
                    description_lines.append(stripped)

            # Search or create feature record
            feature = self.search([('module', '=', module), ('name', '=', fname)], limit=1)
            vals = {
                'name': fname,
                'module': module,
                'feature_title': feature_title,
                'description': '\n'.join(description_lines),
                'file_path': fpath,
                'content': content,
            }
            if feature:
                feature.write(vals)
            else:
                feature = self.create(vals)

            # Parse and sync scenarios
            feature._parse_scenarios(content)
            synced += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Synchronisation terminée'),
                'message': _('%d fichiers .feature synchronisés.') % synced,
                'type': 'success',
                'sticky': False,
            },
        }

    def _parse_scenarios(self, content):
        """Parse Gherkin content and create/update scenario records."""
        Scenario = self.env['telecom.test.scenario']
        existing = {s.name: s for s in self.scenario_ids}
        found_names = set()

        lines = content.split('\n')
        current_scenario = None
        current_steps = []
        scenario_type = 'scenario'

        for line in lines:
            stripped = line.strip()

            if stripped.startswith('Scénario:') or stripped.startswith('Scenario:'):
                # Save previous scenario
                if current_scenario:
                    self._save_scenario(
                        existing, found_names, current_scenario,
                        '\n'.join(current_steps), scenario_type,
                    )
                current_scenario = stripped.split(':', 1)[1].strip()
                current_steps = []
                scenario_type = 'scenario'

            elif stripped.startswith('Plan du Scénario:') or stripped.startswith('Scenario Outline:'):
                if current_scenario:
                    self._save_scenario(
                        existing, found_names, current_scenario,
                        '\n'.join(current_steps), scenario_type,
                    )
                current_scenario = stripped.split(':', 1)[1].strip()
                current_steps = []
                scenario_type = 'outline'

            elif current_scenario and stripped and not stripped.startswith('#') \
                    and not stripped.startswith('Exemples:') and not stripped.startswith('Examples:') \
                    and not stripped.startswith('|') and not stripped.startswith('Contexte:') \
                    and not stripped.startswith('Background:') \
                    and not stripped.startswith('Fonctionnalité:') and not stripped.startswith('Feature:'):
                current_steps.append(stripped)

        # Save last scenario
        if current_scenario:
            self._save_scenario(
                existing, found_names, current_scenario,
                '\n'.join(current_steps), scenario_type,
            )

        # Remove scenarios no longer in file
        for name, rec in existing.items():
            if name not in found_names:
                rec.unlink()

    def _save_scenario(self, existing, found_names, name, steps, scenario_type):
        found_names.add(name)
        vals = {
            'feature_id': self.id,
            'name': name,
            'steps': steps,
            'scenario_type': scenario_type,
            'module': self.module,
        }
        if name in existing:
            existing[name].write(vals)
        else:
            self.env['telecom.test.scenario'].create(vals)

    def action_view_content(self):
        """Open a popup showing the feature file content."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'telecom.test.feature',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
