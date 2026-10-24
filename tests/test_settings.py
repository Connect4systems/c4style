"""Standalone permission and validation tests; no running Frappe site needed."""
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class ValidationError(Exception):
    pass


def throw(message, exc=ValidationError):
    raise exc(message)


fake = types.ModuleType('frappe')
fake.whitelist = lambda **kwargs: lambda fn: fn
fake.throw = throw
fake.ValidationError = ValidationError
fake.PermissionError = PermissionError
fake.session = types.SimpleNamespace(user='user@example.com')
fake.get_roles = Mock(return_value=[])
fake.defaults = types.SimpleNamespace(set_default=Mock(), get_defaults_for=Mock(return_value={}))
fake.clear_cache = Mock()
fake.get_single = Mock()
spec = importlib.util.spec_from_file_location('settings_under_test', Path(__file__).parents[1] / 'c4style/settings.py')
settings = importlib.util.module_from_spec(spec)
previous = sys.modules.get('frappe')
sys.modules['frappe'] = fake
spec.loader.exec_module(settings)
if previous is None:
    del sys.modules['frappe']
else:
    sys.modules['frappe'] = previous


class SettingsTests(unittest.TestCase):
    def setUp(self):
        fake.get_all = Mock(return_value=[dict(name=name, **colors) for name, colors in settings.PALETTES.items()])
        fake.session.user = 'user@example.com'
        fake.get_roles.return_value = []
        fake.defaults.set_default.reset_mock()
        fake.defaults.get_defaults_for.return_value = {}
        self.doc = Mock()
        self.doc.get.side_effect = lambda key: {'primary': '#112233'}.get(key)
        fake.get_single.return_value = self.doc

    def test_rejects_invalid_and_injected_values(self):
        for values in ({'primary': 'red;display:none'}, {'fontSize': True},
                       {'radius': float('nan')}, {'direction': 'invalid'},
                       {'workspaceWide': 1}, {'unknown': 'value'}, {'fontFamily': 'url(evil)'},
                       {'navbarBackground': 'red'}, {'textDirection': 'invalid'},
                       {'brandName': ''}, {'brandName': 'x' * 81}, {'persistentMenu': 1}, []):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                settings.validate(values)

    def test_boot_hides_legacy_settings_search_without_removing_other_pages(self):
        boot = types.SimpleNamespace(page_info={
            'c4style-settings': {'title': 'C4Style Settings'},
            'other-page': {'title': 'Other Page'},
        })
        settings.boot_session(boot)
        self.assertEqual(boot.page_info, {'other-page': {'title': 'Other Page'}})
        self.assertIn('site', boot.c4style)

    def test_non_admin_cannot_publish(self):
        with self.assertRaises(PermissionError):
            settings.save_settings({}, 'site')
        fake.defaults.set_default.assert_not_called()

    def test_guest_cannot_save(self):
        fake.session.user = 'Guest'
        with self.assertRaises(PermissionError):
            settings.save_settings({})

    def test_personal_settings_always_use_session_user(self):
        settings.save_settings({'direction': 'rtl', 'workspaceWide': True})
        args, kwargs = fake.defaults.set_default.call_args
        self.assertEqual(kwargs['parent'], fake.session.user)
        self.assertEqual(json.loads(args[1]), {'direction': 'rtl', 'workspaceWide': True})

    def test_both_manager_roles_can_save_site_colors(self):
        for role in ('System Manager', 'Website Manager'):
            with self.subTest(role=role):
                fake.get_roles.return_value = [role]
                self.doc.reset_mock()
                settings.save_settings({'primary': '#ffffff', 'menuBackground': '#123456'}, 'site')
                self.doc.check_permission.assert_called_once_with('write')
                self.doc.set.assert_any_call('menu_background', '#123456')
                self.doc.save.assert_called_once()

    def test_normal_user_cannot_change_colors_through_personal_api(self):
        for key in ('primary', 'menuBackground', 'menuText', 'menuActive', 'navbarBackground', 'tableHeaderBackground'):
            with self.subTest(key=key), self.assertRaises(PermissionError):
                settings.save_settings({key: '#ffffff'})
        fake.defaults.set_default.assert_not_called()

    def test_personal_theme_selection_requires_the_site_switch(self):
        with self.assertRaises(PermissionError):
            settings.save_settings({'themePalette':'Ocean'})
        fake.defaults.set_default.assert_not_called()
        self.doc.get.side_effect = lambda field: {'primary':'#112233','allow_user_themes':1}.get(field)
        settings.save_settings({'themePalette':'Ocean'})
        self.assertEqual(json.loads(fake.defaults.set_default.call_args.args[1]), {'themePalette':'Ocean'})
        self.assertEqual(fake.defaults.set_default.call_args.kwargs['parent'],fake.session.user)
        self.doc.save.assert_not_called()

    def test_users_cannot_enable_personal_themes_or_save_an_unknown_palette(self):
        with self.assertRaises(PermissionError):
            settings.save_settings({'allowUserThemes':True})
        for palette in ('Custom', 'Unknown', {}, True):
            with self.subTest(palette=palette), self.assertRaises(ValidationError):
                settings.save_settings({'themePalette':palette})

    def test_users_can_reset_to_the_site_theme_while_selection_is_disabled(self):
        settings.save_settings({'themePalette':''})
        self.assertEqual(json.loads(fake.defaults.set_default.call_args.args[1]), {'themePalette':''})

    def test_menu_updates_preserve_other_preferences(self):
        fake.defaults.get_defaults_for.return_value = {
            'c4style_settings': json.dumps({'direction': 'rtl', 'primary': '#ffffff'})}
        settings.save_settings({'menuCollapsed': True})
        args, kwargs = fake.defaults.set_default.call_args
        self.assertEqual(json.loads(args[1]), {'direction': 'rtl', 'menuCollapsed': True})

    def test_boot_ignores_old_personal_color_overrides(self):
        fake.defaults.get_defaults_for.return_value = {
            'c4style_settings': json.dumps({'primary': '#ffffff', 'menuCollapsed': True})}
        boot = types.SimpleNamespace()
        settings.boot_session(boot)
        self.assertEqual(boot.c4style['site']['primary'], '#112233')
        self.assertEqual(boot.c4style['personal'], {'menuCollapsed': True})
        self.assertFalse(boot.c4style['can_manage'])

    def test_single_doctype_permissions(self):
        path = Path(__file__).parents[1] / 'c4style/c4style/doctype/style_settings/style_settings.json'
        doc = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(doc['issingle'], 1)
        self.assertEqual({p['role'] for p in doc['permissions']}, {'System Manager', 'Website Manager'})

    def test_every_settings_control_has_a_server_mapping(self):
        path = Path(__file__).parents[1] / 'c4style/c4style/doctype/style_settings/style_settings.json'
        schema = json.loads(path.read_text())
        controls = {field['fieldname'] for field in schema['fields']
                    if field['fieldtype'] not in ('Tab Break', 'Section Break', 'Column Break', 'HTML')}
        self.assertEqual(controls, set(settings.SITE_FIELDS.values()) | {'palette'})
        self.assertNotIn('persistent_menu', schema['field_order'])

    def test_missing_colors_follow_selected_palette(self):
        self.doc.get.side_effect = lambda field: {'palette': 'Wine', 'primary': '#123456'}.get(field)
        values = settings.document_settings(self.doc)
        self.assertEqual(values['primary'], '#123456')
        self.assertEqual(values['menuBackground'], '#701A3D')
        self.assertEqual(values['announcementColor'], '#831843')

    def test_database_palettes_replace_builtins_and_disabled_choices_are_rejected(self):
        colors = dict(settings.PALETTES['Ocean'], primary='#123456')
        fake.get_all.return_value = [dict(name='Company Blue', **colors)]
        self.assertEqual(settings.get_palettes(), {'Company Blue': colors})
        self.assertEqual(settings.get_palette('Company Blue')['primary'], '#123456')
        fake.get_all.assert_called_with('Color Palette', filters={'enabled': 1},
            fields=['name', *list(settings.PALETTES['C4Style'])], order_by='name')
        for name in ('Ocean', 'Deleted Palette'):
            with self.assertRaises(ValidationError): settings.get_palette(name)
            with self.assertRaises(ValidationError): settings.save_settings({'themePalette': name})

    def test_unavailable_personal_palette_does_not_discard_layout_and_notes(self):
        fake.get_all.return_value = []
        fake.defaults.get_defaults_for.return_value = {settings.KEY: json.dumps({
            'themePalette': 'Ocean', 'menuCollapsed': True,
            'notes': [{'id': 'one', 'text': 'Keep this', 'color': 'mint'}]})}
        personal = settings.read_settings(fake.session.user)
        self.assertNotIn('themePalette', personal)
        self.assertTrue(personal['menuCollapsed'])
        self.assertEqual(personal['notes'][0]['text'], 'Keep this')

    def test_palette_doctype_is_managed_only_by_requested_roles(self):
        schema = json.loads((Path(__file__).parents[1] /
            'c4style/c4style/doctype/color_palette/color_palette.json').read_text())
        self.assertEqual(schema['allow_rename'], 1)
        self.assertEqual({p['role'] for p in schema['permissions']}, {'System Manager', 'Website Manager'})
        for permission in schema['permissions']:
            self.assertTrue(all(permission[key] for key in ('create','read','write','delete','rename')))
        self.assertEqual({field['fieldname'] for field in schema['fields'] if field['fieldtype']=='Color'},
                         set(settings.PALETTES['C4Style']))
        for field in schema['fields']:
            if field['fieldtype'] == 'Color':
                self.assertNotIn('depends_on', field)
                self.assertEqual(field['default'], settings.PALETTES['C4Style'][field['fieldname']])

    def test_palette_seed_preserves_existing_records_and_custom_site_colors(self):
        service = types.ModuleType('frappe')
        service.db = types.SimpleNamespace(exists=Mock(return_value=True),
            get_single_value=Mock(return_value='Custom'), set_single_value=Mock())
        service.get_doc = Mock(); service.clear_cache = Mock()
        with patch.dict(sys.modules, {'frappe': service, 'c4style.settings': settings}):
            spec = importlib.util.spec_from_file_location('palette_seed',
                Path(__file__).parents[1] / 'c4style/install_palettes.py')
            seed = importlib.util.module_from_spec(spec); spec.loader.exec_module(seed)
            seed.execute()
            service.get_doc.assert_not_called()
            service.db.set_single_value.assert_called_once_with('Style Settings', 'palette', '')
            service.db.exists.return_value = False
            seed.execute()
            self.assertEqual(service.get_doc.call_count, 17)
            self.assertTrue(all(call.args[0]['enabled'] == 1 for call in service.get_doc.call_args_list))

    def test_palette_rename_preserves_personal_preferences_and_validates_colors(self):
        service = types.ModuleType('frappe'); service.throw = throw; service.clear_cache = Mock()
        service.get_all = Mock(return_value=[types.SimpleNamespace(name='pref-1',defvalue=json.dumps({
            'themePalette':'Old name','menuCollapsed':True})),
            types.SimpleNamespace(name='pref-2',defvalue='broken')])
        service.db = types.SimpleNamespace(set_value=Mock())
        document = types.ModuleType('frappe.model.document'); document.Document = object
        with patch.dict(sys.modules, {'frappe':service, 'c4style.settings':settings,
                                     'frappe.model.document':document}):
            spec = importlib.util.spec_from_file_location('palette_controller',
                Path(__file__).parents[1] / 'c4style/c4style/doctype/color_palette/color_palette.py')
            module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
            record = module.ColorPalette()
            colors = {'primary':'#123456'}
            record.get = colors.get
            record.set = colors.__setitem__
            record.before_validate()
            record.validate()
            self.assertEqual(colors['primary'], '#123456')
            self.assertEqual(colors['announcement_background'], settings.PALETTES['C4Style']['announcement_background'])
            self.assertEqual(colors['announcement_color'], settings.PALETTES['C4Style']['announcement_color'])
            record.get = lambda field:settings.PALETTES['Ocean'][field]
            record.validate()
            record.get = lambda field:'red;display:none'
            with self.assertRaises(ValidationError): record.validate()
            record.after_rename('Old name','New name')
            self.assertEqual(json.loads(service.db.set_value.call_args.args[3]), {
                'themePalette':'New name','menuCollapsed':True})

    def test_palette_only_api_applies_defaults_and_preserves_explicit_edits(self):
        fake.get_roles.return_value = ['Website Manager']
        self.doc.meta.get_field.return_value.options = 'Wine\nCustom'
        settings.save_settings({'primary': '#123456'}, 'site', palette='Wine')
        self.doc.set.assert_any_call('menu_background', '#701A3D')
        self.doc.set.assert_any_call('announcement_color', '#831843')
        self.doc.set.assert_any_call('primary', '#123456')

    def test_notes_validate_limits_and_do_not_change_site_colors(self):
        note={'id':'one','text':'Private reminder','color':'mint'}
        settings.save_settings({'notes':[note]})
        args, kwargs = fake.defaults.set_default.call_args
        self.assertEqual(json.loads(args[1])['notes'],[note])
        self.assertEqual(kwargs['parent'],fake.session.user)
        for notes in ([dict(note,text='x'*4001)],[note,note],[dict(note,color='red')],[dict(note,owner='someone')], [dict(note,id=str(index),text='x'*4000) for index in range(20)]):
            with self.subTest(notes=notes), self.assertRaises(ValidationError):
                settings.validate({'notes':notes})

    def test_notes_accept_persistent_minimized_state_and_reject_invalid_state(self):
        note = {'id': 'one', 'text': 'Reminder', 'color': 'mint', 'minimized': True}
        settings.save_settings({'notes': [note]})
        self.assertEqual(json.loads(fake.defaults.set_default.call_args.args[1])['notes'], [note])
        for value in (1, 'true', None, {}):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                settings.validate({'notes': [{**note, 'minimized': value}]})

    def test_new_component_options_are_validated(self):
        for values in ({'headerStyle':'javascript:evil'},{'announcementSpeed':0},{'announcementText':'x'*1001}, {'inputBorderStyle':'url(evil)'}):
            with self.subTest(values=values),self.assertRaises(ValidationError):settings.validate(values)


if __name__ == '__main__':
    unittest.main()
