/** @odoo-module **/

import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * AssistantPopup — Floating chat widget (FAB + panel)
 *
 * Mounted globally in the Odoo web client.
 * - FAB button: bottom-right, always visible
 * - Chat panel: 400x500px overlay, persists across navigations
 * - Calls /assistant/chat JSON-RPC endpoint
 */
class AssistantPopup extends Component {
    static template = "telecom_assistant.AssistantPopup";

    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            isOpen: false,
            messages: [],
            inputText: "",
            conversationId: null,
            isLoading: false,
            toolCalls: [],
        });
        this.messagesEnd = useRef("messagesEnd");
    }

    togglePanel() {
        this.state.isOpen = !this.state.isOpen;
    }

    closePanel() {
        this.state.isOpen = false;
    }

    onInputKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }

    async sendMessage() {
        const text = this.state.inputText.trim();
        if (!text || this.state.isLoading) return;

        // Add user message to UI
        this.state.messages.push({
            role: "user",
            content: text,
        });
        this.state.inputText = "";
        this.state.isLoading = true;
        this.scrollToBottom();

        try {
            // Get current context (model + record being viewed)
            let contextModel = null;
            let contextId = null;
            try {
                const action = this.env?.services?.action;
                if (action?.currentController?.props?.resModel) {
                    contextModel = action.currentController.props.resModel;
                    contextId = action.currentController.props.resId || null;
                }
            } catch (e) {
                // Context capture is best-effort
            }

            const result = await this.rpc("/assistant/chat", {
                message: text,
                conversation_id: this.state.conversationId,
                context_model: contextModel,
                context_id: contextId,
            });

            this.state.conversationId = result.conversation_id;
            this.state.messages.push({
                role: "assistant",
                content: result.response,
                tokens: result.tokens,
                toolCalls: result.tool_calls || [],
            });
            this.state.toolCalls = result.tool_calls || [];
        } catch (error) {
            this.state.messages.push({
                role: "assistant",
                content: "Erreur de connexion. Vérifiez que la clé API Claude est configurée.",
            });
        }

        this.state.isLoading = false;
        this.scrollToBottom();
    }

    newConversation() {
        this.state.messages = [];
        this.state.conversationId = null;
        this.state.toolCalls = [];
    }

    scrollToBottom() {
        setTimeout(() => {
            const el = this.messagesEnd?.el;
            if (el) el.scrollIntoView({ behavior: "smooth" });
        }, 100);
    }
}

// Register as a systray item (appears in the top-right area)
// But we want it as a FAB — so we use the main_components registry instead
registry.category("main_components").add("AssistantPopup", {
    Component: AssistantPopup,
});
