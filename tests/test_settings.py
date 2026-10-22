"""Standalone permission and validation tests; no running Frappe site needed."""
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock


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

    def test_notes_validate_limits_and_do_not_change_site_colors(self):
        note={'id':'one','text':'Private reminder','color':'mint'}
        settings.save_settings({'notes':[note]})
        args, kwargs = fake.defaults.set_default.call_args
        self.assertEqual(json.loads(args[1])['notes'],[note])
        self.assertEqual(kwargs['parent'],fake.session.user)
        for notes in ([dict(note,text='x'*4001)],[note,note],[dict(note,color='red')],[dict(note,owner='someone')], [dict(note,id=str(index),text='x'*4000) for index in range(20)]):
            with self.subTest(notes=notes), self.assertRaises(ValidationError):
                settings.validate({'notes':notes})

    def test_new_component_options_are_validated(self):
        for values in ({'headerStyle':'javascript:evil'},{'announcementSpeed':0},{'announcementText':'x'*1001}, {'inputBorderStyle':'url(evil)'}):
            with self.subTest(values=values),self.assertRaises(ValidationError):settings.validate(values)


if __name__ == '__main__':
    unittest.main()
