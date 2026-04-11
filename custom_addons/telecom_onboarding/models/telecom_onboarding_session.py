# -*- coding: utf-8 -*-
"""
telecom.onboarding.session — AI-assisted client onboarding
=============================================================
Upload company docs → AI extracts info → interactive Q&A → provision tenant.

Uses Claude API (vision) to read PDFs/images of:
- Registre de Commerce (RC)
- Organigramme
- Statuts de la société
- Patente / ICE
"""
import base64
import json
import yaml
import logging
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

SESSION_STATES = [
    ('upload', '1. Upload documents'),
    ('extracting', '2. Extraction IA...'),
    ('review', '3. Vérification & questions'),
    ('configuring', '4. Configuration modules'),
    ('provisioning', '5. Provisioning...'),
    ('done', 'Terminé'),
    ('error', 'Erreur'),
]


class TelecomOnboardingDocument(models.Model):
    _name = 'telecom.onboarding.document'
    _description = 'Document uploadé pour onboarding'

    session_id = fields.Many2one(
        'telecom.onboarding.session', required=True, ondelete='cascade',
    )
    name = fields.Char(string='Nom du document', required=True)
    doc_type = fields.Selection([
        ('rc', 'Registre de Commerce'),
        ('ice', 'Certificat ICE'),
        ('patente', 'Patente'),
        ('statuts', 'Statuts de la société'),
        ('organigramme', 'Organigramme'),
        ('autre', 'Autre document'),
    ], string='Type', default='autre')
    file = fields.Binary(string='Fichier', required=True, attachment=True)
    file_name = fields.Char(string='Nom fichier')
    extracted_text = fields.Text(string='Texte extrait par IA')


