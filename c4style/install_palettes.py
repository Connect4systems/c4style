"""One-time seed: subsequent migrations must preserve edits, renames and deletes."""
import frappe
from c4style.settings import PALETTES


def execute():
    for name, colors in PALETTES.items():
        if not frappe.db.exists('Theme Platte Color', name):
            frappe.get_doc(dict(doctype='Theme Platte Color', palette_name=name,
                                enabled=1, **colors)).insert(ignore_permissions=True)
    # Custom was a Select placeholder, not an actual palette. Preserve its colors.
    if frappe.db.get_single_value('Style Settings', 'palette') == 'Custom':
        frappe.db.set_single_value('Style Settings', 'palette', '')
    frappe.clear_cache()
