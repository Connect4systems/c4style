import json
import math
import re

import frappe

KEY = 'c4style_settings'
DEFAULTS = dict(primary='#714B67', accent='#017E84', background='#E5E8EB',
                fontSize=14, radius=6, density='comfortable', workspaceWide=False,
                direction='auto')


def validate(settings):
    if isinstance(settings, str):
        settings = json.loads(settings)
    if not isinstance(settings, dict) or set(settings) - set(DEFAULTS):
        frappe.throw('Invalid style settings')
    for key, value in settings.items():
        valid = False
        if key in ('primary', 'accent', 'background'):
            valid = isinstance(value, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', value)
        elif key in ('fontSize', 'radius'):
            low, high = (12, 18) if key == 'fontSize' else (2, 16)
            valid = type(value) in (int, float) and math.isfinite(value) and low <= value <= high
        elif key == 'density':
            valid = value in ('compact', 'comfortable')
        elif key == 'direction':
            valid = value in ('auto', 'ltr', 'rtl')
        elif key == 'workspaceWide':
            valid = type(value) is bool
        if not valid:
            frappe.throw('Invalid style setting: ' + key)
    return settings


def is_admin():
    return frappe.session.user == 'Administrator' or 'System Manager' in frappe.get_roles()


def read_settings(user):
    raw = frappe.defaults.get_defaults_for(user).get(KEY)
    try:
        return validate(raw) if raw else {}
    except (ValueError, TypeError, frappe.ValidationError):
        return {}


def boot_session(bootinfo):
    bootinfo.c4style = dict(site={**DEFAULTS, **read_settings('__default')},
                           personal=read_settings(frappe.session.user), can_manage=is_admin())


@frappe.whitelist(methods=['POST'])
def save_settings(settings, scope='personal'):
    if frappe.session.user == 'Guest':
        frappe.throw('Please sign in', frappe.PermissionError)
    if scope not in ('personal', 'site'):
        frappe.throw('Invalid settings scope')
    if scope == 'site' and not is_admin():
        frappe.throw('Only System Managers can change the site theme', frappe.PermissionError)
    values = validate(settings)
    if scope == 'site':
        values = {key: value for key, value in values.items()
                  if key not in ('workspaceWide', 'direction')}
    frappe.defaults.set_default(KEY, json.dumps(values),
                               parent='__default' if scope == 'site' else frappe.session.user)
    frappe.clear_cache()
    return values
