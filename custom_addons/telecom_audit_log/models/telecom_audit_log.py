# -*- coding: utf-8 -*-
"""
telecom.audit.log — Central audit trail
==========================================
Logs every significant action across the ERP:
- CRUD on telecom models (create, write, unlink)
- Workflow transitions (state changes)
- Agent IA actions (assistant questions, onboarding steps)
- Login/logout events
- Report generation

Each log entry captures: who, what, when, which record, old/new values.
"""
import json
from odoo import api, fields, models, _


class TelecomAuditLog(models.Model):
    _name = 'telecom.audit.log'
    _description = 'Journal d\'audit TelecomERP'
    _order = 'timestamp desc, id desc'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)
    timestamp = fields.Datetime(
        string='Date/Heure', default=fields.Datetime.now,
        required=True, index=True, readonly=True,
    )

    # Who
    user_id = fields.Many2one(
        'res.users', string='Utilisateur', required=True,
        default=lambda self: self.env.user, index=True, readonly=True,
    )
    user_name = fields.Char(
        string='Nom utilisateur', related='user_id.name', store=True,
    )
    ip_address = fields.Char(string='Adresse IP', readonly=True)

    # What
    action_type = fields.Selection([
        ('create', 'Création'),
        ('write', 'Modification'),
        ('unlink', 'Suppression'),
        ('state_change', 'Changement d\'état'),
        ('button', 'Action / Bouton'),
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('ai_query', 'Question IA'),
        ('ai_onboarding', 'Onboarding IA'),
        ('report', 'Rapport généré'),
        ('export', 'Export données'),
        ('other', 'Autre'),
    ], string='Type d\'action', required=True, index=True, readonly=True)

    # Which record
    model_name = fields.Char(
        string='Modèle', index=True, readonly=True,
    )
    model_description = fields.Char(
        string='Module', readonly=True,
    )
    record_id = fields.Integer(
        string='ID enregistrement', readonly=True,
    )
    record_name = fields.Char(
        string='Nom enregistrement', readonly=True,
    )

    # Details
    description = fields.Char(
        string='Description', readonly=True,
    )
    old_values = fields.Text(
        string='Anciennes valeurs (JSON)', readonly=True,
    )
    new_values = fields.Text(
        string='Nouvelles valeurs (JSON)', readonly=True,
    )
    field_changed = fields.Char(
        string='Champ modifié', readonly=True,
    )

    # For state changes
    old_state = fields.Char(string='Ancien état', readonly=True)
    new_state = fields.Char(string='Nouvel état', readonly=True)

    # For AI
    ai_tokens = fields.Integer(string='Tokens IA', readonly=True)
    ai_tools_used = fields.Char(string='Outils IA utilisés', readonly=True)

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
        index=True, readonly=True,
    )

    @api.depends('action_type', 'model_name', 'record_name', 'user_name')
    def _compute_display_name(self):
        type_labels = dict(self._fields['action_type'].selection)
        for rec in self:
            action = type_labels.get(rec.action_type, rec.action_type or '')
            model = rec.model_description or rec.model_name or ''
            record = rec.record_name or ''
            rec.display_name = '%s — %s %s' % (action, model, record)

    @api.model
    def log(self, action_type, model_name='', record_id=0, record_name='',
            description='', old_values=None, new_values=None,
            field_changed='', old_state='', new_state='',
            ai_tokens=0, ai_tools_used=''):
        """Create an audit log entry. Called from the mixin or directly."""
        try:
            model_desc = ''
            if model_name and model_name in self.env:
                model_desc = self.env[model_name]._description or model_name

            ip = ''
            try:
                from odoo.http import request
                if request:
                    ip = request.httprequest.remote_addr or ''
            except Exception:
                pass

            vals = {
                'action_type': action_type,
                'model_name': model_name,
                'model_description': model_desc,
                'record_id': record_id,
                'record_name': str(record_name)[:200] if record_name else '',
                'description': str(description)[:500] if description else '',
                'old_values': json.dumps(old_values, ensure_ascii=False, default=str)[:5000] if old_values else '',
                'new_values': json.dumps(new_values, ensure_ascii=False, default=str)[:5000] if new_values else '',
                'field_changed': field_changed,
                'old_state': old_state,
                'new_state': new_state,
                'ai_tokens': ai_tokens,
                'ai_tools_used': ai_tools_used,
                'ip_address': ip,
            }
            return self.sudo().create(vals)
        except Exception:
            # Never let audit logging break the main operation
            pass
