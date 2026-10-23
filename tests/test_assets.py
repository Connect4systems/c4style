"""Deployment asset URLs must change when the corresponding file changes."""
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class AssetCacheTests(unittest.TestCase):
    def test_changed_asset_gets_a_new_url_without_changing_other_urls(self):
        with tempfile.TemporaryDirectory() as temp:
            app=Path(temp)
            (app/'hooks.py').write_bytes((ROOT/'c4style/hooks.py').read_bytes())
            for relative in ('css/c4style.css','js/c4style.js','js/desk_tools.js','js/notifications.js'):
                target=app/'public'/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((ROOT/'c4style/public'/relative).read_bytes())
            before=runpy.run_path(str(app/'hooks.py'))
            unchanged=runpy.run_path(str(app/'hooks.py'))
            self.assertEqual(before['app_include_js'],unchanged['app_include_js'])
            self.assertEqual(before['app_include_css'],unchanged['app_include_css'])
            with (app/'public/js/c4style.js').open('a') as asset:
                asset.write('\n// New deployment\n')
            after=runpy.run_path(str(app/'hooks.py'))
            self.assertNotEqual(before['app_include_js'][0],after['app_include_js'][0])
            self.assertEqual(before['app_include_js'][1],after['app_include_js'][1])
            self.assertEqual(before['app_include_css'],after['app_include_css'])
            self.assertTrue(after['app_include_js'][0].startswith('/assets/c4style/js/c4style.js?v='))

if __name__=='__main__':unittest.main()
