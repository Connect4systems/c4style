(() => {
    "use strict";
    const palettes = {
    "C4Style": {
        "primary": "#714B67",
        "accent": "#017E84",
        "background": "#E5E8EB",
        "menu_background": "#FFFFFF",
        "menu_text": "#36414C",
        "menu_active": "#E5F1F1",
        "navbar_background": "#714B67",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#714B67",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#E5E8EB",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#E5E8EB",
        "announcement_color": "#714B67"
    },
    "Ocean": {
        "primary": "#155E75",
        "accent": "#0284C7",
        "background": "#EAF2F8",
        "menu_background": "#153747",
        "menu_text": "#F0F9FF",
        "menu_active": "#24566B",
        "navbar_background": "#155E75",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#155E75",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#EAF2F8",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#EAF2F8",
        "announcement_color": "#155E75"
    },
    "Forest": {
        "primary": "#365C46",
        "accent": "#4F8A62",
        "background": "#EEF3EE",
        "menu_background": "#203D2D",
        "menu_text": "#F0FDF4",
        "menu_active": "#365C46",
        "navbar_background": "#365C46",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#365C46",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#EEF3EE",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#EEF3EE",
        "announcement_color": "#365C46"
    },
    "Sunset": {
        "primary": "#8B4A3C",
        "accent": "#D47A45",
        "background": "#F7F0E8",
        "menu_background": "#4A2D28",
        "menu_text": "#FFF7ED",
        "menu_active": "#75483C",
        "navbar_background": "#8B4A3C",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#8B4A3C",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#F7F0E8",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#F7F0E8",
        "announcement_color": "#8B4A3C"
    },
    "Lime Fresh": {
        "primary": "#3F6212",
        "accent": "#65A30D",
        "background": "#F2F8EC",
        "menu_background": "#365314",
        "menu_text": "#F7FEE7",
        "menu_active": "#4D7C0F",
        "navbar_background": "#3F6212",
        "navbar_text": "#FFFFFF",
        "panel_background": "#F9FCF7",
        "table_header_background": "#3F6212",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#F2F8EC",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#F2F8EC",
        "announcement_color": "#3F6212"
    },
    "Wine": {
        "primary": "#831843",
        "accent": "#BE185D",
        "background": "#FFF1F5",
        "menu_background": "#701A3D",
        "menu_text": "#FFF1F5",
        "menu_active": "#9D2854",
        "navbar_background": "#831843",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#831843",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#FFF1F5",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#FFF1F5",
        "announcement_color": "#831843"
    },
    "Crimson Red": {
        "primary": "#9F1239",
        "accent": "#E11D48",
        "background": "#FFF1F2",
        "menu_background": "#881337",
        "menu_text": "#FFF1F2",
        "menu_active": "#BE123C",
        "navbar_background": "#9F1239",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#9F1239",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#FFF1F2",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#FFF1F2",
        "announcement_color": "#9F1239"
    },
    "Ocean Teal": {
        "primary": "#115E59",
        "accent": "#0D9488",
        "background": "#F0FDFA",
        "menu_background": "#134E4A",
        "menu_text": "#F0FDFA",
        "menu_active": "#0F766E",
        "navbar_background": "#115E59",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#115E59",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#F0FDFA",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#F0FDFA",
        "announcement_color": "#115E59"
    },
    "Burnt Orange": {
        "primary": "#9A3412",
        "accent": "#EA580C",
        "background": "#FFF7ED",
        "menu_background": "#7C2D12",
        "menu_text": "#FFF7ED",
        "menu_active": "#C2410C",
        "navbar_background": "#9A3412",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#9A3412",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#FFF7ED",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#FFF7ED",
        "announcement_color": "#9A3412"
    },
    "Indigo Night": {
        "primary": "#3730A3",
        "accent": "#6366F1",
        "background": "#EEF2FF",
        "menu_background": "#312E81",
        "menu_text": "#EEF2FF",
        "menu_active": "#4338CA",
        "navbar_background": "#3730A3",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#3730A3",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#EEF2FF",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#EEF2FF",
        "announcement_color": "#3730A3"
    },
    "Dark Green": {
        "primary": "#14532D",
        "accent": "#16A34A",
        "background": "#F0FDF4",
        "menu_background": "#14532D",
        "menu_text": "#F0FDF4",
        "menu_active": "#166534",
        "navbar_background": "#14532D",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#14532D",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#F0FDF4",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#F0FDF4",
        "announcement_color": "#14532D"
    },
    "Royal Purple": {
        "primary": "#6B21A8",
        "accent": "#A855F7",
        "background": "#FAF5FF",
        "menu_background": "#581C87",
        "menu_text": "#FAF5FF",
        "menu_active": "#7E22CE",
        "navbar_background": "#6B21A8",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#6B21A8",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#FAF5FF",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#FAF5FF",
        "announcement_color": "#6B21A8"
    },
    "Jet Black": {
        "primary": "#27272A",
        "accent": "#71717A",
        "background": "#F4F4F5",
        "menu_background": "#18181B",
        "menu_text": "#FAFAFA",
        "menu_active": "#3F3F46",
        "navbar_background": "#27272A",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#27272A",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#F4F4F5",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#F4F4F5",
        "announcement_color": "#27272A"
    },
    "Sky Blue": {
        "primary": "#0369A1",
        "accent": "#0EA5E9",
        "background": "#F0F9FF",
        "menu_background": "#075985",
        "menu_text": "#F0F9FF",
        "menu_active": "#0284C7",
        "navbar_background": "#0369A1",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#0369A1",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#F0F9FF",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#F0F9FF",
        "announcement_color": "#0369A1"
    },
    "Charcoal Grey": {
        "primary": "#374151",
        "accent": "#6B7280",
        "background": "#F3F4F6",
        "menu_background": "#1F2937",
        "menu_text": "#F9FAFB",
        "menu_active": "#4B5563",
        "navbar_background": "#374151",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#374151",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#F3F4F6",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#F3F4F6",
        "announcement_color": "#374151"
    },
    "Coffee Brown": {
        "primary": "#713F12",
        "accent": "#A16207",
        "background": "#FAF6F0",
        "menu_background": "#5C3317",
        "menu_text": "#FFFBEB",
        "menu_active": "#854D0E",
        "navbar_background": "#713F12",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#713F12",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#FAF6F0",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#FAF6F0",
        "announcement_color": "#713F12"
    },
    "Rose Pink": {
        "primary": "#9D174D",
        "accent": "#EC4899",
        "background": "#FDF2F8",
        "menu_background": "#831843",
        "menu_text": "#FDF2F8",
        "menu_active": "#BE185D",
        "navbar_background": "#9D174D",
        "navbar_text": "#FFFFFF",
        "panel_background": "#FFFFFF",
        "table_header_background": "#9D174D",
        "table_header_text": "#FFFFFF",
        "secondary_background": "#A58F7A",
        "secondary_text": "#FFFFFF",
        "row_hover_background": "#FDF2F8",
        "row_border": "#CAD3C4",
        "input_background": "#FFFFFF",
        "input_border": "#A9B49F",
        "announcement_background": "#FDF2F8",
        "announcement_color": "#9D174D"
    }
};
    let boot = (frappe.boot && frappe.boot.c4style) || {};
    let theme = boot.site || {};
    let personal = { menuCollapsed: theme.menuDefaultCollapsed !== false, workspaceWide: false, direction: "auto", notes: [], ...(boot.personal || {}) };
    const originalDirection = document.documentElement.getAttribute("dir") || "ltr";
    const color = value => typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value);

    function applyTheme(values) {
        theme = { ...theme, ...values };
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
    function savePersonal(key, value) {
        if (savingPersonal) return;
        savingPersonal = true;
        const previous = personal[key];
        personal[key] = value;
        applyPersonal();
        refreshMenus();
        document.querySelectorAll("[data-c4style-menu-controls] button, [data-c4style-personal-action]").forEach(item => { item.disabled = true; });
        frappe.call({
            method: "c4style.settings.save_settings", args: { settings: JSON.stringify({ [key]: value }) },
            callback: () => {
                if (frappe.c4style.sync_tools) frappe.c4style.sync_tools();
                frappe.show_alert({ message: key === "notes" ? __("Notes saved") : __("Layout preference saved"), indicator: "green" });
            },
            error: () => { personal[key] = previous; applyPersonal(); refreshMenus(); },
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
        apply_theme: applyTheme, palettes,
        palette_settings: name => Object.fromEntries(Object.entries(paletteFields).map(([key, field]) => [key, palettes[name][field]])),
        get_theme: () => ({ ...theme }), get_personal: () => ({ ...personal }), save_personal: savePersonal,
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
            theme = { ...current.site };
            personal = { menuCollapsed: theme.menuDefaultCollapsed !== false, workspaceWide: false,
                direction: "auto", notes: [], ...(current.personal || {}) };
        }
        applyTheme(theme);
    }
    function start() {
        document.querySelectorAll("[data-c4style-settings-link]").forEach(link => link.remove());
        loadBootTheme();
        applyPersonal();
        refreshMenus();
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
