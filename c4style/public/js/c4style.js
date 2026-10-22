(() => {
    "use strict";
    const boot = (frappe.boot && frappe.boot.c4style) || {};
    let theme = boot.site || {};
    let personal = { menuCollapsed: false, workspaceWide: false, direction: "auto", ...(boot.personal || {}) };
    const originalDirection = document.documentElement.getAttribute("dir") || "ltr";
    const color = value => typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value);

    function applyTheme(values) {
        theme = { ...theme, ...values };
        const root = document.documentElement;
        const variables = {
            primary: ["--primary", "--btn-primary", "--navbar-bg"],
            accent: ["--secondary"], background: ["--bg-color"],
            menuBackground: ["--c4style-menu-bg"], menuText: ["--c4style-menu-text"],
            menuActive: ["--c4style-menu-active"],
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
        document.body.classList.toggle("c4style-compact", theme.density === "compact");
    }

    function applyPersonal() {
        document.body.classList.toggle("c4style-menu-collapsed", personal.menuCollapsed);
        document.body.classList.toggle("c4style-workspace-wide", personal.workspaceWide);
        document.documentElement.setAttribute("dir", personal.direction === "auto" ? originalDirection : personal.direction);
    }

    function savePersonal(key, value) {
        const previous = personal[key];
        personal[key] = value;
        applyPersonal();
        refreshMenus();
        document.querySelectorAll("[data-c4style-menu-controls] button").forEach(item => { item.disabled = true; });
        frappe.call({
            method: "c4style.settings.save_settings", args: { settings: JSON.stringify({ [key]: value }) },
            callback: () => frappe.show_alert({ message: __("Layout preference saved"), indicator: "green" }),
            error: () => { personal[key] = previous; applyPersonal(); refreshMenus(); },
            always: () => document.querySelectorAll("[data-c4style-menu-controls] button").forEach(item => { item.disabled = false; }),
        });
    }

    function refreshMenus() {
        document.querySelectorAll(".desk-sidebar").forEach(sidebar => {
            const section = sidebar.closest(".layout-side-section");
            if (section) section.classList.add("c4style-menu-section");
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
                sidebar.prepend(controls);
            }
            sidebar.querySelectorAll(".item-anchor").forEach(anchor => {
                const label = anchor.querySelector(".sidebar-item-label");
                if (label && !anchor.title) anchor.title = label.textContent.trim();
                if (label && !anchor.getAttribute("aria-label")) anchor.setAttribute("aria-label", label.textContent.trim());
            });
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

    frappe.c4style = { apply_theme: applyTheme };
    // Keep bookmarks working while the native Single DocType enforces permissions.
    frappe.standard_pages = frappe.standard_pages || {};
    frappe.standard_pages["c4style-settings"] = () => {
        const wrapper = frappe.container.add_page("c4style-settings");
        wrapper.page_name = "c4style-settings";
        frappe.ui.make_app_page({ parent: wrapper, title: __("Style Settings"), single_column: true });
        frappe.set_route("Form", "Style Settings");
    };
    try { localStorage.removeItem("_page:c4style-settings"); } catch (error) { /* Storage is optional. */ }
    function start() {
        document.querySelectorAll("[data-c4style-settings-link]").forEach(link => link.remove());
        applyTheme(theme);
        applyPersonal();
        refreshMenus();
        new MutationObserver(refreshMenus).observe(document.body, { childList: true, subtree: true });
    }
    if (document.body) start();
    else document.addEventListener("DOMContentLoaded", start, { once: true });
})();
