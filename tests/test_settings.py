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

    def test_rejects_invalid_and_injected_values(self):
        for values in ({'primary': 'red;display:none'}, {'fontSize': True},
                       {'radius': float('nan')}, {'direction': 'invalid'},
                       {'workspaceWide': 1}, {'unknown': 'value'}, []):
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

    def test_admin_publish_excludes_personal_layout(self):
        fake.get_roles.return_value = ['System Manager']
        settings.save_settings({'primary': '#ffffff', 'direction': 'rtl', 'workspaceWide': True}, 'site')
        args, kwargs = fake.defaults.set_default.call_args
        self.assertEqual(kwargs['parent'], '__default')
        self.assertEqual(json.loads(args[1]), {'primary': '#ffffff'})

    def test_boot_merges_site_defaults_and_personal_settings(self):
        fake.defaults.get_defaults_for.side_effect = lambda user: {
            'c4style_settings': json.dumps({'primary': '#112233'} if user == '__default' else {'direction': 'rtl'})}
        boot = types.SimpleNamespace()
        try:
            settings.boot_session(boot)
            self.assertEqual(boot.c4style['site']['primary'], '#112233')
            self.assertEqual(boot.c4style['personal'], {'direction': 'rtl'})
            self.assertFalse(boot.c4style['can_manage'])
        finally:
            fake.defaults.get_defaults_for.side_effect = None


if __name__ == '__main__':
    unittest.main()
