const c4style_palettes = {
    C4Style: ["#714B67", "#017E84", "#E5E8EB", "#FFFFFF", "#36414C", "#E5F1F1"],
    Ocean: ["#155E75", "#0284C7", "#EAF2F8", "#153747", "#F0F9FF", "#24566B"],
    Forest: ["#365C46", "#4F8A62", "#EEF3EE", "#203D2D", "#F0FDF4", "#365C46"],
    Sunset: ["#8B4A3C", "#D47A45", "#F7F0E8", "#4A2D28", "#FFF7ED", "#75483C"],
};
frappe.ui.form.on("Style Settings", {
    refresh(frm) {
        frm.set_intro(__("Site and menu styling applies to all users after saving and reloading. Each user can expand or narrow their menu using the arrow in the workspace sidebar."));
    },
    palette(frm) {
        const colors = c4style_palettes[frm.doc.palette];
        if (!colors) return;
        const fields = ["primary", "accent", "background", "menu_background", "menu_text", "menu_active"];
        frm.set_value(Object.fromEntries(fields.map((field, index) => [field, colors[index]])));
    },
    after_save(frm) {
        frappe.call({ method: "c4style.settings.get_settings", callback: response => {
            frappe.c4style.apply_theme(response.message);
            frappe.show_alert({ message: __("Site style saved"), indicator: "green" });
        }});
    },
});
