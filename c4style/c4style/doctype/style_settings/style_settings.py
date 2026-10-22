import frappe
from frappe.model.document import Document
from c4style.settings import document_settings, is_admin, validate


class StyleSettings(Document):
    def validate(self):
        if not is_admin():
            frappe.throw("Only System Manager or Website Manager can edit Style Settings", frappe.PermissionError)
        validate(document_settings(self))

    def on_update(self):
        frappe.clear_cache()
