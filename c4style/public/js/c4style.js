(() => {
    "use strict";
    const palettes = { ...((frappe.boot && frappe.boot.c4style && frappe.boot.c4style.palettes) || {}) };
    let boot = (frappe.boot && frappe.boot.c4style) || {};
    let siteTheme = boot.site || {};
    let theme = siteTheme;
    let personal = { menuCollapsed: theme.menuDefaultCollapsed !== false, workspaceWide: false, direction: "auto", notes: [], ...(boot.personal || {}) };
    const originalDirection = document.documentElement.getAttribute("dir") || "ltr";
    const color = value => typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value);

    function replacePalettes(values) {
        Object.keys(palettes).forEach(name => delete palettes[name]);
        Object.assign(palettes, values);
    }
    function refreshPalettes(callback) {
        frappe.call({ method: "c4style.settings.get_palettes", callback: response => {
            replacePalettes(response.message || {});
            applyTheme(siteTheme);
            if (callback) callback();
        }});
    }

    function applyTheme(values) {
        siteTheme = { ...siteTheme, ...values };
        const palette = siteTheme.allowUserThemes && palettes[personal.themePalette];
        const overrides = palette ? Object.fromEntries(Object.entries(paletteFields).map(([key, field]) => [key, palette[field]])) : {};
        theme = { ...siteTheme, ...overrides };
        const root = document.documentElement;
        const variables = {
            primary: ["--primary", "--btn-primary"],
            navbarBackground: ["--navbar-bg"], navbarText: ["--c4style-navbar-text"],
            panelBackground: ["--c4style-panel-bg"],
            tableHeaderBackground: ["--c4style-table-header-bg"], tableHeaderText: ["--c4style-table-header-text"],
            accent: ["--secondary"], background: ["--bg-color"],
            menuBackground: ["--c4style-menu-bg"], menuText: ["--c4style-menu-text"],
            menuActive: ["--c4style-menu-active"],
            secondaryBackground: ["--c4style-secondary-bg"], secondaryText: ["--c4style-secondary-text"],
            rowHoverBackground: ["--c4style-row-hover"], rowBorder: ["--c4style-row-border"],
            inputBackground: ["--c4style-input-bg"], inputBorder: ["--c4style-input-border"],
            announcementBackground: ["--c4style-announcement-bg"], announcementColor: ["--c4style-announcement-text"],
        };
        Object.entries(variables).forEach(([key, names]) => {
            if (color(theme[key])) names.forEach(name => root.style.setProperty(name, theme[key]));
        });
        if (color(theme.accent)) {
            root.style.setProperty("--btn-secondary", theme.accent + "80");
            root.style.setProperty("--sidebar-select-color", theme.accent + "20");
        }
        if (color(theme.primary)) root.style.setProperty("--table-border-color", theme.primary + "40");
        if (Number.isFinite(theme.fontSize) && theme.fontSize >= 12 && theme.fontSize <= 18) {
            root.style.setProperty("--c4style-font-size", theme.fontSize + "px");
            root.style.setProperty("--text-base", theme.fontSize + "px");
        }
        if (Number.isFinite(theme.radius) && theme.radius >= 2 && theme.radius <= 16)
            root.style.setProperty("--c4style-radius", theme.radius + "px");
        const fonts = { system: 'system-ui, -apple-system, "Segoe UI", sans-serif', arial: 'Arial, sans-serif', tahoma: 'Tahoma, sans-serif', georgia: 'Georgia, serif' };
        root.style.setProperty("--c4style-font-family", fonts[theme.fontFamily] || fonts.system);
        root.style.setProperty("--font-stack", fonts[theme.fontFamily] || fonts.system);
        document.body.classList.toggle("c4style-compact", theme.density === "compact");
        ["headerStyle", "rowStyle", "inputBorderStyle", "fieldStyle", "buttonStyle", "shadowStyle", "menuBehavior"].forEach(key => {
            const supported = {
                headerStyle: ["pill", "flat"], rowStyle: ["separated", "flat"], inputBorderStyle: ["dashed", "solid", "none"],
                fieldStyle: ["boxed", "underline"], buttonStyle: ["filled", "outline"], shadowStyle: ["soft", "none"], menuBehavior: ["hover", "click"],
            };
            if (supported[key].includes(theme[key])) document.body.dataset[key] = theme[key];
        });
        applyPersonal();
        syncNavigation();
        refreshMenus();
        if (frappe.c4style.sync_tools) frappe.c4style.sync_tools();
    }

    function applyPersonal() {
        document.body.classList.toggle("c4style-menu-collapsed", personal.menuCollapsed);
        document.body.classList.toggle("c4style-workspace-wide", personal.workspaceWide);
        const siteDirection = theme.textDirection === "rtl" || theme.textDirection === "ltr" ? theme.textDirection : originalDirection;
        document.documentElement.setAttribute("dir", personal.direction === "auto" ? siteDirection : personal.direction);
    }

    let savingPersonal = false;
    function savePersonal(key, value, onSaved) {
        if (savingPersonal) return;
        savingPersonal = true;
        const previous = personal[key];
        personal[key] = value;
        if (key === "themePalette") applyTheme({});
        else applyPersonal();
        refreshMenus();
        document.querySelectorAll("[data-c4style-menu-controls] button, [data-c4style-personal-action]").forEach(item => { item.disabled = true; });
        frappe.call({
            method: "c4style.settings.save_settings", args: { settings: JSON.stringify({ [key]: value }) },
            callback: () => {
                if (frappe.c4style.sync_tools) frappe.c4style.sync_tools();
                if (typeof onSaved === "function") onSaved();
                frappe.show_alert({ message: key === "notes" ? __("Notes saved") : __("Layout preference saved"), indicator: "green" });
            },
            error: () => {
                personal[key] = previous;
                if (key === "themePalette") applyTheme({});
                else applyPersonal();
                refreshMenus();
                if (frappe.c4style.sync_tools) frappe.c4style.sync_tools();
            },
            always: () => { savingPersonal = false; document.querySelectorAll("[data-c4style-menu-controls] button, [data-c4style-personal-action]").forEach(item => { item.disabled = false; }); },
        });
    }

    function refreshMenus() {
        document.querySelectorAll(".desk-sidebar").forEach(sidebar => {
            const section = sidebar.closest(".layout-side-section");
            if (section) section.classList.add("c4style-menu-section");
            if (document.body.classList.contains("c4style-has-app-menu") && !sidebar.closest(".c4style-app-menu")) {
                const controls = sidebar.querySelector("[data-c4style-menu-controls]");
                if (controls) controls.remove();
                return;
            }
            if (!sidebar.querySelector("[data-c4style-menu-controls]")) {
                const controls = document.createElement("div");
                controls.dataset.c4styleMenuControls = "true";
                controls.className = "c4style-menu-controls";
                ["menuCollapsed", "workspaceWide"].forEach(key => {
                    const button = document.createElement("button");
                    button.type = "button";
                    button.className = "btn btn-default btn-sm";
                    button.dataset.c4styleToggle = key;
                    button.addEventListener("click", () => savePersonal(key, !personal[key]));
                    controls.appendChild(button);
                });
                const direction = document.createElement("button");
                direction.type = "button";
                direction.className = "btn btn-default btn-sm";
                direction.dataset.c4styleDirection = "true";
                direction.addEventListener("click", () => savePersonal("direction", document.documentElement.dir === "rtl" ? "ltr" : "rtl"));
                controls.appendChild(direction);
                sidebar.prepend(controls);
            }
            sidebar.querySelectorAll(".item-anchor").forEach(anchor => {
                const label = anchor.querySelector(".sidebar-item-label");
                if (label && !anchor.title) anchor.title = label.textContent.trim();
                if (label && !anchor.getAttribute("aria-label")) anchor.setAttribute("aria-label", label.textContent.trim());
            });
        });
        document.querySelectorAll("[data-c4style-direction]").forEach(button => {
            const rtl = document.documentElement.dir === "rtl";
            button.textContent !== (rtl ? "LTR" : "RTL") && (button.textContent = rtl ? "LTR" : "RTL");
            const label = rtl ? __("Switch to left-to-right") : __("Switch to right-to-left");
            button.title = label;
            button.setAttribute("aria-label", label);
        });
        document.querySelectorAll("[data-c4style-toggle]").forEach(button => {
            const menu = button.dataset.c4styleToggle === "menuCollapsed";
            const active = personal[button.dataset.c4styleToggle];
            const label = menu ? (active ? __("Expand menu") : __("Narrow menu"))
                : (active ? __("Narrow workspace") : __("Expand workspace"));
            const rtl = document.documentElement.dir === "rtl";
            const right = menu ? active !== rtl : active === rtl;
            const text = (right ? "\u2192" : "\u2190") + (personal.menuCollapsed ? "" : " " + label);
            if (button.textContent !== text) button.textContent = text;
            button.title = label;
            button.setAttribute("aria-label", label);
            button.setAttribute("aria-pressed", String(active));
        });
    }

    function syncNavigation() {
        const workspaces = (frappe.boot && frappe.boot.allowed_workspaces) || [];
        const existing = document.querySelector(".c4style-app-menu");
        if (!workspaces.length) {
            if (existing) existing.remove();
            document.body.classList.remove("c4style-has-app-menu");
            return;
        }
        if (existing) {
            existing.querySelector(".c4style-brand-label").textContent = theme.brandName || "C4Style";
            return;
        }
        const nav = document.createElement("aside");
        nav.className = "c4style-app-menu";
        nav.setAttribute("aria-label", __("Workspace navigation"));
        const brand = document.createElement("a");
        brand.className = "c4style-brand";
        brand.href = "/app";
        brand.title = __("Apps and workspaces");
        brand.setAttribute("aria-label", __("Apps and workspaces"));
        brand.addEventListener("click", event => {
            if (!event.ctrlKey && !event.metaKey && !event.shiftKey && frappe.c4style.open_launcher) {
                event.preventDefault(); frappe.c4style.open_launcher();
            }
        });
        const mark = document.createElement("span");
        mark.className = "c4style-brand-mark";
        mark.textContent = "C4";
        const logo = frappe.boot.app_logo_url;
        if (typeof logo === "string" && (/^\/(?!\/)/.test(logo) || /^https:\/\//i.test(logo))) {
            const img = document.createElement("img");
            img.src = logo; img.alt = "";
            mark.replaceChildren(img);
        }
        const name = document.createElement("span");
        name.className = "c4style-brand-label";
        name.textContent = theme.brandName || "C4Style";
        brand.append(mark, name);
        const menu = document.createElement("div");
        menu.className = "desk-sidebar";
        const links = document.createElement("nav");
        links.setAttribute("aria-label", __("Workspaces"));
        menu.appendChild(links);
        nav.append(brand, menu);
        const visible = workspaces.filter(item => !item.is_hidden);
        const nodes = new Map();
        visible.forEach(item => {
            const title = item.title || item.name;
            if (!title) return;
            const row = document.createElement("div");
            row.className = "desk-sidebar-item standard-sidebar-item";
            const anchor = document.createElement("a");
            anchor.className = "item-anchor";
            const slug = frappe.router && frappe.router.slug ? frappe.router.slug(title) : title.toLowerCase().replace(/\s+/g, "-");
            anchor.href = "/app/" + (item.public ? "" : "private/") + encodeURIComponent(slug);
            anchor.dataset.workspace = title;
            anchor.title = __(title);
            anchor.setAttribute("aria-label", __(title));
            const icon = document.createElement("span");
            icon.className = "sidebar-item-icon";
            if (frappe.utils && frappe.utils.icon) {
                const iconName = /^[a-z0-9-]+$/i.test(item.icon || "") ? item.icon : "folder-normal";
                icon.innerHTML = frappe.utils.icon(iconName, "md");
            } else icon.textContent = title.slice(0, 1).toUpperCase();
            const label = document.createElement("span");
            label.className = "sidebar-item-label";
            label.textContent = __(title);
            anchor.append(icon, label);
            row.appendChild(anchor);
            nodes.set(item.name || title, { row, item });
        });
        const hasChildren = key => visible.some(item => item.parent_page === key);
        nodes.forEach(({ row, item }, key) => {
            let node = row;
            if (hasChildren(key)) {
                const group = document.createElement("details");
                group.className = "c4style-nav-group";
                group.open = true;
                const summary = document.createElement("summary");
                summary.appendChild(row);
                group.appendChild(summary);
                node = group;
            }
            nodes.get(key).node = node;
        });
        nodes.forEach(({ node, item }) => {
            const parent = nodes.get(item.parent_page);
            // Bad workspace trees must not prevent Desk from rendering.
            const seen = new Set([item.name || item.title]);
            let ancestor = parent;
            let cyclic = false;
            while (ancestor) {
                const key = ancestor.item.name || ancestor.item.title;
                if (seen.has(key)) { cyclic = true; break; }
                seen.add(key);
                ancestor = nodes.get(ancestor.item.parent_page);
            }
            if (!cyclic && parent && parent.node.tagName === "DETAILS") parent.node.appendChild(node);
            else links.appendChild(node);
        });
        document.body.prepend(nav);
        document.body.classList.add("c4style-has-app-menu");
        links.addEventListener("click", event => {
            const anchor = event.target.closest("a[data-workspace]");
            if (anchor) markActiveWorkspace(anchor.pathname);
        });
        markActiveWorkspace(window.location.pathname);
    }

    function markActiveWorkspace(path) {
        document.querySelectorAll(".c4style-app-menu a[data-workspace]").forEach(anchor => {
            const active = decodeURI(anchor.pathname) === decodeURI(path);
            anchor.closest(".standard-sidebar-item").classList.toggle("selected", active);
            if (active) anchor.setAttribute("aria-current", "page");
            else anchor.removeAttribute("aria-current");
        });
    }

    const paletteFields = {
        primary: "primary", accent: "accent", background: "background", menuBackground: "menu_background", menuText: "menu_text", menuActive: "menu_active",
        navbarBackground: "navbar_background", navbarText: "navbar_text", panelBackground: "panel_background", tableHeaderBackground: "table_header_background", tableHeaderText: "table_header_text",
        secondaryBackground: "secondary_background", secondaryText: "secondary_text", rowHoverBackground: "row_hover_background", rowBorder: "row_border", inputBackground: "input_background", inputBorder: "input_border",
        announcementBackground: "announcement_background", announcementColor: "announcement_color",
    };
    frappe.c4style = {
        apply_theme: applyTheme, palettes, refresh_palettes: refreshPalettes,
        palette_settings: name => Object.fromEntries(Object.entries(paletteFields).map(([key, field]) => [key, palettes[name][field]])),
        get_theme: () => ({ ...theme }), get_site_theme: () => ({ ...siteTheme }),
        get_personal: () => ({ ...personal }), save_personal: savePersonal,
    };
    // Keep bookmarks working while the native Single DocType enforces permissions.
    frappe.standard_pages = frappe.standard_pages || {};
    frappe.standard_pages["c4style-settings"] = () => {
        const wrapper = frappe.container.add_page("c4style-settings");
        wrapper.page_name = "c4style-settings";
        frappe.ui.make_app_page({ parent: wrapper, title: __("Style Settings"), single_column: true });
        frappe.set_route("Form", "Style Settings");
    };
    try { localStorage.removeItem("_page:c4style-settings"); } catch (error) { /* Storage is optional. */ }
    function loadBootTheme() {
        const current = frappe.boot && frappe.boot.c4style;
        if (current && current !== boot) {
            boot = current;
            replacePalettes(current.palettes || {});
            siteTheme = { ...current.site };
            personal = { menuCollapsed: siteTheme.menuDefaultCollapsed !== false, workspaceWide: false,
                direction: "auto", notes: [], ...(current.personal || {}) };
        }
        applyTheme(siteTheme);
    }
    let refreshingSettings = false;
    let settingsListenerInstalled = false;
    function refreshSiteSettings() {
        if (refreshingSettings || !frappe.boot?.c4style || !frappe.call) return;
        refreshingSettings = true;
        frappe.call({
            method: "c4style.settings.get_settings",
            callback: response => {
                if (response.message) applyTheme(response.message);
            },
            always: () => { refreshingSettings = false; },
        });
    }
    function installSettingsListener() {
        if (!settingsListenerInstalled && frappe.realtime?.on) {
            frappe.realtime.on("c4style_settings_changed", refreshSiteSettings);
            settingsListenerInstalled = true;
        }
    }
    function start() {
        document.querySelectorAll("[data-c4style-settings-link]").forEach(link => link.remove());
        loadBootTheme();
        applyPersonal();
        refreshMenus();
        installSettingsListener();
        // Refresh stale boot settings and recover when websocket delivery is unavailable.
        refreshSiteSettings();
        window.addEventListener("focus", refreshSiteSettings);
        document.addEventListener("visibilitychange", () => {
            if (!document.hidden) refreshSiteSettings();
        });
        window.setInterval(() => {
            installSettingsListener();
            if (!document.hidden) refreshSiteSettings();
        }, 30000);
        if (window.jQuery) window.jQuery(document).on("app_ready.c4style", loadBootTheme);
        new MutationObserver(refreshMenus).observe(document.body, { childList: true, subtree: true });
        if (frappe.router && frappe.router.on) frappe.router.on("change", () => {
            syncNavigation();
            refreshMenus();
            markActiveWorkspace(window.location.pathname);
            if (frappe.c4style.sync_tools) frappe.c4style.sync_tools();
        });
    }
    if (document.body) start();
    else document.addEventListener("DOMContentLoaded", start, { once: true });
})();
