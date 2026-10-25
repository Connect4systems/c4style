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

    def test_existing_doctype_is_renamed_without_merging_or_reseeding(self):
        service = self.service({('DocType', 'Color Palette')})
        load('rename_theme_platte_color', service).execute()
        service.rename_doc.assert_called_once_with('DocType', 'Color Palette', 'Theme Platte Color',
            force=True, ignore_permissions=True, validate=False, show_alert=False, rebuild_search=False)
        service.delete_doc.assert_not_called()

    def test_fresh_and_already_upgraded_sites_skip_rename(self):
        for existing in (set(), {('DocType', 'Theme Platte Color')}):
            service = self.service(existing)
            load('rename_theme_platte_color', service).execute()
            service.rename_doc.assert_not_called()

    def test_conflicting_doctypes_stop_before_changing_data(self):
        service = self.service({('DocType', 'Color Palette'), ('DocType', 'Theme Platte Color')})
        with self.assertRaises(ValueError):
            load('rename_theme_platte_color', service).execute()
        service.rename_doc.assert_not_called()

    def test_cleanup_only_deletes_retired_page_and_is_repeatable(self):
        for exists in (True, False):
            service = self.service({('Page', 'c4style-settings')} if exists else set())
            load('remove_settings_page', service).execute()
            if exists:
                service.delete_doc.assert_called_once_with('Page', 'c4style-settings', ignore_permissions=True, force=True)
            else:
                service.delete_doc.assert_not_called()
        self.assertFalse((ROOT / 'c4style/c4style/page/c4style_settings/c4style_settings.json').exists())

    def test_rename_runs_before_sync_and_page_cleanup_after_sync(self):
        patches = (ROOT / 'c4style/patches.txt').read_text()
        self.assertLess(patches.index('c4style.rename_theme_platte_color'), patches.index('[post_model_sync]'))
        self.assertGreater(patches.index('c4style.remove_settings_page'), patches.index('[post_model_sync]'))
