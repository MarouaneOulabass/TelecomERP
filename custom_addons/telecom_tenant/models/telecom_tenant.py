# -*- coding: utf-8 -*-
"""
telecom.tenant — Tenant registry for multi-tenant SaaS
========================================================
Each record represents one tenant (client) with its own Odoo database.
This model lives in the MASTER database (the control plane).

Tenant lifecycle:
  draft → provisioning → active → suspended → archived
"""
import re
import json
import yaml
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


TENANT_STATE = [
    ('draft', 'Brouillon'),
    ('provisioning', 'En provisioning...'),
    ('active', 'Actif'),
    ('suspended', 'Suspendu'),
    ('archived', 'Archivé'),
]

CAPABILITY_MODULES = {
    'telecom_base': 'telecom_base',
    'telecom_localization_ma': 'telecom_localization_ma',
    'telecom_site': 'telecom_site',
    'telecom_intervention': 'telecom_intervention',
    'telecom_hr_ma': 'telecom_hr_ma',
    'telecom_equipment': 'telecom_equipment',
    'telecom_fleet': 'telecom_fleet',
    'telecom_project': 'telecom_project',
    'telecom_ao': 'telecom_ao',
    'telecom_contract': 'telecom_contract',
    'telecom_finance_ma': 'telecom_finance_ma',
    'telecom_reporting': 'telecom_reporting',
    'telecom_cost': 'telecom_cost',
    'telecom_margin': 'telecom_margin',
}