class TelecomOnboardingMessage(models.Model):
    _name = 'telecom.onboarding.message'
    _description = 'Message de conversation onboarding'
    _order = 'sequence, id'

    session_id = fields.Many2one(
        'telecom.onboarding.session', required=True, ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    role = fields.Selection([
        ('assistant', 'Agent IA'),
        ('user', 'Client'),
        ('system', 'Système'),
    ], string='Rôle', required=True)
    content = fields.Text(string='Message', required=True)
    timestamp = fields.Datetime(default=fields.Datetime.now)


class TelecomOnboardingSession(models.Model):
    _name = 'telecom.onboarding.session'
    _description = 'Session d\'onboarding IA'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(
        string='Session', compute='_compute_name', store=True,
    )
    state = fields.Selection(
        SESSION_STATES, string='Étape', default='upload', tracking=True,
    )

    # -- Documents --
    document_ids = fields.One2many(
        'telecom.onboarding.document', 'session_id', string='Documents',
    )
    document_count = fields.Integer(compute='_compute_doc_count')

    # -- Extracted data --
    extracted_data = fields.Text(
        string='Données extraites (JSON)',
        help='JSON brut extrait par Claude depuis les documents.',
    )
    company_name = fields.Char(string='Raison sociale')
    ice = fields.Char(string='ICE')
    if_number = fields.Char(string='IF')
    rc_number = fields.Char(string='RC')
    patente = fields.Char(string='Patente')
    city = fields.Char(string='Ville')
    forme_juridique = fields.Selection([
        ('sarl', 'SARL'), ('sa', 'SA'), ('sarl_au', 'SARL AU'),
        ('sas', 'SAS'), ('auto_entrepreneur', 'Auto-entrepreneur'),
    ], string='Forme juridique')
    capital_social = fields.Float(string='Capital social (MAD)')
    nb_employees = fields.Integer(string='Nombre d\'employés estimé')
    activities = fields.Text(string='Activités détectées')

    # -- Conversation --
    message_ids = fields.One2many(
        'telecom.onboarding.message', 'session_id', string='Conversation',
    )
    user_input = fields.Text(string='Votre réponse')

    # -- Module selection --
    cap_site = fields.Boolean(string='Sites & Infrastructure', default=True)
    cap_intervention = fields.Boolean(string='Interventions terrain', default=True)
    cap_hr = fields.Boolean(string='RH & Paie', default=True)
    cap_equipment = fields.Boolean(string='Équipements', default=False)
    cap_fleet = fields.Boolean(string='Parc véhicules', default=False)
    cap_project = fields.Boolean(string='Projets & Chantiers', default=True)
    cap_ao = fields.Boolean(string='Appels d\'offres', default=False)
    cap_contract = fields.Boolean(string='Contrats & SLA', default=True)
    cap_finance = fields.Boolean(string='Finance CCAG', default=True)
    cap_cost = fields.Boolean(string='Coûts & Rentabilité', default=True)
    cap_reporting = fields.Boolean(string='Reporting', default=True)

    # -- Output --
    yaml_profile = fields.Text(string='Profil YAML généré')
    tenant_id = fields.Many2one('telecom.tenant', string='Tenant créé')
    subdomain = fields.Char(string='Sous-domaine')

    # -- Config --
    api_key = fields.Char(
        string='Clé API Claude',
        help='Clé API Anthropic. Si vide, utilise la variable ANTHROPIC_API_KEY.',
    )

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
    )

    @api.depends('company_name', 'create_date')
    def _compute_name(self):
        for rec in self:
            if rec.company_name:
                rec.name = 'Onboarding — %s' % rec.company_name
            else:
                dt = rec.create_date.strftime('%d/%m %H:%M') if rec.create_date else 'Nouveau'
                rec.name = 'Onboarding — %s' % dt

    def _compute_doc_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)

    # ── Claude API ─────────────────────────────────────────────────

    def _get_claude_client(self):
        """Get anthropic client."""
        try:
            import anthropic
        except ImportError:
            raise UserError(_(
                "Le module 'anthropic' n'est pas installé.\n"
                "Installez-le : pip install anthropic"
            ))
        import os
        api_key = self.api_key or os.environ.get('ANTHROPIC_API_KEY', '')
        if not api_key:
            # Check Odoo config param
            api_key = self.env['ir.config_parameter'].sudo().get_param('telecom.anthropic_api_key', '')
        if not api_key:
            raise UserError(_(
                "Clé API Claude non configurée.\n"
                "Renseignez-la dans le formulaire ou dans Settings > Paramètres système > telecom.anthropic_api_key"
            ))
        return anthropic.Anthropic(api_key=api_key)

    def _call_claude(self, messages, system_prompt='', images=None):
        """Call Claude API with optional images."""
        client = self._get_claude_client()

        api_messages = []
        for msg in messages:
            content = msg.get('content', '')
            role = msg.get('role', 'user')
            if role == 'system':
                continue
            api_messages.append({'role': role, 'content': content})

        # Add images to the last user message
        if images and api_messages:
            last_msg = api_messages[-1]
            content_parts = []
            for img_data, media_type in images:
                content_parts.append({
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': media_type,
                        'data': img_data,
                    }
                })
            content_parts.append({
                'type': 'text',
                'text': last_msg['content'],
            })
            last_msg['content'] = content_parts

        response = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=4096,
            system=system_prompt,
            messages=api_messages,
        )
        return response.content[0].text

    # ── Actions ────────────────────────────────────────────────────

    def action_extract_documents(self):
        """Send uploaded documents to Claude for extraction."""
        self.ensure_one()
        if not self.document_ids:
            raise UserError(_('Veuillez uploader au moins un document.'))

        self.state = 'extracting'
        self.env.cr.commit()

        system_prompt = """Tu es un assistant spécialisé dans l'extraction d'informations
depuis des documents d'entreprise marocains. Tu extrais les données suivantes
au format JSON strict (pas de markdown, juste le JSON) :

{
  "company_name": "raison sociale",
  "ice": "15 chiffres ICE",
  "if_number": "identifiant fiscal",
  "rc_number": "registre de commerce",
  "patente": "numero patente",
  "city": "ville",
  "forme_juridique": "sarl|sa|sarl_au|sas|auto_entrepreneur",
  "capital_social": 0,
  "nb_employees_estimate": 0,
  "activities": ["deploiement fibre", "maintenance 4G", ...],
  "departments": ["Direction", "Technique", "Commercial", ...],
  "missing_info": ["liste des infos non trouvées dans les documents"]
}

Si une info n'est pas lisible, mets null. Ne devine pas. Indique les infos manquantes."""

        images = []
        for doc in self.document_ids:
            if doc.file:
                data = base64.b64encode(doc.file).decode('utf-8') if isinstance(doc.file, bytes) else doc.file.decode('utf-8') if isinstance(doc.file, bytes) else doc.file
                # Determine media type from filename
                fname = (doc.file_name or '').lower()
                if fname.endswith('.pdf'):
                    media_type = 'application/pdf'
                elif fname.endswith(('.jpg', '.jpeg')):
                    media_type = 'image/jpeg'
                elif fname.endswith('.png'):
                    media_type = 'image/png'
                else:
                    media_type = 'image/jpeg'
                images.append((data, media_type))

        try:
            result = self._call_claude(
                [{'role': 'user', 'content': 'Analyse ces documents d\'entreprise marocaine et extrais toutes les informations au format JSON.'}],
                system_prompt=system_prompt,
                images=images if images else None,
            )

            # Parse JSON from response
            self.extracted_data = result
            try:
                # Find JSON in response
                json_str = result
                if '{' in result:
                    start = result.index('{')
                    end = result.rindex('}') + 1
                    json_str = result[start:end]
                data = json.loads(json_str)

                self.company_name = data.get('company_name') or ''
                self.ice = data.get('ice') or ''
                self.if_number = data.get('if_number') or ''
                self.rc_number = data.get('rc_number') or ''
                self.patente = data.get('patente') or ''
                self.city = data.get('city') or ''
                self.forme_juridique = data.get('forme_juridique') or False
                self.capital_social = data.get('capital_social') or 0
                self.nb_employees = data.get('nb_employees_estimate') or 0
                activities = data.get('activities') or []
                self.activities = ', '.join(activities) if activities else ''

                # Suggest capabilities based on activities
                act_str = ' '.join(activities).lower()
                self.cap_fleet = 'vehicul' in act_str or 'terrain' in act_str
                self.cap_equipment = 'equip' in act_str or 'antenne' in act_str or 'fibre' in act_str
                self.cap_ao = 'appel' in act_str or 'marche' in act_str or 'ao' in act_str

                # Generate welcome message
                missing = data.get('missing_info') or []
                welcome = "J'ai analysé vos documents. Voici ce que j'ai extrait :\n\n"
                welcome += "• Société : %s\n" % (self.company_name or '?')
                welcome += "• ICE : %s\n" % (self.ice or 'non trouvé')
                welcome += "• Ville : %s\n" % (self.city or 'non trouvée')
                welcome += "• Forme juridique : %s\n" % (self.forme_juridique or 'non trouvée')
                welcome += "• Employés estimés : %d\n" % (self.nb_employees or 0)
                welcome += "• Activités : %s\n" % (self.activities or 'non détectées')

                if missing:
                    welcome += "\nInformations manquantes dans vos documents :\n"
                    for m in missing:
                        welcome += "• %s\n" % m
                    welcome += "\nPouvez-vous compléter ces informations ?"

                self.env['telecom.onboarding.message'].create({
                    'session_id': self.id,
                    'role': 'assistant',
                    'content': welcome,
                    'sequence': 10,
                })

            except (json.JSONDecodeError, ValueError):
                self.env['telecom.onboarding.message'].create({
                    'session_id': self.id,
                    'role': 'assistant',
                    'content': "J'ai lu vos documents mais je n'ai pas pu extraire les données de manière structurée. Voici ce que j'ai compris :\n\n%s\n\nPouvez-vous me confirmer les informations de votre société ?" % result[:500],
                    'sequence': 10,
                })

            self.state = 'review'

        except Exception as e:
            self.env['telecom.onboarding.message'].create({
                'session_id': self.id,
                'role': 'system',
                'content': 'Erreur lors de l\'extraction : %s' % str(e),
                'sequence': 10,
            })
            self.state = 'review'

        self.env.cr.commit()

    def action_send_message(self):
        """Send user message and get AI response."""
        self.ensure_one()
        if not self.user_input:
            return

        user_text = self.user_input
        seq = len(self.message_ids) * 10 + 10

        # Save user message
        self.env['telecom.onboarding.message'].create({
            'session_id': self.id,
            'role': 'user',
            'content': user_text,
            'sequence': seq,
        })
        self.user_input = False

        # Build conversation history
        system_prompt = """Tu es l'assistant d'onboarding de TelecomERP, un ERP pour les entreprises
télécom marocaines. Tu aides à configurer le compte du client.

Données extraites jusqu'ici :
- Société : %s
- ICE : %s
- Ville : %s
- Activités : %s
- Employés : %d

Tu dois :
1. Compléter les informations manquantes en posant des questions courtes
2. Recommander les modules adaptés à son activité
3. Quand tout est complet, dire "Je vais maintenant configurer votre espace."

Réponds en français, de manière professionnelle et concise.""" % (
            self.company_name or '?',
            self.ice or '?',
            self.city or '?',
            self.activities or '?',
            self.nb_employees or 0,
        )

        messages = []
        for msg in self.message_ids.sorted('sequence'):
            if msg.role in ('assistant', 'user'):
                messages.append({'role': msg.role, 'content': msg.content})

        try:
            response = self._call_claude(messages, system_prompt=system_prompt)
            self.env['telecom.onboarding.message'].create({
                'session_id': self.id,
                'role': 'assistant',
                'content': response,
                'sequence': seq + 5,
            })

            # Update fields from conversation if agent extracted new info
            if 'configurer votre espace' in response.lower() or 'provisioning' in response.lower():
                self.state = 'configuring'

        except Exception as e:
            self.env['telecom.onboarding.message'].create({
                'session_id': self.id,
                'role': 'system',
                'content': 'Erreur : %s' % str(e),
                'sequence': seq + 5,
            })

        self.env.cr.commit()

    def action_generate_and_provision(self):
        """Generate YAML and create tenant."""
        self.ensure_one()
        if not self.company_name:
            raise UserError(_('La raison sociale est obligatoire.'))
        if not self.subdomain:
            # Auto-generate subdomain from company name
            import re
            self.subdomain = re.sub(r'[^a-z0-9]', '-', self.company_name.lower())[:30].strip('-')

        self.state = 'provisioning'
        self.env.cr.commit()

        # Build capabilities list
        caps = ['telecom_base', 'telecom_localization_ma']
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
                'name': self.company_name,
                'subdomain': self.subdomain,
                'language': 'fr_FR',
                'country': 'MA',
                'currency': 'MAD',
            },
            'organization': {
                'company_name': self.company_name,
                'ice': self.ice or '',
                'if_number': self.if_number or '',
                'rc_number': self.rc_number or '',
                'patente': self.patente or '',
                'city': self.city or '',
                'forme_juridique': self.forme_juridique or 'sarl',
                'capital_social': self.capital_social or 0,
                'nb_employees': self.nb_employees or 0,
            },
            'capabilities': {
                'enabled': caps,
            },
        }

        self.yaml_profile = yaml.dump(profile, allow_unicode=True, default_flow_style=False)

        # Create tenant
        try:
            tenant_vals = {
                'name': self.company_name,
                'subdomain': self.subdomain,
                'ice': self.ice or '',
                'city': self.city or '',
                'forme_juridique': self.forme_juridique or False,
                'contact_name': '',
                'contact_email': '',
                'language': 'fr_FR',
                'yaml_profile': self.yaml_profile,
                'admin_password': 'admin',
            }
            for field in cap_map:
                tenant_vals[field] = getattr(self, field)

            tenant = self.env['telecom.tenant'].create(tenant_vals)
            self.tenant_id = tenant.id

            # Add completion message
            self.env['telecom.onboarding.message'].create({
                'session_id': self.id,
                'role': 'assistant',
                'content': "Configuration terminée ! Le tenant '%s' a été créé.\n\nSous-domaine : %s.telecomerp.ma\nModules activés : %d\n\nCliquez sur 'Provisionner' dans la fiche tenant pour créer la base de données." % (
                    self.company_name, self.subdomain, len(caps)),
                'sequence': 999,
            })

            self.state = 'done'
        except Exception as e:
            self.state = 'error'
            self.env['telecom.onboarding.message'].create({
                'session_id': self.id,
                'role': 'system',
                'content': 'Erreur de provisioning : %s' % str(e),
                'sequence': 999,
            })

        self.env.cr.commit()

    def action_reset(self):
        self.ensure_one()
        self.state = 'upload'
        self.message_ids.unlink()
        self.extracted_data = False
