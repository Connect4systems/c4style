(() => {
    "use strict";
    const api = frappe.c4style;
    if (!api) return;
    let unreadCount = 0;
    let initialized = false;
    let latestCreation = '';
    let fetching = false;
    let queued = false;
    let queuedNotify = false;
    let realtime = null;
    let audio = null;
    const known = new Set();

    function openNotifications() {
        document.querySelector('.c4style-tools-dialog[open]')?.close();
        frappe.route_options = { for_user: frappe.session.user };
        frappe.set_route("List", "Notification Log");
    }
    api.open_notifications = openNotifications;

    function syncBadge() {
        document.querySelectorAll('[data-c4style-tools], [data-c4style-notifications-link]').forEach(element => {
            let badge = element.querySelector('.c4style-notification-count');
            if (!badge) {
                badge = document.createElement('span'); badge.className = 'c4style-notification-count';
                badge.setAttribute('aria-hidden', 'true'); element.appendChild(badge);
            }
            const label = unreadCount > 99 ? '99+' : String(unreadCount);
            if (badge.textContent !== label) badge.textContent = label;
            badge.hidden = unreadCount === 0;
            const base = element.matches('[data-c4style-tools]') ? __('Appearance tools') : __('My notifications');
            const title = unreadCount ? `${base} (${unreadCount} ${__('unread')})` : base;
            element.setAttribute('aria-label', base);
            element.setAttribute('aria-description', `${unreadCount} ${__('unread notifications')}`);
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
    function popup(records) {
        document.querySelector('.c4style-notification-toast')?.remove();
        const toast = document.createElement('aside'); toast.className = 'c4style-notification-toast';
        toast.setAttribute('role', 'status'); toast.setAttribute('aria-live', 'polite');
        const title = document.createElement('strong'); title.textContent = __('New notification');
        const message = document.createElement('p'); message.textContent = records[0].subject || __('You have a new notification');
        const view = document.createElement('button'); view.type = 'button'; view.className = 'btn btn-primary btn-sm';
        view.textContent = __('View notifications'); view.addEventListener('click', () => { toast.remove(); openNotifications(); });
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
                if (!result || !Number.isInteger(result.unread_count) || !Array.isArray(result.notifications)) return;
                const records = result.notifications.filter(record => record && typeof record.name === 'string');
                const fresh = records.filter(record => !known.has(record.name)
                    && (!record.creation || !latestCreation || record.creation >= latestCreation));
                unreadCount = Math.max(0, result.unread_count); syncBadge();
                const enabled = frappe.boot?.notification_settings?.enabled;
                if (initialized && notify && fresh.length && enabled !== false && enabled !== 0) popup(fresh);
                records.forEach(record => known.add(record.name));
                records.forEach(record => {
                    if (typeof record.creation === 'string' && record.creation > latestCreation) latestCreation = record.creation;
                });
                // Bound memory for long-running Desk tabs while retaining recent deduplication.
                while (known.size > 1000) known.delete(known.values().next().value);
                initialized = true;
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
        frappe.realtime.on('indicator_hide', () => refresh(false));
    }
    api.refresh_notifications = () => refresh(false);
    function start() {
        installRealtime(); refresh(); syncBadge();
        if (window.jQuery) {
            window.jQuery(document).on('app_ready.c4styleNotifications', () => { installRealtime(); refresh(); });
            window.jQuery(document).on('ajaxComplete.c4styleNotifications', (event, xhr, settings) => {
                if (xhr.status >= 200 && xhr.status < 300 && /notification_log\.(mark_as_read|mark_all_as_read)/.test(settings.url || '')) refresh();
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