class TelecomTenant(models.Model):
    _name = 'telecom.tenant'
    _description = 'Tenant TelecomERP'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # -- Identity --
    name = fields.Char(
        string='Raison sociale', required=True, tracking=True,
    )
    subdomain = fields.Char(
        string='Sous-domaine', required=True, tracking=True,
        help='Sous-domaine unique : client1.telecomerp.ma',
    )
    db_name = fields.Char(
        string='Base de données', compute='_compute_db_name', store=True,
        readonly=True,
    )
    state = fields.Selection(
        TENANT_STATE, string='État', default='draft',
        tracking=True, index=True,
    )

    # -- Contact --
    contact_name = fields.Char(string='Contact principal')
    contact_email = fields.Char(string='Email')
    contact_phone = fields.Char(string='Téléphone')

    # -- Company info --
    ice = fields.Char(string='ICE (15 chiffres)', size=15)
    city = fields.Char(string='Ville')
    forme_juridique = fields.Selection([
        ('sarl', 'SARL'), ('sa', 'SA'), ('sarl_au', 'SARL AU'),
        ('sas', 'SAS'), ('auto_entrepreneur', 'Auto-entrepreneur'),
    ], string='Forme juridique')

    # -- Configuration --
    language = fields.Selection([
        ('fr_FR', 'Français'), ('ar_001', 'Arabe'), ('en_US', 'English'),
    ], string='Langue', default='fr_FR')
    currency = fields.Selection([
        ('MAD', 'MAD — Dirham marocain'),
    ], string='Devise', default='MAD')

    # -- Capabilities --
    cap_site = fields.Boolean(string='Sites & Infrastructure', default=True)
    cap_intervention = fields.Boolean(string='Interventions terrain', default=True)
    cap_hr = fields.Boolean(string='RH & Paie marocaine', default=True)
    cap_equipment = fields.Boolean(string='Équipements', default=True)
    cap_fleet = fields.Boolean(string='Parc véhicules', default=False)
    cap_project = fields.Boolean(string='Projets & Chantiers', default=True)
    cap_ao = fields.Boolean(string='Appels d\'offres', default=False)
    cap_contract = fields.Boolean(string='Contrats & SLA', default=True)
    cap_finance = fields.Boolean(string='Finance CCAG', default=True)
    cap_cost = fields.Boolean(string='Coûts & Rentabilité', default=True)
    cap_reporting = fields.Boolean(string='Reporting', default=True)

    # -- YAML profile --
    yaml_profile = fields.Text(
        string='Profil YAML',
        help='Profil de configuration complet au format YAML.',
    )
    yaml_valid = fields.Boolean(
        string='YAML valide', compute='_compute_yaml_valid',
    )

    # -- Provisioning --
    provision_date = fields.Datetime(string='Date de provisioning')
    provision_log = fields.Text(string='Log de provisioning')
    admin_password = fields.Char(string='Mot de passe admin initial')

    # -- Subscription --
    plan = fields.Selection([
        ('starter', 'Starter (500 MAD/mois)'),
        ('pro', 'Pro (1000 MAD/mois)'),
        ('enterprise', 'Enterprise (1500 MAD/mois)'),
    ], string='Formule', default='pro')
    date_start = fields.Date(string='Début abonnement')
    date_end = fields.Date(string='Fin abonnement')
    monthly_price = fields.Float(string='Prix mensuel (MAD)')

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
    )

    # -- SQL Constraints --
    _sql_constraints = [
        ('subdomain_uniq', 'UNIQUE(subdomain)', 'Ce sous-domaine est déjà utilisé.'),
    ]

    # -- Computed --
    @api.depends('subdomain')
    def _compute_db_name(self):
        for rec in self:
            if rec.subdomain:
                clean = re.sub(r'[^a-z0-9]', '_', rec.subdomain.lower())
                rec.db_name = f'telecom_{clean}'
            else:
                rec.db_name = False

    @api.depends('yaml_profile')
    def _compute_yaml_valid(self):
        for rec in self:
            if not rec.yaml_profile:
                rec.yaml_valid = False
                continue
            try:
                data = yaml.safe_load(rec.yaml_profile)
                rec.yaml_valid = bool(
                    data and isinstance(data, dict)
                    and 'tenant' in data
                    and 'capabilities' in data
                )
            except Exception:
                rec.yaml_valid = False

    # -- Constraints --
    @api.constrains('subdomain')
    def _check_subdomain(self):
        for rec in self:
            if rec.subdomain and not re.match(r'^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$', rec.subdomain):
                raise ValidationError(_(
                    'Le sous-domaine doit contenir uniquement des lettres minuscules, '
                    'chiffres et tirets (3-32 caractères).'
                ))

    @api.constrains('ice')
    def _check_ice(self):
        for rec in self:
            if rec.ice and not re.match(r'^\d{15}$', rec.ice):
                raise ValidationError(_("L'ICE doit contenir exactement 15 chiffres."))

    # -- Actions --
    def action_generate_yaml(self):
        """Generate YAML profile from form fields."""
        self.ensure_one()
        caps = []
        cap_map = {
            'cap_site': 'telecom_site',
            'cap_intervention': 'telecom_intervention',
            'cap_hr': 'telecom_hr_ma',
            'cap_equipment': 'telecom_equipment',
            'cap_fleet': 'telecom_fleet',
            'cap_project': 'telecom_project',
            'cap_ao': 'telecom_ao',
            'cap_contract': 'telecom_contract',
            'cap_finance': 'telecom_finance_ma',
            'cap_cost': 'telecom_cost',
            'cap_reporting': 'telecom_reporting',
        }
        for field, module in cap_map.items():
            if getattr(self, field):
                caps.append(module)

        profile = {
            'schema_version': '1.0',
            'tenant': {
                'name': self.name,
                'subdomain': self.subdomain,
                'language': self.language or 'fr_FR',
                'country': 'MA',
                'currency': self.currency or 'MAD',
            },
            'organization': {
                'company_name': self.name,
                'ice': self.ice or '',
                'city': self.city or '',
                'forme_juridique': self.forme_juridique or 'sarl',
            },
            'capabilities': {
                'enabled': caps,
            },
        }
        self.yaml_profile = yaml.dump(profile, allow_unicode=True, default_flow_style=False)

    def action_provision(self):
        """Provision a new tenant database."""
        self.ensure_one()
        if self.state not in ('draft',):
            raise UserError(_('Seul un tenant en brouillon peut être provisionné.'))
        if not self.subdomain:
            raise UserError(_('Le sous-domaine est obligatoire.'))

        self.write({'state': 'provisioning'})

        log_lines = []
        try:
            import odoo
            db_name = self.db_name

            # 1. Create database
            log_lines.append(f'Création de la base {db_name}...')
            odoo.service.db.exp_create_database(
                db_name, False, self.language or 'fr_FR',
                self.admin_password or 'admin',
            )
            log_lines.append(f'Base {db_name} créée.')

            # 2. Install modules
            modules_to_install = ['telecom_base', 'telecom_localization_ma']
            cap_map = {
                'cap_site': 'telecom_site',
                'cap_intervention': 'telecom_intervention',
                'cap_hr': 'telecom_hr_ma',
                'cap_equipment': 'telecom_equipment',
                'cap_fleet': 'telecom_fleet',
                'cap_project': 'telecom_project',
                'cap_ao': 'telecom_ao',
                'cap_contract': 'telecom_contract',
                'cap_finance': 'telecom_finance_ma',
                'cap_cost': 'telecom_cost',
                'cap_reporting': 'telecom_reporting',
            }
            for field, module in cap_map.items():
                if getattr(self, field):
                    modules_to_install.append(module)

            log_lines.append(f'Modules à installer : {", ".join(modules_to_install)}')

            # Install in new DB
            new_registry = odoo.registry(db_name)
            with new_registry.cursor() as cr:
                new_env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

                # Install modules
                for mod_name in modules_to_install:
                    mod = new_env['ir.module.module'].search([('name', '=', mod_name)], limit=1)
                    if mod and mod.state != 'installed':
                        mod.button_immediate_install()
                        log_lines.append(f'  Installé : {mod_name}')

                # 3. Configure company
                company = new_env.company
                company.write({
                    'name': self.name,
                    'city': self.city or '',
                })
                if self.ice:
                    company.write({'ice': self.ice})
                if self.forme_juridique:
                    company.write({'forme_juridique': self.forme_juridique})

                # Set language
                if self.language:
                    new_env['res.lang']._activate_lang(self.language)
                    admin = new_env['res.users'].browse(2)
                    admin.write({'lang': self.language})

                log_lines.append(f'Société configurée : {self.name}')
                cr.commit()

            self.write({
                'state': 'active',
                'provision_date': fields.Datetime.now(),
                'provision_log': '\n'.join(log_lines),
                'date_start': date.today(),
            })

        except Exception as e:
            log_lines.append(f'ERREUR : {str(e)}')
            self.write({
                'state': 'draft',
                'provision_log': '\n'.join(log_lines),
            })
            raise UserError(_('Erreur de provisioning :\n%s') % str(e))

    def action_suspend(self):
        for rec in self:
            if rec.state != 'active':
                raise UserError(_('Seul un tenant actif peut être suspendu.'))
            rec.state = 'suspended'

    def action_reactivate(self):
        for rec in self:
            if rec.state != 'suspended':
                raise UserError(_('Seul un tenant suspendu peut être réactivé.'))
            rec.state = 'active'

    def action_archive_tenant(self):
        for rec in self:
            rec.state = 'archived'
