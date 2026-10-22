const c4style_palettes = frappe.c4style.palettes;
function c4style_preview(frm) {
    const field = frm.fields_dict && frm.fields_dict.theme_preview;
    if (!field) return;
    const panel = document.createElement("div");
    panel.className = "c4style-theme-preview";
    const fonts = { system: "system-ui, sans-serif", arial: "Arial, sans-serif", tahoma: "Tahoma, sans-serif", georgia: "Georgia, serif" };
    panel.style.fontFamily = fonts[frm.doc.font_family] || fonts.system;
    if (frm.doc.font_size >= 12 && frm.doc.font_size <= 18) panel.style.fontSize = frm.doc.font_size + "px";
    if (frm.doc.radius >= 2 && frm.doc.radius <= 16) panel.style.borderRadius = frm.doc.radius + "px";
    panel.innerHTML = `<div class="c4style-preview-header"></div><div class="c4style-preview-body">
        <div class="c4style-preview-menu"></div><div class="c4style-preview-card">
        <h4></h4><div class="c4style-preview-filters"><input class="form-control" disabled value="Item name" aria-label="Preview item filter"><button type="button" class="btn btn-default">Filter</button></div>
        <div class="c4style-preview-table"></div><div class="c4style-preview-row">4700 BC INSTANT P <span>Enabled</span></div>
        <div class="c4style-preview-row">FORTUNE KACHI GH <span>Enabled</span></div><p></p><button type="button" class="btn c4style-preview-primary"></button>
        </div></div>`;
    const hex = (field, fallback) => /^#[0-9a-f]{6}$/i.test(frm.doc[field] || "") ? frm.doc[field] : fallback;
    const localColors = { secondary_background: "--c4style-secondary-bg", secondary_text: "--c4style-secondary-text", input_background: "--c4style-input-bg", input_border: "--c4style-input-border", row_border: "--c4style-row-border", row_hover_background: "--c4style-row-hover" };
    Object.entries(localColors).forEach(([field, variable]) => { if (/^#[0-9a-f]{6}$/i.test(frm.doc[field] || "")) panel.style.setProperty(variable, frm.doc[field]); });
    const input = panel.querySelector("input");
    input.style.setProperty("border-style", ["solid", "dashed", "none"].includes(frm.doc.input_border_style) ? frm.doc.input_border_style : "dashed", "important");
    const header = panel.querySelector(".c4style-preview-header");
    if (frm.doc.header_style === "pill") { header.style.margin = "12px"; header.style.borderRadius = "999px"; }
    header.textContent = frm.doc.brand_name || "C4Style";
    header.style.background = hex("navbar_background", "#714B67");
    header.style.color = hex("navbar_text", "#FFFFFF");
    const menu = panel.querySelector(".c4style-preview-menu");
    menu.textContent = __("Home") + " / " + __("Accounting") + " / " + __("Stock");
    menu.style.background = hex("menu_background", "#FFFFFF");
    menu.style.color = hex("menu_text", "#36414C");
    panel.querySelector(".c4style-preview-body").style.background = hex("background", "#E5E8EB");
    const card = panel.querySelector(".c4style-preview-card");
    card.style.background = hex("panel_background", "#FFFFFF");
    card.querySelector("h4").textContent = __("Workspace preview");
    const table = card.querySelector(".c4style-preview-table");
    table.textContent = __("Name") + "                         " + __("Status");
    table.style.background = hex("table_header_background", "#714B67");
    table.style.color = hex("table_header_text", "#FFFFFF");
    card.querySelector("p").textContent = __("Your site colors, menu and table headers in one theme.");
    const button = card.querySelector(".c4style-preview-primary");
    button.textContent = __("Primary action");
    button.style.setProperty("background", hex("primary", "#714B67"), "important");
    button.style.color = "white";
    panel.dir = frm.doc.text_direction === "auto" ? document.documentElement.dir : frm.doc.text_direction;
    field.$wrapper.empty().append(panel);
}
const c4style_form_events = {
    refresh(frm) {
        frm.set_intro(__("Choose a palette, then customize its colors and typography. Save to apply it to everyone. Each user controls their own menu and workspace width."));
        c4style_preview(frm);
    },
    palette(frm) {
        const values = c4style_palettes[frm.doc.palette];
        if (values) return frm.set_value(values);
    },
    after_save(frm) {
        frappe.call({ method: "c4style.settings.get_settings", callback: response => {
            frappe.c4style.apply_theme(response.message);
            frappe.show_alert({ message: __("Site style saved"), indicator: "green" });
        }});
    },
};
["primary", "accent", "background", "menu_background", "menu_text", "menu_active",
 "navbar_background", "navbar_text", "panel_background", "table_header_background",
 "table_header_text", "brand_name", "font_family", "text_direction", "font_size", "radius",
 "secondary_background", "secondary_text", "input_background", "input_border", "input_border_style",
 "header_style", "row_style", "row_border", "row_hover_background", "button_style", "field_style", "shadow_style"]
    .forEach(field => { c4style_form_events[field] = c4style_preview; });
frappe.ui.form.on("Style Settings", c4style_form_events);
