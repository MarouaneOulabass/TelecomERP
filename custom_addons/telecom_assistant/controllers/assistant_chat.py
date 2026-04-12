# -*- coding: utf-8 -*-
"""
HTTP API for the assistant popup widget.
Called by the OWL frontend component via JSON-RPC.
"""
import json
from odoo import http
from odoo.http import request


class AssistantChatController(http.Controller):

    @http.route('/assistant/chat', type='json', auth='user')
    def chat(self, message, conversation_id=None, context_model=None, context_id=None):
        """Process a chat message and return the assistant's response.

        Args:
            message: User's question text
            conversation_id: Existing conversation ID (or None for new)
            context_model: Current Odoo model being viewed
            context_id: Current record ID being viewed
        Returns:
            dict with response, conversation_id, tool_calls
        """
        env = request.env

        # Get or create conversation
        Conversation = env['telecom.assistant.conversation']
        if conversation_id:
            conv = Conversation.browse(conversation_id)
            if not conv.exists():
                conv = Conversation.create({})
        else:
            conv = Conversation.create({})

        # Add context to message if available
        full_message = message
        if context_model and context_id:
            try:
                record = env[context_model].browse(int(context_id))
                if record.exists():
                    rec_name = getattr(record, 'name', '') or getattr(record, 'display_name', '') or str(record.id)
                    model_desc = env[context_model]._description or context_model
                    full_message = "[Contexte: %s — %s (id=%s)]\n\n%s" % (
                        model_desc, rec_name, context_id, message
                    )
            except Exception:
                pass

        # Set message and send
        conv.user_input = full_message
        conv.action_send()

        # Get last assistant message
        last_msg = conv.message_ids.sorted('sequence', reverse=True)[:1]
        response_text = last_msg.content if last_msg else 'Erreur'
        tokens = last_msg.tokens_used if last_msg else 0

        # Get tool calls
        tool_calls = []
        if last_msg and last_msg.tool_call_ids:
            for tc in last_msg.tool_call_ids:
                tool_calls.append({
                    'tool': tc.tool_name,
                    'duration_ms': tc.duration_ms,
                    'success': tc.success,
                })

        return {
            'response': response_text,
            'conversation_id': conv.id,
            'tokens': tokens,
            'tool_calls': tool_calls,
        }

    @http.route('/assistant/history', type='json', auth='user')
    def history(self, conversation_id):
        """Get full conversation history."""
        conv = request.env['telecom.assistant.conversation'].browse(conversation_id)
        if not conv.exists():
            return {'messages': []}

        messages = []
        for msg in conv.message_ids.sorted('sequence'):
            messages.append({
                'role': msg.role,
                'content': msg.content,
                'timestamp': str(msg.timestamp) if msg.timestamp else '',
                'tokens': msg.tokens_used or 0,
            })
        return {'messages': messages}

    @http.route('/assistant/conversations', type='json', auth='user')
    def conversations(self):
        """List user's recent conversations."""
        convs = request.env['telecom.assistant.conversation'].search(
            [('user_id', '=', request.env.user.id)],
            order='create_date desc', limit=20,
        )
        result = []
        for c in convs:
            first_msg = c.message_ids.filtered(lambda m: m.role == 'user')[:1]
            result.append({
                'id': c.id,
                'preview': (first_msg.content or '')[:80] if first_msg else 'Nouvelle conversation',
                'date': str(c.create_date)[:16] if c.create_date else '',
                'messages': len(c.message_ids),
            })
        return {'conversations': result}
