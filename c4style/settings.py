import json
import math
import re
from pathlib import Path

import frappe

KEY = 'c4style_settings'
PALETTES = json.loads(Path(__file__).with_name('palettes.json').read_text(encoding='utf-8'))


@frappe.whitelist()
def get_palettes():
    if frappe.session.user == 'Guest':
        frappe.throw('Please sign in', frappe.PermissionError)
    fields = list(PALETTES['C4Style'])
    return {row['name']: {field: row[field] for field in fields}
            for row in frappe.get_all('Theme Color Platte', filters={'enabled': 1},
                                      fields=['name', *fields], order_by='name')}


@frappe.whitelist()
def get_palette(name):
    if not isinstance(name, str):
        frappe.throw('Select an enabled Theme Color Platte')
    palette = get_palettes().get(name)
    if palette is None:
        frappe.throw('Select an enabled Theme Color Platte')
    return palette


DEFAULTS = dict(primary='#714B67', accent='#017E84', background='#E5E8EB',
                fontSize=14, radius=6, density='comfortable', workspaceWide=False,
                direction='auto', menuCollapsed=False, menuBackground='#FFFFFF',
                menuText='#36414C', menuActive='#E5F1F1',
                navbarBackground='#714B67', navbarText='#FFFFFF', panelBackground='#FFFFFF',
                tableHeaderBackground='#714B67', tableHeaderText='#FFFFFF',
                fontFamily='system', textDirection='auto', brandName='C4Style',
                headerStyle='pill', rowStyle='separated', inputBorderStyle='dashed',
                fieldStyle='boxed', buttonStyle='filled', shadowStyle='soft', menuBehavior='hover',
                secondaryBackground='#A58F7A', secondaryText='#FFFFFF',
                rowHoverBackground='#F1F6ED', rowBorder='#CAD3C4',
                inputBackground='#FFFFFF', inputBorder='#A9B49F',
                menuDefaultCollapsed=True, showScrollButtons=True, nativeDrawers=True,
                enableAnnouncement=False, announcementText='', announcementSpeed=24, announcementFontSize=14,
                announcementBackground='#F0EDF7', announcementColor='#36414C', notes=[],
                allowUserThemes=False, themePalette='', notificationSound=True)


