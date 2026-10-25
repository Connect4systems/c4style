"""Rename the palette DocType before sync so existing records and links survive."""
import frappe


def execute():
    if not frappe.db.exists('DocType', 'Color Palette'):
        return
    if frappe.db.exists('DocType', 'Theme Platte Color'):
        frappe.throw('Both Color Palette and Theme Platte Color exist. Resolve the duplicate DocTypes before migrating.')
    # This is an intentional standard DocType rename, not a record merge.
    frappe.rename_doc('DocType', 'Color Palette', 'Theme Platte Color',
                      force=True, ignore_permissions=True, validate=False,
                      show_alert=False, rebuild_search=False)
    frappe.clear_cache()
