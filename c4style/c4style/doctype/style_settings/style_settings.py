import frappe
from frappe.model.document import Document
from c4style.settings import get_palette, document_settings, is_admin, validate


class StyleSettings(Document):
    def validate(self):
        if not is_admin():
            frappe.throw("Only System Manager or Website Manager can edit Style Settings", frappe.PermissionError)
        previous = self.get_doc_before_save()
        changed = not previous or previous.get('palette') != self.get('palette')
        # An already-selected palette may have since been disabled. Keep the
        # saved site colors, but reject any new selection of a disabled record.
        preset = get_palette(self.palette) if self.get('palette') and changed else {}
        for field, value in preset.items():
            # Preserve explicit edits while supplying preset defaults.
            if self.get(field) in (None, '') or (
                previous and previous.get('palette') != self.get('palette')
                and self.get(field) == previous.get(field)
            ):
                self.set(field, value)
        validate(document_settings(self))

    def on_update(self):
        frappe.clear_cache()