def validate(settings):
    if isinstance(settings, str):
        settings = json.loads(settings)
    if not isinstance(settings, dict) or set(settings) - set(DEFAULTS):
        frappe.throw('Invalid style settings')
    for key, value in settings.items():
        valid = False
        if key in ('primary', 'accent', 'background', 'menuBackground', 'menuText', 'menuActive',
                   'navbarBackground', 'navbarText', 'panelBackground',
                   'tableHeaderBackground', 'tableHeaderText', 'secondaryBackground', 'secondaryText',
                   'rowHoverBackground', 'rowBorder', 'inputBackground', 'inputBorder',
                   'announcementBackground', 'announcementColor'):
            valid = isinstance(value, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', value)
        elif key in ('fontSize', 'radius', 'announcementSpeed', 'announcementFontSize'):
            low, high = {'fontSize': (12, 18), 'radius': (2, 16), 'announcementSpeed': (5, 120), 'announcementFontSize': (10, 48)}[key]
            valid = type(value) in (int, float) and math.isfinite(value) and low <= value <= high
        elif key == 'density':
            valid = value in ('compact', 'comfortable')
        elif key in ('direction', 'textDirection'):
            valid = value in ('auto', 'ltr', 'rtl')
        elif key == 'fontFamily':
            valid = value in ('system', 'arial', 'tahoma', 'georgia')
        elif key == 'themePalette':
            valid = isinstance(value, str) and (value == '' or value in get_palettes())
        elif key == 'brandName':
            valid = isinstance(value, str) and 1 <= len(value.strip()) <= 80
        elif key in ('headerStyle', 'rowStyle', 'inputBorderStyle', 'fieldStyle', 'buttonStyle', 'shadowStyle', 'menuBehavior'):
            valid = value in {
                'headerStyle': ('pill', 'flat'), 'rowStyle': ('separated', 'flat'),
                'inputBorderStyle': ('dashed', 'solid', 'none'), 'fieldStyle': ('boxed', 'underline'),
                'buttonStyle': ('filled', 'outline'), 'shadowStyle': ('soft', 'none'),
                'menuBehavior': ('hover', 'click'),
            }[key]
        elif key == 'announcementText':
            valid = isinstance(value, str) and len(value) <= 1000
        elif key == 'notes':
            valid = isinstance(value, list) and len(value) <= 20 and all(
                isinstance(note, dict) and {'id', 'text', 'color'} <= set(note)
                and set(note) <= {'id', 'text', 'color', 'minimized'}
                and ('minimized' not in note or type(note['minimized']) is bool)
                and isinstance(note['id'], str) and 1 <= len(note['id']) <= 80
                and isinstance(note['text'], str) and len(note['text']) <= 4000
                and note['color'] in ('mint', 'sun', 'rose', 'sky') for note in value
            )
            if valid:
                valid = len({note['id'] for note in value}) == len(value) and len(json.dumps(value).encode('utf-8')) <= 48000
        elif key in ('workspaceWide', 'menuCollapsed', 'menuDefaultCollapsed',
                     'showScrollButtons', 'nativeDrawers', 'enableAnnouncement', 'allowUserThemes', 'notificationSound'):
            valid = type(value) is bool
        if not valid:
            frappe.throw('Invalid style setting: ' + key)
    return settings


def is_admin():
    return frappe.session.user == 'Administrator' or bool({'System Manager', 'Website Manager'} & set(frappe.get_roles()))


def read_settings(user):
    raw = frappe.defaults.get_defaults_for(user).get(KEY)
    try:
        values = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(values, dict) and values.get('themePalette') not in get_palettes():
            values.pop('themePalette', None)
        return validate(values) if values else {}
    except (ValueError, TypeError, frappe.ValidationError):
        return {}


SITE_FIELDS = dict(allowUserThemes='allow_user_themes', primary='primary', accent='accent', background='background',
                   fontSize='font_size', radius='radius', density='density',
                   menuBackground='menu_background', menuText='menu_text', menuActive='menu_active',
                   navbarBackground='navbar_background', navbarText='navbar_text',
                   panelBackground='panel_background', tableHeaderBackground='table_header_background',
                   tableHeaderText='table_header_text', fontFamily='font_family',
                   textDirection='text_direction', brandName='brand_name',
                   headerStyle='header_style', rowStyle='row_style', inputBorderStyle='input_border_style',
                   fieldStyle='field_style', buttonStyle='button_style', shadowStyle='shadow_style',
                   menuBehavior='menu_behavior', secondaryBackground='secondary_background',
                   secondaryText='secondary_text', rowHoverBackground='row_hover_background',
                   rowBorder='row_border', inputBackground='input_background', inputBorder='input_border',
                   menuDefaultCollapsed='menu_default_collapsed', showScrollButtons='show_scroll_buttons',
                   nativeDrawers='native_drawers', enableAnnouncement='enable_announcement',
                   announcementFontSize='announcement_font_size', announcementText='announcement_text', announcementSpeed='announcement_speed',
                   announcementBackground='announcement_background', announcementColor='announcement_color')
PERSONAL_FIELDS = {'workspaceWide', 'direction', 'menuCollapsed', 'notes', 'themePalette', 'notificationSound'}


def document_settings(doc):
    palette = get_palettes().get(doc.get('palette'), {})
    values = {key: doc.get(field) if doc.get(field) not in (None, '') else palette.get(field, DEFAULTS[key])
              for key, field in SITE_FIELDS.items()}
    for key in ('menuDefaultCollapsed', 'showScrollButtons', 'nativeDrawers', 'enableAnnouncement', 'allowUserThemes'):
        if values[key] in (0, 1):
            values[key] = bool(values[key])
    return values


def get_site_settings():
    return {**DEFAULTS, **document_settings(frappe.get_single('Style Settings'))}


def boot_session(bootinfo):
    # Suppress stale Page metadata while upgraded sessions refresh their cache.
    page_info = bootinfo.get('page_info') if isinstance(bootinfo, dict) else getattr(bootinfo, 'page_info', None)
    if isinstance(page_info, dict):
        page_info.pop('c4style-settings', None)
    personal = read_settings(frappe.session.user)
    bootinfo.c4style = dict(site=get_site_settings(),
                           personal={k: v for k, v in personal.items() if k in PERSONAL_FIELDS},
                           can_manage=is_admin(), palettes=get_palettes())


@frappe.whitelist()
def get_settings():
    if frappe.session.user == 'Guest':
        frappe.throw('Please sign in', frappe.PermissionError)
    return get_site_settings()


@frappe.whitelist(methods=['POST'])
def save_settings(settings, scope='personal', palette=None):
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
        if palette is not None:
            if not isinstance(palette, str):
                frappe.throw('Invalid palette')
            preset = get_palette(palette)
            doc.set('palette', palette)
            # Apply the entire preset; explicit manager edits win.
            values = {**{key: preset[field] for key, field in SITE_FIELDS.items()
                         if field in preset}, **values}
        for key, value in values.items():
            if key in SITE_FIELDS:
                doc.set(SITE_FIELDS[key], value)
        doc.save()
        return document_settings(doc)
    if set(values) - PERSONAL_FIELDS:
        frappe.throw('Personal preferences may only change layout, notes and an allowed theme preference', frappe.PermissionError)
    if values.get('themePalette') and not get_site_settings()['allowUserThemes']:
        frappe.throw('Personal theme selection is disabled by the site manager', frappe.PermissionError)
    # Merge partial menu updates without discarding other account preferences.
    current = {k: v for k, v in read_settings(frappe.session.user).items() if k in PERSONAL_FIELDS}
    current.update(values)
    frappe.defaults.set_default(KEY, json.dumps(current), parent=frappe.session.user)
    frappe.clear_cache(user=frappe.session.user)
    return current
