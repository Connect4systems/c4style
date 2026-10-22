const c4style_palettes = {
    C4Style: ["#714B67", "#017E84", "#E5E8EB", "#FFFFFF", "#36414C", "#E5F1F1"],
    Ocean: ["#155E75", "#0284C7", "#EAF2F8", "#153747", "#F0F9FF", "#24566B"],
    Forest: ["#365C46", "#4F8A62", "#EEF3EE", "#203D2D", "#F0FDF4", "#365C46"],
    Sunset: ["#8B4A3C", "#D47A45", "#F7F0E8", "#4A2D28", "#FFF7ED", "#75483C"],
    "Lime Fresh": ["#3F6212", "#65A30D", "#F2F8EC", "#365314", "#F7FEE7", "#4D7C0F"],
    Wine: ["#831843", "#BE185D", "#FFF1F5", "#701A3D", "#FFF1F5", "#9D2854"],
};
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
        <h4></h4><div class="c4style-preview-table"></div><p></p><button type="button" class="btn"></button>
        </div></div>`;
    const hex = (field, fallback) => /^#[0-9a-f]{6}$/i.test(frm.doc[field] || "") ? frm.doc[field] : fallback;
    const header = panel.querySelector(".c4style-preview-header");
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
    const button = card.querySelector("button");
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
        const colors = c4style_palettes[frm.doc.palette];
        if (!colors) return;
        const fields = ["primary", "accent", "background", "menu_background", "menu_text", "menu_active"];
        return frm.set_value({
            ...Object.fromEntries(fields.map((field, index) => [field, colors[index]])),
            navbar_background: colors[0], navbar_text: "#FFFFFF", panel_background: "#FFFFFF",
            table_header_background: colors[0], table_header_text: "#FFFFFF",
        });
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
 "table_header_text", "brand_name", "font_family", "text_direction", "font_size", "radius"]
    .forEach(field => { c4style_form_events[field] = c4style_preview; });
frappe.ui.form.on("Style Settings", c4style_form_events);
