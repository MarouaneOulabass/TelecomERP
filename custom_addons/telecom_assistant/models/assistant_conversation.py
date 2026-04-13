# -*- coding: utf-8 -*-
"""
Assistant Conversation — chat interface with tool-use tracing.
"""
import json
import time
import os
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from . import assistant_tool_registry as registry

_logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Tu es l'assistant TelecomERP, un assistant professionnel pour les entreprises
télécom marocaines. Tu réponds en français (ou arabe/darija si l'utilisateur le demande).

RÈGLES STRICTES :
1. Tu ne donnes JAMAIS de chiffre que tu n'as pas obtenu d'un outil. Si tu n'as pas l'info, dis-le.
2. Tu utilises les outils disponibles pour répondre aux questions sur les données.
3. Si aucun outil ne peut répondre, dis-le clairement et propose des questions que tu peux traiter.
4. Sois concis et professionnel. Pas de bavardage.
5. Les montants sont en MAD (Dirham marocain).

Tu as accès aux outils suivants pour interroger les données de l'ERP."""


class AssistantToolCall(models.Model):
    """Trace of each tool call made by the assistant."""
    _name = 'telecom.assistant.tool.call'
    _description = 'Appel d\'outil assistant'
    _order = 'id'

    message_id = fields.Many2one(
        'telecom.assistant.message', required=True, ondelete='cascade',
    )
    tool_name = fields.Char(string='Outil', required=True)
    parameters = fields.Text(string='Paramètres (JSON)')
    result = fields.Text(string='Résultat (JSON)')
    duration_ms = fields.Integer(string='Durée (ms)')
    success = fields.Boolean(string='Succès', default=True)
    error_message = fields.Char(string='Erreur')


class AssistantMessage(models.Model):
    _name = 'telecom.assistant.message'
    _description = 'Message assistant'
    _order = 'sequence, id'

    conversation_id = fields.Many2one(
        'telecom.assistant.conversation', required=True, ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    role = fields.Selection([
        ('user', 'Utilisateur'),
        ('assistant', 'Assistant'),
    ], string='Rôle', required=True)
    content = fields.Text(string='Message', required=True)
    tool_call_ids = fields.One2many(
        'telecom.assistant.tool.call', 'message_id', string='Outils appelés',
    )
    tokens_used = fields.Integer(string='Tokens utilisés')
    timestamp = fields.Datetime(default=fields.Datetime.now)


class AssistantConversation(models.Model):
    _name = 'telecom.assistant.conversation'
    _description = 'Conversation assistant'
    _order = 'create_date desc'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)
    user_id = fields.Many2one(
        'res.users', string='Utilisateur', default=lambda self: self.env.user,
        readonly=True,
    )
    message_ids = fields.One2many(
        'telecom.assistant.message', 'conversation_id', string='Messages',
    )
    message_count = fields.Integer(compute='_compute_message_count')
    user_input = fields.Text(string='Votre question')
    total_tokens = fields.Integer(string='Tokens totaux', compute='_compute_total_tokens')
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
    )

    @api.depends('user_id', 'create_date')
    def _compute_display_name(self):
        for rec in self:
            dt = rec.create_date.strftime('%d/%m %H:%M') if rec.create_date else ''
            user = rec.user_id.name or ''
            rec.display_name = '%s — %s' % (user, dt)

    def _compute_message_count(self):
        for rec in self:
            rec.message_count = len(rec.message_ids)

    def _compute_total_tokens(self):
        for rec in self:
            rec.total_tokens = sum(m.tokens_used or 0 for m in rec.message_ids)

    def _get_claude_client(self):
        try:
            import anthropic
        except ImportError:
            raise UserError(_(
                "Le module 'anthropic' n'est pas installé.\n"
                "pip install anthropic"
            ))
        api_key = self.env['ir.config_parameter'].sudo().get_param('telecom.anthropic_api_key', '')
        if not api_key:
            api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        if not api_key:
            raise UserError(_(
                "Clé API Claude non configurée.\n"
                "Settings > Paramètres système > telecom.anthropic_api_key"
            ))
        return anthropic.Anthropic(api_key=api_key)

    def action_send(self):
        """Send user message, call tools, get response."""
        self.ensure_one()
        if not self.user_input:
            return

        question = self.user_input
        self.user_input = False
        seq = len(self.message_ids) * 10 + 10

        # Save user message
        user_msg = self.env['telecom.assistant.message'].create({
            'conversation_id': self.id,
            'role': 'user',
            'content': question,
            'sequence': seq,
        })

        # Build conversation history for Claude
        messages = []
        for msg in self.message_ids.sorted('sequence'):
            messages.append({'role': msg.role, 'content': msg.content})

        # Get available tools
        tools = registry.get_all_tools()

        try:
            # Budget check: limit total tokens per tenant per month
            monthly_limit = int(self.env['ir.config_parameter'].sudo().get_param(
                'telecom.assistant_monthly_token_limit', '500000'
            ))
            if monthly_limit > 0 and self.total_tokens > monthly_limit:
                raise UserError(_(
                    "Budget mensuel de l'assistant dépassé (%d tokens / %d max).\n"
                    "Contactez l'administrateur."
                ) % (self.total_tokens, monthly_limit))

            client = self._get_claude_client()

            # Call Claude with tools — timeout via httpx (anthropic client default: 600s)
            response = client.messages.create(
                model='claude-sonnet-4-20250514',
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=tools if tools else None,
                timeout=30.0,  # 30s timeout per API call
            )

            # Process response — handle tool use
            assistant_text = ''
            tool_calls_made = []
            tokens = response.usage.input_tokens + response.usage.output_tokens

            # Loop for multi-turn tool use
            current_messages = list(messages)
            current_response = response
            max_iterations = 5

            for _ in range(max_iterations):
                if current_response.stop_reason == 'tool_use':
                    # Extract tool calls
                    tool_results = []
                    for block in current_response.content:
                        if block.type == 'tool_use':
                            tool_name = block.name
                            tool_input = block.input
                            tool_id = block.id

                            # Call the tool
                            start = time.time()
                            try:
                                # SQL direct : tool execution must use user's env for record rule isolation
                                result = registry.call_tool(tool_name, self.env, tool_input)
                                duration = int((time.time() - start) * 1000)
                                result_json = json.dumps(result, ensure_ascii=False, default=str)

                                tool_calls_made.append({
                                    'tool_name': tool_name,
                                    'parameters': json.dumps(tool_input, ensure_ascii=False),
                                    'result': result_json[:5000],
                                    'duration_ms': duration,
                                    'success': True,
                                })

                                tool_results.append({
                                    'type': 'tool_result',
                                    'tool_use_id': tool_id,
                                    'content': result_json,
                                })
                            except Exception as e:
                                duration = int((time.time() - start) * 1000)
                                tool_calls_made.append({
                                    'tool_name': tool_name,
                                    'parameters': json.dumps(tool_input, ensure_ascii=False),
                                    'result': '',
                                    'duration_ms': duration,
                                    'success': False,
                                    'error_message': str(e)[:200],
                                })
                                tool_results.append({
                                    'type': 'tool_result',
                                    'tool_use_id': tool_id,
                                    'content': json.dumps({'error': str(e)}),
                                    'is_error': True,
                                })

                    # Continue conversation with tool results
                    current_messages.append({'role': 'assistant', 'content': current_response.content})
                    current_messages.append({'role': 'user', 'content': tool_results})

                    current_response = client.messages.create(
                        model='claude-sonnet-4-20250514',
                        max_tokens=2048,
                        system=SYSTEM_PROMPT,
                        messages=current_messages,
                        tools=tools if tools else None,
                        timeout=30.0,  # Same timeout for tool-use continuation
                    )
                    tokens += current_response.usage.input_tokens + current_response.usage.output_tokens
                else:
                    # Final text response
                    for block in current_response.content:
                        if hasattr(block, 'text'):
                            assistant_text += block.text
                    break

            # Save assistant message
            assistant_msg = self.env['telecom.assistant.message'].create({
                'conversation_id': self.id,
                'role': 'assistant',
                'content': assistant_text or 'Aucune réponse générée.',
                'sequence': seq + 5,
                'tokens_used': tokens,
            })

            # Save tool call traces
            for tc in tool_calls_made:
                tc['message_id'] = assistant_msg.id
                self.env['telecom.assistant.tool.call'].create(tc)

        except Exception as e:
            self.env['telecom.assistant.message'].create({
                'conversation_id': self.id,
                'role': 'assistant',
                'content': 'Erreur : %s' % str(e),
                'sequence': seq + 5,
            })

        self.env.cr.commit()
