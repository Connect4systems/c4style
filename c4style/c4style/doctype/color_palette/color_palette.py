import json
import re

import frappe
from frappe.model.document import Document

from c4style.settings import KEY, PALETTES


class ColorPalette(Document):
    def before_validate(self):
        for field, default in PALETTES['C4Style'].items():
            if self.get(field) in (None, ''):
                self.set(field, default)

    def validate(self):
        for field in PALETTES['C4Style']:
            if not re.fullmatch(r'#[0-9a-fA-F]{6}', self.get(field) or ''):
                frappe.throw('Enter a six-digit hex color for ' + field.replace('_', ' '))

    def on_update(self):
        frappe.clear_cache()

    def on_trash(self):
        # Site colors are a saved snapshot and remain usable after removal.
        if frappe.db.get_single_value('Style Settings', 'palette') == self.name:
            frappe.db.set_single_value('Style Settings', 'palette', '')
        frappe.clear_cache()

    def after_rename(self, old, new, merge=False):
        # Frappe updates the Style Settings Link. Personal choices live in JSON.
        for row in frappe.get_all('DefaultValue', filters={'defkey': KEY}, fields=['name', 'defvalue']):
            try:
                values = json.loads(row.defvalue)
            except (ValueError, TypeError):
                continue
            if isinstance(values, dict) and values.get('themePalette') == old:
                values['themePalette'] = new
                frappe.db.set_value('DefaultValue', row.name, 'defvalue', json.dumps(values))
        frappe.clear_cache()
