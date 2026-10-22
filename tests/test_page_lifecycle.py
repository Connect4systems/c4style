"""Exercise the real assets in QuickJS with the Frappe page lifecycle."""
from pathlib import Path
import unittest

try:
    import quickjs
except ImportError:
    quickjs = None

ROOT = Path(__file__).parents[1]


@unittest.skipIf(quickjs is None, 'Install quickjs to run JavaScript lifecycle tests')
class PageLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.context = quickjs.Context()
        self.context.eval('''
            var __ = (text) => text;
            var markup = "";
            var controls = {};
            var listeners = {};
            var container = {
                querySelectorAll: () => [],
                querySelector: (selector) => controls[selector] || (controls[selector] = {
                    textContent: "", setAttribute: function (key, value) { this[key] = value; }
                }),
                addEventListener: (name, fn) => { listeners[name] = fn; }
            };
            var document = {
                documentElement: {
                    dir: "ltr", getAttribute: () => "ltr",
                    setAttribute: function (key, value) { this[key] = value; },
                    style: { setProperty: () => {} }
                },
                body: { classList: { toggle: () => {} } },
                querySelector: () => null
            };
            var localStorage = { getItem: () => null, setItem: () => {} };
            var MutationObserver = function () { this.observe = () => {}; };
            var pageCreated = 0;
            var frappe = {
                session: { user: "Administrator" },
                boot: { c4style: { site: {}, personal: {}, can_manage: true } },
                pages: {},
                ui: { make_app_page: function (options) {
                    pageCreated++;
                    return { main: {
                        html: (value) => { markup = value; },
                        find: () => [container]
                    }};
                }}
            };
        ''')
        self.context.eval((ROOT / 'c4style/public/js/c4style.js').read_text(encoding='utf-8'))

    def load_page(self):
        # Frappe PageView constructs a page only when this registry entry is absent.
        self.assertTrue(self.context.eval('!frappe.pages["c4style-settings"]'))
        self.context.eval('frappe.pages["c4style-settings"] = { page_name: "c4style-settings" };')
        self.context.eval((ROOT / 'c4style/c4style/page/c4style_settings/c4style_settings.js').read_text(encoding='utf-8'))
        self.context.eval('frappe.pages["c4style-settings"].on_page_load(frappe.pages["c4style-settings"]);')

    def test_route_constructs_and_renders_settings(self):
        self.load_page()
        self.assertEqual(self.context.eval('pageCreated'), 1)
        markup = self.context.eval('markup')
        for text in ('Color theme', 'Text direction', 'Save my preferences', 'Apply style for all users'):
            self.assertIn(text, markup)

    def test_workspace_arrow_and_label_change_after_click(self):
        self.load_page()
        self.assertEqual(self.context.eval('controls["[data-workspace-icon]"].textContent'), '\u2192')
        self.context.eval('''listeners.click({ target: { closest: (selector) =>
            selector === "[data-action]" ? { dataset: { action: "workspace" } } : null
        }});''')
        self.assertEqual(self.context.eval('controls["[data-workspace-icon]"].textContent'), '\u2190')
        self.assertEqual(self.context.eval('controls["[data-workspace-label]"].textContent'), 'Narrow workspace')

    def test_regular_user_does_not_see_publish_button(self):
        self.context.eval('frappe.boot.c4style.can_manage = false;')
        self.load_page()
        self.assertNotIn('data-action="publish"', self.context.eval('markup'))


if __name__ == '__main__':
    unittest.main()
