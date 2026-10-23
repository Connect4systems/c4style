"""Ensure the retired extension cannot intercept approval actions."""
import importlib.util
from pathlib import Path
import runpy
import sys
import types
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).parents[1]


class WorkflowRemovalTests(unittest.TestCase):
    def test_no_approval_overrides_or_workflow_scripts_remain(self):
        hooks = runpy.run_path(str(ROOT / 'c4style/hooks.py'))
        self.assertNotIn('override_whitelisted_methods', hooks)
        self.assertNotIn('doc_events', hooks)
        self.assertNotIn('doctype_js', hooks)
        self.assertEqual(hooks['after_install'], 'c4style.install_palettes.execute')
        self.assertEqual(hooks['after_migrate'], 'c4style.remove_workflow_notifications.execute')

    def test_cleanup_only_removes_owned_field_metadata_and_can_repeat(self):
        existing = {'Workflow Transition-c4style_create_notification',
                    'Notification-c4style_workflow'}
        fake = types.ModuleType('frappe')
        fake.db = types.SimpleNamespace(get_value=Mock(side_effect=lambda dt, filters, field:
            f"{filters['dt']}-{filters['fieldname']}" if
            f"{filters['dt']}-{filters['fieldname']}" in existing else None))
        fake.delete_doc = Mock(side_effect=lambda dt, name, **kw: existing.remove(name))
        fake.clear_cache = Mock()
        previous = sys.modules.get('frappe'); sys.modules['frappe'] = fake
        try:
            spec = importlib.util.spec_from_file_location('cleanup', ROOT / 'c4style/remove_workflow_notifications.py')
            cleanup = importlib.util.module_from_spec(spec); spec.loader.exec_module(cleanup)
            cleanup.execute(); cleanup.execute()
        finally:
            if previous is None: sys.modules.pop('frappe', None)
            else: sys.modules['frappe'] = previous
        self.assertEqual(fake.delete_doc.call_count, 2)
        self.assertTrue(all(call.args[0] == 'Custom Field' for call in fake.delete_doc.call_args_list))
        self.assertEqual(existing, set())
