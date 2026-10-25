"""Upgrade coverage for existing palette data and retired Page cleanup."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).parents[1]


def load(name, service):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'c4style' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'frappe': service}):
        spec.loader.exec_module(module)
    return module


class ThemeMigrationTests(unittest.TestCase):
    def service(self, existing):
        service = types.ModuleType('frappe')
        service.db = types.SimpleNamespace(exists=Mock(side_effect=lambda dt, name: (dt, name) in existing))
        service.rename_doc = Mock()
        service.delete_doc = Mock()
        service.clear_cache = Mock()
        service.throw = Mock(side_effect=ValueError)
        return service

    def test_retired_rename_patch_never_accesses_existing_palette_doctypes(self):
        for existing in (set(), {('DocType', 'Color Palette')},
                         {('DocType', 'Color Palette'), ('DocType', 'Theme Platte Color')}):
            service = self.service(existing)
            load('rename_theme_platte_color', service).execute()
            service.db.exists.assert_not_called()
            service.rename_doc.assert_not_called()
            service.delete_doc.assert_not_called()

    def test_independent_store_is_seeded_without_modifying_original_records(self):
        import json
        service = self.service(set())
        service.db.get_single_value = Mock(return_value='Original custom palette')
        service.db.set_single_value = Mock()
        service.get_doc = Mock()
        settings = types.ModuleType('c4style.settings')
        settings.PALETTES = json.loads((ROOT / 'c4style/palettes.json').read_text())
        with patch.dict(sys.modules, {'c4style.settings': settings}):
            seed = load('install_palettes', service)
        with patch.dict(sys.modules, {'c4style.install_palettes': seed}):
            migration = load('initialize_theme_color_platte', service)
        migration.execute()
        self.assertEqual(service.get_doc.call_count, 17)
        self.assertTrue(all(call.args[0]['doctype'] == 'Theme Color Platte'
                            for call in service.get_doc.call_args_list))
        self.assertTrue(all(call.args[0] == 'Theme Color Platte'
                            for call in service.db.exists.call_args_list))
        service.db.set_single_value.assert_called_once_with('Style Settings', 'palette', '')
        service.rename_doc.assert_not_called()
        service.delete_doc.assert_not_called()

    def test_cleanup_only_deletes_retired_page_and_is_repeatable(self):
        for exists in (True, False):
            service = self.service({('Page', 'c4style-settings')} if exists else set())
            load('remove_settings_page', service).execute()
            if exists:
                service.delete_doc.assert_called_once_with('Page', 'c4style-settings', ignore_permissions=True, force=True)
            else:
                service.delete_doc.assert_not_called()
        self.assertFalse((ROOT / 'c4style/c4style/page/c4style_settings/c4style_settings.json').exists())

    def test_initialization_and_page_cleanup_run_after_sync(self):
        patches = (ROOT / 'c4style/patches.txt').read_text()
        self.assertGreater(patches.index('c4style.initialize_theme_color_platte'), patches.index('[post_model_sync]'))
        self.assertGreater(patches.index('c4style.remove_settings_page'), patches.index('[post_model_sync]'))
