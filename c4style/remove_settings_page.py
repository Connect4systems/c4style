"""Remove the obsolete custom Page; Style Settings remains the native form."""
import frappe


def execute():
    if frappe.db.exists('Page', 'c4style-settings'):
        frappe.delete_doc('Page', 'c4style-settings', ignore_permissions=True, force=True)
    frappe.clear_cache()
