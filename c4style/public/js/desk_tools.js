(() => {
    "use strict";
    const api = frappe.c4style;
    if (!api) return;
    let dismissedAnnouncement = null;
    const notePositions = new Map();
    const observedDropdowns = new WeakSet();
    const allowedWorkspaces = () => ((frappe.boot && frappe.boot.allowed_workspaces) || []).filter(item => !item.is_hidden);
    const button = (label, action, className = "btn btn-default") => {
        const element = document.createElement("button");
        element.type = "button"; element.className = className; element.textContent = __(label);
        element.addEventListener("click", action);
        return element;
    };
    function dialog(title, build) {
        const previous = document.querySelector(".c4style-tools-dialog");
        if (previous) { previous.close(); previous.remove(); }
        const element = document.createElement("dialog");
        element.className = "c4style-tools-dialog";
        const header = document.createElement("header");
        const heading = document.createElement("h3");
        heading.id = "c4style-dialog-title"; heading.textContent = __(title);
        element.setAttribute("aria-labelledby", heading.id);
        const close = button("Close", () => element.close(), "btn btn-default btn-sm");
        header.append(heading, close);
        const body = document.createElement("div"); body.className = "c4style-tools-body";
        element.append(header, body); build(body, element); document.body.appendChild(element);
        element.addEventListener("click", event => { if (event.target === element) element.close(); });
        element.addEventListener("close", () => element.remove(), { once: true });
        element.showModal();
        return element;
    }
    function workspaceLink(item) {
        const title = item.title || item.name || "";
        const slug = frappe.router && frappe.router.slug ? frappe.router.slug(title) : title.toLowerCase().replace(/\s+/g, "-");
        const anchor = document.createElement("a");
        anchor.href = "/app/" + (item.public ? "" : "private/") + encodeURIComponent(slug);
        anchor.className = "c4style-app-tile";
        const icon = document.createElement("span"); icon.className = "c4style-app-tile-icon";
        if (frappe.utils && frappe.utils.icon) icon.innerHTML = frappe.utils.icon(/^[a-z0-9-]+$/i.test(item.icon || "") ? item.icon : "folder-normal", "lg");
        else icon.textContent = title.slice(0, 1);
        const label = document.createElement("span"); label.textContent = __(title);
        anchor.append(icon, label); anchor.dataset.search = title.toLowerCase();
        return anchor;
    }
    function openLauncher() {
        dialog("Apps and workspaces", (body, element) => {
            const search = document.createElement("input"); search.type = "search";
            search.className = "form-control"; search.placeholder = __("Find a workspace");
            search.setAttribute("aria-label", __("Find a workspace"));
            const grid = document.createElement("div"); grid.className = "c4style-app-grid";
            allowedWorkspaces().forEach(item => grid.appendChild(workspaceLink(item)));
            const empty = document.createElement("p"); empty.textContent = __("No matching workspaces"); empty.hidden = true;
            search.addEventListener("input", () => {
                const value = search.value.trim().toLowerCase();
                grid.querySelectorAll("a").forEach(anchor => { anchor.hidden = !anchor.dataset.search.includes(value); });
                empty.hidden = !!grid.querySelector("a:not([hidden])");
            });
            grid.addEventListener("click", event => { if (event.target.closest("a")) element.close(); });
            body.append(search, grid, empty);
        });
    }
    function openPalettes() {
        if (!(frappe.boot.c4style || {}).can_manage) return;
        dialog("Choose site theme", body => {
            const explanation = document.createElement("p");
            explanation.textContent = __("These palettes update the shared site theme. Confirm before applying a palette to all users.");
            const grid = document.createElement("div"); grid.className = "c4style-palette-grid";
            Object.entries(api.palettes).forEach(([name, palette]) => {
                const choice = button(name, () => frappe.confirm(__("Apply {0} to the site for all users?", [name]), () => {
                    choice.disabled = true;
                    frappe.call({ method: "c4style.settings.save_settings", args: { settings: JSON.stringify(api.palette_settings(name)), scope: "site", palette: name },
                        callback: response => { api.apply_theme(response.message); frappe.show_alert({ message: __("Site style saved"), indicator: "green" }); },
                        always: () => { choice.disabled = false; },
                    });
                }), "c4style-palette-choice btn btn-default");
                const colors = document.createElement("span"); colors.className = "c4style-palette-dots"; colors.setAttribute("aria-hidden", "true");
                [palette.primary, palette.accent, palette.background, palette.secondary_background, palette.menu_background].forEach(color => {
                    const dot = document.createElement("i"); dot.style.backgroundColor = color; colors.appendChild(dot);
                });
                choice.prepend(colors); grid.appendChild(choice);
            });
            body.append(explanation, grid);
        });
    }
    function saveNote(note, onSaved) {
        const notes = api.get_personal().notes || [];
        const exists = notes.some(item => item.id === note.id);
        api.save_personal("notes", exists ? notes.map(item => item.id === note.id ? { ...note } : item) : [...notes, { ...note }], onSaved);
    }
    function deleteNote(id, onSaved) {
        api.save_personal("notes", (api.get_personal().notes || []).filter(item => item.id !== id), onSaved);
    }
    function openNotes() {
        let draft = (api.get_personal().notes || []).map(note => ({ ...note }));
        dialog("My sticky notes", body => {
            const hint = document.createElement("p"); hint.textContent = __("Private to your account. Saved notes return automatically after refresh. Minimize keeps a note; Delete removes it.");
            const list = document.createElement("div"); list.className = "c4style-notes-grid";
            function render() {
                list.replaceChildren();
                draft.forEach(note => {
                    const card = document.createElement("section"); card.className = "c4style-note"; card.dataset.color = note.color;
                    const text = document.createElement("textarea"); text.className = "form-control"; text.value = note.text; text.maxLength = 4000;
                    text.setAttribute("aria-label", __("Note text")); text.addEventListener("input", () => { note.text = text.value; });
                    const color = document.createElement("select"); color.className = "form-control"; color.setAttribute("aria-label", __("Note color"));
                    ["mint", "sun", "rose", "sky"].forEach(value => color.add(new Option(__(value), value)));
                    color.value = note.color; color.addEventListener("change", () => { note.color = color.value; card.dataset.color = note.color; });
                    const save = button("Save", () => saveNote(note), "btn btn-default btn-sm"); save.setAttribute("aria-label", __("Save note"));
                    const minimize = button(note.minimized ? "Restore" : "Minimize", () => {
                        const minimized = !note.minimized;
                        const saved = (api.get_personal().notes || []).find(item => item.id === note.id);
                        const update = () => { note.minimized = minimized; render(); };
                        if (saved) saveNote({ ...saved, minimized }, update);
                        else update();
                    }, "btn btn-default btn-sm");
                    minimize.setAttribute("aria-expanded", String(!note.minimized));
                    const remove = button("Delete", () => {
                        const saved = (api.get_personal().notes || []).some(item => item.id === note.id);
                        const update = () => { draft = draft.filter(item => item.id !== note.id); render(); };
                        if (saved) deleteNote(note.id, update);
                        else update();
                    }, "btn btn-default btn-sm"); remove.setAttribute("aria-label", __("Delete note"));
                    [save, minimize, remove].forEach(control => { control.dataset.c4stylePersonalAction = "true"; });
                    const actions = document.createElement("div"); actions.className = "c4style-note-actions"; actions.append(save, minimize, remove);
                    text.hidden = color.hidden = !!note.minimized;
                    card.append(text, color, actions); list.appendChild(card);
                });
            }
            const add = button("Add note", () => {
                if (draft.length >= 20) return;
                draft.push({ id: crypto.randomUUID(), text: "", color: "sun" }); render();
            });
            const save = button("Save notes", () => api.save_personal("notes", draft.map(note => ({ ...note }))), "btn btn-primary");
            save.dataset.c4stylePersonalAction = "true";
            const actions = document.createElement("div"); actions.className = "c4style-tools-actions"; actions.append(add, save);
            body.append(hint, list, actions); render();
        });
    }
    function syncPinnedNotes() {
        const notes = api.get_personal().notes || [];
        document.querySelectorAll(".c4style-note-window").forEach(card => {
            if (!notes.some(note => note.id === card.dataset.noteId)) card.remove();
        });
        notes.forEach((note, index) => {
            let card = Array.from(document.querySelectorAll(".c4style-note-window")).find(item => item.dataset.noteId === note.id);
            if (card) {
                const text = card.querySelector("textarea");
                if (text.value === card.dataset.savedText) text.value = note.text;
                card.dataset.savedText = note.text; card.dataset.color = note.color;
                card.classList.toggle("c4style-note-minimized", !!note.minimized);
                text.hidden = !!note.minimized;
                const minimize = card.querySelector("[data-note-minimize]");
                const minimizeLabel = __(note.minimized ? "Restore" : "Minimize");
                if (minimize.textContent !== minimizeLabel) minimize.textContent = minimizeLabel;
                minimize.setAttribute("aria-expanded", String(!note.minimized));
                return;
            }
            card = document.createElement("section"); card.className = "c4style-note c4style-note-window";
            card.dataset.noteId = note.id; card.dataset.color = note.color; card.dataset.savedText = note.text;
            card.setAttribute("aria-label", __("Pinned private note"));
            const header = document.createElement("div"); header.className = "c4style-note-move";
            const title = document.createElement("strong"); title.textContent = __("My note");
            title.tabIndex = 0; title.setAttribute("role", "button"); title.setAttribute("aria-label", __("Move note with arrow keys or drag"));
            header.append(title);
            const text = document.createElement("textarea"); text.className = "form-control"; text.value = note.text; text.maxLength = 4000;
            text.setAttribute("aria-label", __("Pinned note text"));
            const save = button("Save", () => {
                const saved = (api.get_personal().notes || []).find(item => item.id === note.id);
                if (saved) saveNote({ ...saved, text: text.value });
            }, "btn btn-default btn-sm");
            save.setAttribute("aria-label", __("Save note"));
            const minimize = button(note.minimized ? "Restore" : "Minimize", () => {
                const saved = (api.get_personal().notes || []).find(item => item.id === note.id);
                if (saved) saveNote({ ...saved, minimized: !saved.minimized });
            }, "btn btn-default btn-sm");
            minimize.dataset.noteMinimize = "true"; minimize.setAttribute("aria-expanded", String(!note.minimized));
            const remove = button("Delete", () => deleteNote(note.id), "btn btn-default btn-sm");
            remove.setAttribute("aria-label", __("Delete note"));
            [save, minimize, remove].forEach(control => { control.dataset.c4stylePersonalAction = "true"; });
            const actions = document.createElement("div"); actions.className = "c4style-note-actions"; actions.append(save, minimize, remove);
            card.classList.toggle("c4style-note-minimized", !!note.minimized); text.hidden = !!note.minimized;
            card.append(header, text, actions); document.body.appendChild(card);
            function place(x, y) {
                x = Math.max(8, Math.min(x, window.innerWidth - card.offsetWidth - 8));
                y = Math.max(8, Math.min(y, window.innerHeight - 60));
                card.style.left = `${x}px`; card.style.top = `${y}px`; notePositions.set(note.id, { x, y });
            }
            const saved = notePositions.get(note.id);
            const rail = document.querySelector(".c4style-app-menu");
            place(saved ? saved.x : (rail ? rail.offsetWidth : 0) + 24 + index * 24, saved ? saved.y : 115 + index * 24);
            let drag = null;
            header.addEventListener("pointerdown", event => {
                if (event.target.closest("button")) return;
                event.preventDefault(); const rect = card.getBoundingClientRect();
                drag = { x: event.clientX - rect.x, y: event.clientY - rect.y }; header.setPointerCapture(event.pointerId);
            });
            header.addEventListener("pointermove", event => { if (drag) place(event.clientX - drag.x, event.clientY - drag.y); });
            header.addEventListener("pointerup", () => { drag = null; });
            header.addEventListener("pointercancel", () => { drag = null; });
            header.addEventListener("keydown", event => {
                if (event.target !== title || !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) return;
                event.preventDefault(); const rect = card.getBoundingClientRect();
                place(rect.x + (event.key === "ArrowLeft" ? -10 : event.key === "ArrowRight" ? 10 : 0), rect.y + (event.key === "ArrowUp" ? -10 : event.key === "ArrowDown" ? 10 : 0));
            });
        });
    }
    function openTools() {
        dialog("Appearance tools", (body, element) => {
            const actions = document.createElement("div"); actions.className = "c4style-tools-actions";
            actions.append(button("Apps and workspaces", openLauncher), button("My sticky notes", openNotes));
            if ((frappe.boot.c4style || {}).can_manage) {
                actions.append(button("Choose site theme", openPalettes));
                actions.append(button("Style Settings", () => { element.close(); frappe.set_route("Form", "Style Settings"); }));
            }
            body.appendChild(actions);
        });
    }
    function syncAnnouncement() {
        const theme = api.get_theme();
        let strip = document.querySelector(".c4style-announcement");
        const text = theme.announcementText || "";
        if (!theme.enableAnnouncement || !text.trim() || text === dismissedAnnouncement) {
            if (strip) strip.remove();
            document.documentElement.style.setProperty("--c4style-announcement-height", "0px");
            return;
        }
        const navbar = document.querySelector(".navbar");
        if (!navbar) return;
        if (!strip) {
            strip = document.createElement("section"); strip.className = "c4style-announcement";
            strip.setAttribute("aria-label", __("Site announcement"));
            const viewport = document.createElement("div"); viewport.className = "c4style-announcement-viewport";
            const message = document.createElement("span"); message.className = "c4style-announcement-message";
            viewport.appendChild(message);
            const close = button("\u00d7", () => { dismissedAnnouncement = api.get_theme().announcementText; syncAnnouncement(); measureHeader(); }, "c4style-announcement-close");
            close.setAttribute("aria-label", __("Dismiss announcement"));
            strip.append(viewport, close); navbar.before(strip);
        }
        const message = strip.querySelector(".c4style-announcement-message");
        if (message.textContent !== text) message.textContent = text;
        const duration = theme.announcementSpeed;
        strip.style.setProperty("--c4style-announcement-duration", `${duration >= 5 && duration <= 120 ? duration : 24}s`);
        const viewport = strip.querySelector(".c4style-announcement-viewport");
        const overflow = Math.max(0, message.scrollWidth - viewport.clientWidth);
        strip.classList.toggle("c4style-announcement-overflow", overflow > 0);
        strip.style.setProperty("--c4style-announcement-travel", `${document.documentElement.dir === "rtl" ? overflow : -overflow}px`);
        document.documentElement.style.setProperty("--c4style-announcement-height", `${strip.offsetHeight}px`);
    }
    function syncBreadcrumbs() {
        const navbar = document.querySelector(".navbar .container");
        if (!navbar || !frappe.get_route) return;
        let bar = navbar.querySelector(".c4style-breadcrumbs");
        if (!bar) {
            bar = document.createElement("nav"); bar.className = "c4style-breadcrumbs";
            bar.setAttribute("aria-label", __("Breadcrumb")); navbar.prepend(bar);
        }
        const native = document.querySelector("#navbar-breadcrumbs");
        const hasNative = !!(native && native.children.length);
        if (bar.hidden !== hasNative) bar.hidden = hasNative;
        if (hasNative) return;
        const route = frappe.get_route() || [];
        const entries = [];
        if ((route[0] === "List" || route[0] === "Form") && route[1]) {
            const doctype = route[1];
            const meta = frappe.get_meta ? frappe.get_meta(doctype) : null;
            if (meta && meta.module) {
                const workspace = allowedWorkspaces().find(item => item.title === meta.module || item.name === meta.module || item.module === meta.module);
                if (workspace) entries.push({ text: __(workspace.title || workspace.name), href: workspaceLink(workspace).getAttribute("href") });
            }
            entries.push({ text: __(doctype), href: "/app/" + (frappe.router && frappe.router.slug ? frappe.router.slug(doctype) : doctype.toLowerCase().replace(/\s+/g, "-")) });
            if (route[0] === "Form" && route[2] && !(meta && meta.issingle)) entries.push({ text: route[2] });
        } else entries.push({ text: __("Home"), href: "/app" });
        const signature = JSON.stringify(entries);
        if (bar.dataset.signature === signature) return;
        bar.dataset.signature = signature; bar.replaceChildren();
        entries.forEach((entry, index) => {
            if (index) {
                const separator = document.createElement("span"); separator.className = "c4style-breadcrumb-separator";
                separator.setAttribute("aria-hidden", "true"); separator.textContent = "\u203a"; bar.appendChild(separator);
            }
            const current = index === entries.length - 1;
            const item = document.createElement(!current && entry.href ? "a" : "span");
            item.textContent = entry.text; item.title = entry.text;
            if (item.tagName === "A") item.href = entry.href;
            if (current) item.setAttribute("aria-current", "page");
            bar.appendChild(item);
        });
    }
    function measureHeader() {
        const header = document.querySelector(".navbar");
        const pageHead = Array.from(document.querySelectorAll(".page-head")).find(node => node.getClientRects().length);
        const theme = api.get_theme();
        const margin = theme.headerStyle === "pill" ? 24 : 0;
        const announcement = document.querySelector(".c4style-announcement");
        document.documentElement.style.setProperty("--c4style-header-offset", `${(header ? header.offsetHeight : 50) + margin + (announcement ? announcement.offsetHeight : 0)}px`);
        document.documentElement.style.setProperty("--c4style-page-head-height", `${pageHead ? pageHead.offsetHeight : 60}px`);
    }
    function closeNativeDrawer() {
        document.querySelectorAll(".dropdown-notifications, .dropdown-navbar-user").forEach(item => {
            if (!item.classList.contains("show") && !item.querySelector(".dropdown-menu.show")) return;
            const toggle = item.querySelector('[data-toggle="dropdown"], [data-bs-toggle="dropdown"]');
            if (toggle) toggle.click();
        });
    }
    function updateDrawerBackdrop() {
        const active = api.get_theme().nativeDrawers && document.querySelector(".dropdown-notifications.show, .dropdown-navbar-user.show, .dropdown-notifications > .dropdown-menu.show, .dropdown-navbar-user > .dropdown-menu.show");
        document.body.classList.toggle("c4style-drawer-open", !!active);
        const existing = document.querySelector(".c4style-drawer-backdrop");
        if (active && !existing) {
            const backdrop = document.createElement("div"); backdrop.className = "c4style-drawer-backdrop";
            backdrop.addEventListener("click", closeNativeDrawer); document.body.appendChild(backdrop);
        } else if (!active && existing) existing.remove();
    }
    function installNativeDrawers() {
        document.body.classList.toggle("c4style-native-drawers", !!api.get_theme().nativeDrawers);
        document.querySelectorAll(".dropdown-notifications, .dropdown-navbar-user").forEach(dropdown => {
            const menu = dropdown.querySelector(".dropdown-menu");
            if (!menu || observedDropdowns.has(menu)) return;
            observedDropdowns.add(menu);
            const header = document.createElement("div"); header.className = "c4style-native-drawer-header";
            const title = document.createElement("strong"); title.textContent = dropdown.matches(".dropdown-notifications") ? __("Notifications") : __("User menu");
            const close = button("Close", event => { event.preventDefault(); event.stopPropagation(); closeNativeDrawer(); }, "btn btn-default btn-sm");
            header.append(title, close); menu.prepend(header);
            new MutationObserver(updateDrawerBackdrop).observe(dropdown, { attributes: true, attributeFilter: ["class"], subtree: true });
        });
        updateDrawerBackdrop();
    }
    const groupStates = new WeakMap();
    function syncListGrouping() {
        const list = window.cur_list;
        const result = list && list.$result && list.$result[0];
        if (!result || !result.isConnected || !result.getClientRects().length || !Array.isArray(list.data)) return;
        let state = groupStates.get(result);
        if (!state) {
            const toolbar = document.createElement("div"); toolbar.className = "c4style-group-toolbar";
            const label = document.createElement("label"); label.textContent = __("Group loaded rows");
            const select = document.createElement("select"); select.className = "form-control"; select.setAttribute("aria-label", __("Group loaded rows"));
            select.add(new Option(__("No grouping"), ""));
            const usable = ["Data", "Link", "Select", "Check", "Int", "Float", "Currency", "Date", "Datetime"];
            const seen = new Set();
            (list.columns || []).forEach(column => {
                const field = column.df;
                if (field && field.fieldname && !seen.has(field.fieldname) && usable.includes(field.fieldtype)) {
                    seen.add(field.fieldname); select.add(new Option(__(field.label || field.fieldname), field.fieldname));
                }
            });
            if (!seen.size) return;
            const note = document.createElement("small"); note.textContent = __("Groups only the records currently loaded. Filters, sorting and permissions stay with Frappe.");
            label.appendChild(select); toolbar.append(label, note); result.before(toolbar);
            state = { field: "", rows: [], lastData: "", headers: [], toolbar };
            groupStates.set(result, state);
            select.addEventListener("change", () => { state.field = select.value; state.lastData = ""; syncListGrouping(); });
        }
        const rows = Array.from(result.querySelectorAll(".list-row-container"));
        const signature = JSON.stringify(list.data.map(doc => [doc.name, doc[state.field]]));
        const oldRows = new Set(state.rows);
        if (signature === state.lastData && rows.length === state.rows.length && rows.every(row => oldRows.has(row))) return;
        state.headers.forEach(header => header.remove()); state.headers = [];
        rows.forEach(row => { row.hidden = false; });
        const documents = new Map(list.data.map((doc, index) => [String(doc.name), { doc, index }]));
        const ordered = rows.map((row, index) => {
            const named = row.querySelector("[data-name]");
            return { row, record: documents.get(named && named.dataset.name) || { doc: list.data[index] || {}, index } };
        }).sort((a, b) => a.record.index - b.record.index);
        state.rows = rows; state.lastData = signature;
        if (!state.field) { ordered.forEach(({ row }) => result.appendChild(row)); return; }
        const groups = new Map();
        ordered.forEach(({ row, record }) => {
            const raw = record.doc[state.field]; const value = raw == null || raw === "" ? __("Not set") : String(raw);
            if (!groups.has(value)) groups.set(value, []);
            groups.get(value).push(row);
        });
        groups.forEach((members, name) => {
            const header = button(`${name} (${members.length})`, () => {
                const expanded = header.getAttribute("aria-expanded") === "true";
                header.setAttribute("aria-expanded", String(!expanded)); members.forEach(row => { row.hidden = expanded; });
            }, "c4style-list-group");
            header.setAttribute("aria-expanded", "true"); header.setAttribute("aria-label", `${name} (${members.length})`); state.headers.push(header); result.appendChild(header);
            members.forEach(row => result.appendChild(row));
        });
    }
    function syncTools() {
        if (!document.querySelector("[data-c4style-tools]")) {
            const trigger = button("\u25c8", openTools, "c4style-tools-trigger"); trigger.dataset.c4styleTools = "true";
            trigger.title = __("Appearance tools"); trigger.setAttribute("aria-label", __("Appearance tools")); trigger.setAttribute("aria-haspopup", "dialog");
            document.body.appendChild(trigger);
        }
        let scroll = document.querySelector(".c4style-scroll-controls");
        if (api.get_theme().showScrollButtons && !scroll) {
            scroll = document.createElement("div"); scroll.className = "c4style-scroll-controls";
            [true, false].forEach(top => {
                const control = button(top ? "\u2191" : "\u2193", () => window.scrollTo({ top: top ? 0 : document.documentElement.scrollHeight,
                    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" }), "btn btn-default btn-sm");
                const label = top ? __("Scroll to top") : __("Scroll to bottom"); control.title = label; control.setAttribute("aria-label", label);
                scroll.appendChild(control);
            });
            document.body.appendChild(scroll);
        } else if (!api.get_theme().showScrollButtons && scroll) scroll.remove();
        syncAnnouncement(); installNativeDrawers(); syncBreadcrumbs(); measureHeader(); syncListGrouping(); syncPinnedNotes();
    }
    api.sync_tools = syncTools;
    api.open_tools = openTools;
    api.open_launcher = openLauncher;
    function start() {
        syncTools();
        window.addEventListener("resize", () => { syncAnnouncement(); measureHeader(); });
        document.addEventListener("keydown", event => { if (event.key === "Escape") closeNativeDrawer(); });
        // Batch route-created navbar/menu work. Child mutations do not re-run synchronously.
        let queued = false;
        new MutationObserver(() => {
            if (queued) return;
            queued = true;
            requestAnimationFrame(() => { queued = false; syncTools(); });
        }).observe(document.body, { childList: true, subtree: true });
    }
    if (document.body) start(); else document.addEventListener("DOMContentLoaded", start, { once: true });
})();
