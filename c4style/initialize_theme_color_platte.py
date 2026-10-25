"""Initialize the independent theme store without accessing other palette DocTypes."""
import frappe
from c4style.install_palettes import execute as seed_palettes


def execute():
    # A separate patch is necessary when install_palettes already ran on this site.
    seed_palettes()
    selected = frappe.db.get_single_value('Style Settings', 'palette')
    if selected and not frappe.db.exists('Theme Color Platte', selected):
        # Preserve all saved site colors; only detach an unavailable preset.
        frappe.db.set_single_value('Style Settings', 'palette', '')
    frappe.clear_cache()
