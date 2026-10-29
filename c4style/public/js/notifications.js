(() => {
    "use strict";
    const api = frappe.c4style;
    if (!api) return;
    let unreadCount = 0;
    let pending = [];
    let listDialog = null;
    let fetching = false;
    let queued = false;
    let queuedNotify = false;
    let realtime = null;
    let audio = null;
    const storageKey = `c4style-pending-workflows:${frappe.session.user}`;
    let saved = [];
    try { saved = JSON.parse(sessionStorage.getItem(storageKey) || '[]'); } catch (error) {}
    const known = new Set(Array.isArray(saved) ? saved : []);

    function openNotifications() {
        document.querySelector('.c4style-tools-dialog[open]')?.close();
        if (!listDialog) {
            listDialog = new frappe.ui.Dialog({title: __('Pending workflows'), size: 'large',
                fields: [{fieldname: 'items', fieldtype: 'HTML'}]});
        }
        renderList();
        listDialog.show();
        refresh(false);
    }
    function renderList() {
        if (!listDialog) return;
        const host = listDialog.fields_dict.items.$wrapper[0];
        host.replaceChildren();
        if (!pending.length) {
            const empty = document.createElement('p');
            empty.textContent = __('No workflows require your action.'); host.appendChild(empty);
        }
        pending.forEach(record => {
            const row = document.createElement('div'); row.className = 'mb-3';
            const link = document.createElement('a');
            link.href = frappe.utils.get_form_link(record.doctype, record.document_name);
            link.textContent = record.subject;
            link.addEventListener('click', event => {
                event.preventDefault(); listDialog.hide();
                frappe.set_route('Form', record.doctype, record.document_name);
            });
            const actions = document.createElement('div'); actions.className = 'text-muted';
            actions.textContent = (record.actions || []).join(', ');
            row.append(link, actions); host.appendChild(row);
        });
    }
    api.open_notifications = openNotifications;

    function syncBadge() {
        document.querySelectorAll('[data-c4style-tools], [data-c4style-notifications-link]').forEach(element => {
            let badge = element.querySelector('.c4style-notification-count');
            if (!badge) {
                badge = document.createElement('span'); badge.className = 'c4style-notification-count';
                badge.setAttribute('aria-hidden', 'true'); element.appendChild(badge);
            }
            const label = String(unreadCount);
            if (badge.textContent !== label) badge.textContent = label;
            badge.hidden = unreadCount === 0;
            const base = element.matches('[data-c4style-tools]') ? __('Appearance tools') : __('Pending workflows');
            const title = unreadCount ? `${base} (${unreadCount} ${__('pending')})` : base;
            element.setAttribute('aria-label', base);
            element.setAttribute('aria-description', `${unreadCount} ${__('pending workflows')}`);
            element.title = title;
        });
    }
    async function unlockAudio() {
        try {
            const Context = window.AudioContext || window.webkitAudioContext;
            if (!Context) return;
            if (!audio) audio = new Context();
            if (audio.state === 'suspended') await audio.resume();
        } catch (error) { /* Visual notifications remain available if audio is blocked. */ }
    }
    function playBell() {
        if (!audio || audio.state !== 'running') return;
        try {
            [880, 1760].forEach((frequency, index) => {
                const oscillator = audio.createOscillator(); const gain = audio.createGain();
                oscillator.type = 'sine'; oscillator.frequency.value = frequency;
                gain.gain.setValueAtTime(0, audio.currentTime);
                gain.gain.linearRampToValueAtTime(index ? 0.08 : 0.16, audio.currentTime + 0.015);
                gain.gain.exponentialRampToValueAtTime(0.001, audio.currentTime + 0.8);
                oscillator.connect(gain); gain.connect(audio.destination);
                oscillator.start(); oscillator.stop(audio.currentTime + 0.85);
            });
        } catch (error) { /* A sound failure must not interrupt notification delivery. */ }
    }
    function popup(records, ownerUpdate = false) {
        document.querySelector('.c4style-notification-toast')?.remove();
        const toast = document.createElement('aside'); toast.className = 'c4style-notification-toast';
        toast.setAttribute('role', 'status'); toast.setAttribute('aria-live', 'polite');
        const title = document.createElement('strong'); title.textContent = ownerUpdate ? __('Workflow update') : __('Workflow action required');
        const message = document.createElement('p'); message.textContent = records[0].subject || __('A workflow requires your action');
        const view = document.createElement('button'); view.type = 'button'; view.className = 'btn btn-primary btn-sm';
        view.textContent = ownerUpdate ? __('Open document') : __('View pending workflows');
        view.addEventListener('click', () => {
            toast.remove();
            if (ownerUpdate) frappe.set_route('Form', records[0].doctype, records[0].document_name);
            else openNotifications();
        });
        const close = document.createElement('button'); close.type = 'button'; close.className = 'btn btn-default btn-sm';
        close.textContent = __('Dismiss'); close.addEventListener('click', () => toast.remove());
        const actions = document.createElement('div'); actions.className = 'c4style-notification-actions'; actions.append(view, close);
        if (!audio || audio.state !== 'running') {
            const enable = document.createElement('button'); enable.type = 'button'; enable.className = 'btn btn-default btn-sm';
            enable.textContent = __('Enable bell sound'); enable.addEventListener('click', async () => {
                await unlockAudio(); playBell(); if (audio?.state === 'running') enable.remove();
            }); actions.appendChild(enable);
        }
        toast.append(title, message, actions);
        const host = document.querySelector('.c4style-tools-dialog[open]') || document.body;
        host.appendChild(toast);
        // Popovers stay visible above an open Appearance dialog without blocking Desk.
        if (typeof toast.showPopover === 'function') { toast.setAttribute('popover', 'manual'); toast.showPopover(); }
        playBell();
    }
    function refresh(notify = false) {
        if (!frappe.session?.user || frappe.session.user === 'Guest') return;
        if (fetching) { queued = true; queuedNotify = queuedNotify || notify; return; }
        fetching = true;
        frappe.call({ method: 'c4style.notifications.get_notifications',
            callback: response => {
                const result = response.message;
                if (!result || !Number.isInteger(result.pending_count) || !Array.isArray(result.notifications)) return;
                const records = result.notifications.filter(record => record && typeof record.name === 'string');
                const fresh = records.filter(record => !known.has(record.name));
                unreadCount = Math.max(0, result.pending_count);
                pending = records; syncBadge(); renderList();
                const enabled = frappe.boot?.notification_settings?.enabled;
                if (notify && fresh.length && enabled !== false && enabled !== 0) popup(fresh);
                known.clear(); records.forEach(record => known.add(record.name));
                try { sessionStorage.setItem(storageKey, JSON.stringify([...known])); } catch (error) {}
            },
            error: () => {},
            always: () => {
                fetching = false;
                if (queued) { const next = queuedNotify; queued = queuedNotify = false; refresh(next); }
            },
        });
    }
    function installRealtime() {
        if (!frappe.realtime?.on || !frappe.realtime.socket || realtime === frappe.realtime.socket) return;
        realtime = frappe.realtime.socket;
        frappe.realtime.on('notification', () => refresh(true));
        frappe.realtime.on('doc_update', () => refresh(true));
        frappe.realtime.on('c4style_workflow_owner_update', record => {
            const enabled = frappe.boot?.notification_settings?.enabled;
            if (record?.doctype && record?.document_name && enabled !== false && enabled !== 0) popup([record], true);
            refresh(true);
        });
        frappe.realtime.on('indicator_hide', () => refresh(false));
    }
    api.refresh_notifications = () => refresh(false);
    function start() {
        installRealtime(); refresh(true); syncBadge();
        if (window.jQuery) {
            window.jQuery(document).on('app_ready.c4styleNotifications', () => { installRealtime(); refresh(); });
            window.jQuery(document).on('ajaxComplete.c4styleNotifications', (event, xhr, settings) => {
                const method = `${settings.url || ''} ${typeof settings.data === 'string' ? settings.data : settings.data?.cmd || ''}`;
                if (xhr.status >= 200 && xhr.status < 300 && !xhr.responseJSON?.exc
                    && /(apply_workflow|frappe\.desk\.form\.(save|run_method))/.test(method)) refresh();
            });
        }
        document.addEventListener('pointerdown', unlockAudio, { passive: true });
        document.addEventListener('keydown', unlockAudio);
        window.addEventListener('focus', () => refresh(true));
        document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(true); });
        window.setInterval(() => { if (!document.hidden) { installRealtime(); refresh(true); } }, 30000);
        let scheduled = false;
        new MutationObserver(() => {
            if (scheduled) return;
            scheduled = true; requestAnimationFrame(() => { scheduled = false; syncBadge(); });
        }).observe(document.body, { childList: true, subtree: true });
    }
    if (document.body) start(); else document.addEventListener('DOMContentLoaded', start, { once: true });
})();
