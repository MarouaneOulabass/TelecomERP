# -*- coding: utf-8 -*-
"""
telecom.test.scenario — Individual BDD scenario
=================================================
"""
from odoo import api, fields, models


class TelecomTestScenario(models.Model):
    _name = 'telecom.test.scenario'
    _description = 'Scénario de test BDD'
    _order = 'module, feature_id, name'

    name = fields.Char(string='Nom du scénario', required=True)
    feature_id = fields.Many2one(
        'telecom.test.feature', string='Fichier .feature',
        required=True, ondelete='cascade', index=True,
    )
    module = fields.Char(string='Module', index=True)
    scenario_type = fields.Selection([
        ('scenario', 'Scénario'),
        ('outline', 'Plan du Scénario (paramétré)'),
    ], string='Type', default='scenario')
    steps = fields.Text(string='Étapes (Given/When/Then)')
    last_status = fields.Selection([
        ('passed', 'Passé'),
        ('failed', 'Échoué'),
        ('error', 'Erreur'),
        ('skipped', 'Ignoré'),
        ('not_run', 'Jamais exécuté'),
    ], string='Dernier résultat', default='not_run')
    last_error = fields.Text(string='Dernier message d\'erreur')
    last_run_date = fields.Datetime(string='Dernière exécution')
    last_duration = fields.Float(string='Durée (s)', digits=(6, 2))

    color = fields.Integer(compute='_compute_color')

    def _compute_color(self):
        color_map = {'passed': 10, 'failed': 1, 'error': 1, 'skipped': 3, 'not_run': 0}
        for rec in self:
            rec.color = color_map.get(rec.last_status, 0)
