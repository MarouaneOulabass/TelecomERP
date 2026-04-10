/** @odoo-module **/

/**
 * Fix for mobile browsers where navigator.clipboard is unavailable (HTTP context).
 * Odoo 17 assumes clipboard API is always available, which crashes on:
 * - Mobile Safari without HTTPS
 * - Some Android browsers without HTTPS
 *
 * This patch wraps the clipboard call in a try/catch to prevent the crash.
 */
import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";

// Ensure clipboard API exists even without HTTPS
if (!browser.navigator?.clipboard) {
    browser.navigator = browser.navigator || {};
    browser.navigator.clipboard = {
        writeText: async (text) => {
            console.warn("Clipboard API not available (HTTPS required). Text not copied:", text);
        },
        readText: async () => {
            console.warn("Clipboard API not available (HTTPS required).");
            return "";
        },
    };
}
