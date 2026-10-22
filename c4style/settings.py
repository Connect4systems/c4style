import json
import math
import re

import frappe

KEY = 'c4style_settings'
DEFAULTS = dict(primary='#714B67', accent='#017E84', background='#E5E8EB',
                fontSize=14, radius=6, density='comfortable', workspaceWide=False,
                direction='auto', menuCollapsed=False, menuBackground='#FFFFFF',
                menuText='#36414C', menuActive='#E5F1F1')


def validate(settings):
    if isinstance(settings, str):
        settings = json.loads(settings)
    if not isinstance(settings, dict) or set(settings) - set(DEFAULTS):
        frappe.throw('Invalid style settings')
    for key, value in settings.items():
        valid = False
        if key in ('primary', 'accent', 'background', 'menuBackground', 'menuText', 'menuActive'):
            valid = isinstance(value, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', value)
        elif key in ('fontSize', 'radius'):
            low, high = (12, 18) if key == 'fontSize' else (2, 16)
            valid = type(value) in (int, float) and math.isfinite(value) and low <= value <= high
        elif key == 'density':
            valid = value in ('compact', 'comfortable')
        elif key == 'direction':
            valid = value in ('auto', 'ltr', 'rtl')
        elif key in ('workspaceWide', 'menuCollapsed'):
            valid = type(value) is bool
        if not valid:
            frappe.throw('Invalid style setting: ' + key)
    return settings


def is_admin():
    return frappe.session.user == 'Administrator' or bool({'System Manager', 'Website Manager'} & set(frappe.get_roles()))


def read_settings(user):
    raw = frappe.defaults.get_defaults_for(user).get(KEY)
    try:
        return validate(raw) if raw else {}
    except (ValueError, TypeError, frappe.ValidationError):
        return {}


SITE_FIELDS = dict(primary='primary', accent='accent', background='background',
                   fontSize='font_size', radius='radius', density='density',
                   menuBackground='menu_background', menuText='menu_text', menuActive='menu_active')
PERSONAL_FIELDS = {'workspaceWide', 'direction', 'menuCollapsed'}


def document_settings(doc):
    return {key: doc.get(field) if doc.get(field) is not None else DEFAULTS[key]
            for key, field in SITE_FIELDS.items()}


def get_site_settings():
    return {**DEFAULTS, **document_settings(frappe.get_single('Style Settings'))}


def boot_session(bootinfo):
    personal = read_settings(frappe.session.user)
    bootinfo.c4style = dict(site=get_site_settings(),
                           personal={k: v for k, v in personal.items() if k in PERSONAL_FIELDS},
                           can_manage=is_admin())


@frappe.whitelist()
def get_settings():
    if frappe.session.user == 'Guest':
        frappe.throw('Please sign in', frappe.PermissionError)
    return get_site_settings()


@frappe.whitelist(methods=['POST'])
def save_settings(settings, scope='personal'):
    if frappe.session.user == 'Guest':
        frappe.throw('Please sign in', frappe.PermissionError)
    if scope not in ('personal', 'site'):
        frappe.throw('Invalid settings scope')
    if scope == 'site' and not is_admin():
        frappe.throw('Only System Manager or Website Manager can edit Style Settings', frappe.PermissionError)
    values = validate(settings)
    if scope == 'site':
        doc = frappe.get_single('Style Settings')
        doc.check_permission('write')
        for key, value in values.items():
            if key in SITE_FIELDS:
                doc.set(SITE_FIELDS[key], value)
        doc.save()
        return document_settings(doc)
    if set(values) - PERSONAL_FIELDS:
        frappe.throw('Personal preferences may only change menu width, workspace width and text direction', frappe.PermissionError)
    # Merge partial menu updates without discarding other account preferences.
    current = {k: v for k, v in read_settings(frappe.session.user).items() if k in PERSONAL_FIELDS}
    current.update(values)
    frappe.defaults.set_default(KEY, json.dumps(current), parent=frappe.session.user)
    frappe.clear_cache(user=frappe.session.user)
    return current
