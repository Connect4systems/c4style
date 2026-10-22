"""Browser checks for native settings and the per-user workspace menu."""
from pathlib import Path
import unittest
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
ROOT = Path(__file__).parents[1]


@unittest.skipIf(sync_playwright is None, 'Install Playwright and Chromium to run browser checks')
class MenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.route('https://c4style.test/**', lambda route: route.fulfill(content_type='text/html', body='''
            <html><body><nav class="navbar"></nav><div class="layout-main" style="display:flex">
            <aside class="layout-side-section"><div class="desk-sidebar">
            <div class="desk-sidebar-item standard-sidebar-item selected"><a class="item-anchor" href="/app/accounting">
            <span class="sidebar-item-icon">A</span><span class="sidebar-item-label">Accounting</span></a></div>
            </div></aside><main>Workspace</main></div></body></html>'''))
        self.page.goto('https://c4style.test/app/home')
        self.page.add_style_tag(content=(ROOT / 'c4style/public/css/c4style.css').read_text(encoding='utf-8'))
        self.page.add_script_tag(content='''
            window.__ = text => text;
            window.calls = [];
            window.frappe = {
                session: {user: 'normal@example.com'},
                boot: {c4style: {site: {menuBackground:'#123456'}, personal:{}, can_manage:false}},
                pages: {}, show_alert: () => {},
                ui: {form: {on: (name, events) => { window.formEvents = events; }}},
                call(options) {
                    calls.push(options.args);
                    if (options.callback) options.callback({message:{}});
                    if (options.always) options.always();
                },
                set_route: (...args) => { window.route = args; },
                container: {add_page: () => ({})}
            };
        ''')
        self.page.add_script_tag(content=(ROOT / 'c4style/public/js/c4style.js').read_text(encoding='utf-8'))

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.page.close()

    def test_menu_collapses_to_icons_and_preserves_links(self):
        self.page.get_by_role('button', name='Narrow menu', exact=True).click()
        self.assertFalse(self.page.locator('.sidebar-item-label').is_visible())
        self.assertTrue(self.page.locator('.sidebar-item-icon').is_visible())
        self.assertEqual(self.page.locator('.item-anchor').get_attribute('href'), '/app/accounting')
        self.assertEqual(self.page.locator('.item-anchor').get_attribute('aria-label'), 'Accounting')
        self.assertEqual(self.page.locator('.c4style-menu-section').evaluate('(el) => getComputedStyle(el).maxWidth'), '76px')
        self.page.get_by_role('button', name='Expand menu', exact=True).click()
        self.assertTrue(self.page.locator('.sidebar-item-label').is_visible())
        self.assertEqual(self.page.evaluate('JSON.parse(calls[0].settings)'), {'menuCollapsed': True})

    def test_no_header_settings_link_and_site_menu_color_applies(self):
        self.assertEqual(self.page.locator('nav button').count(), 0)
        self.assertEqual(self.page.locator('.desk-sidebar').evaluate('(el) => getComputedStyle(el).backgroundColor'), 'rgb(18, 52, 86)')

    def test_workspace_width_saves_separately(self):
        self.page.get_by_role('button', name='Expand workspace', exact=True).click()
        self.assertTrue(self.page.locator('body').evaluate('(el) => el.classList.contains("c4style-workspace-wide")'))
        self.assertEqual(self.page.evaluate('JSON.parse(calls[0].settings)'), {'workspaceWide': True})

    def test_palette_updates_site_and_menu_colors(self):
        self.page.add_script_tag(content=(ROOT / 'c4style/c4style/doctype/style_settings/style_settings.js').read_text(encoding='utf-8'))
        self.page.evaluate('formEvents.palette({doc:{palette:"Ocean"}, set_value: values => {window.paletteValues = values;}})')
        self.assertEqual(self.page.evaluate('paletteValues.menu_background'), '#153747')
        self.assertEqual(self.page.evaluate('paletteValues.primary'), '#155E75')

    def test_new_sidebars_get_toggle_without_duplicate_buttons(self):
        self.page.evaluate('document.body.insertAdjacentHTML("beforeend", \'<aside class="layout-side-section"><div class="desk-sidebar"></div></aside>\')')
        self.page.wait_for_function('document.querySelectorAll("[data-c4style-menu-controls]").length === 2')
        self.assertEqual(self.page.locator('[data-c4style-toggle="menuCollapsed"]').count(), 2)

    def test_failed_save_restores_menu(self):
        self.page.evaluate('() => { frappe.call = options => {options.error(); options.always();}; }')
        self.page.get_by_role('button', name='Narrow menu', exact=True).click()
        self.assertTrue(self.page.locator('.sidebar-item-label').is_visible())
        self.assertTrue(self.page.get_by_role('button', name='Narrow menu', exact=True).is_enabled())

    def enable_app_menu(self):
        self.page.evaluate('''() => {
            frappe.boot.allowed_workspaces = [
                {name:'Accounting',title:'Accounting',public:1,icon:'accounting'},
                {name:'Reports',title:'Reports',public:1,parent_page:'Accounting'},
                {name:'Private notes',title:'Private notes',public:0},
                {name:'Hidden',title:'Hidden',public:1,is_hidden:1}
            ];
            frappe.c4style.apply_theme({persistentMenu:true,brandName:'Connect 4',fontFamily:'tahoma',navbarBackground:'#3F6212',navbarText:'#FFFFFF',tableHeaderBackground:'#3F6212',tableHeaderText:'#FFFFFF'});
        }''')

    def test_persistent_menu_uses_allowed_workspaces_and_removes_duplicate_sidebar(self):
        self.enable_app_menu()
        nav = self.page.locator('.c4style-app-menu')
        self.assertTrue(nav.is_visible())
        self.assertEqual(nav.locator('a[data-workspace]').count(), 3)
        self.assertEqual(nav.locator('a[data-workspace="Private notes"]').get_attribute('href'), '/app/private/private-notes')
        self.assertEqual(nav.locator('details a[data-workspace="Reports"]').count(), 1)
        self.assertFalse(self.page.locator('.layout-side-section').is_visible())
        self.assertEqual(self.page.locator('[data-c4style-menu-controls]').count(), 1)
        self.page.get_by_role('button', name='Narrow menu', exact=True).click()
        self.assertFalse(nav.locator('.sidebar-item-label').first.is_visible())
        self.assertTrue(nav.locator('a[data-workspace="Reports"]').is_visible())
        self.assertEqual(nav.evaluate('(el) => getComputedStyle(el).width'), '72px')
        self.assertEqual(self.page.locator('nav.navbar').evaluate('(el) => getComputedStyle(el).backgroundColor'), 'rgb(63, 98, 18)')

    def test_direction_switch_saves_personally_and_moves_navigation(self):
        self.enable_app_menu()
        self.page.get_by_role('button', name='Switch to right-to-left').click()
        self.assertEqual(self.page.locator('html').get_attribute('dir'), 'rtl')
        self.assertEqual(self.page.evaluate('JSON.parse(calls[0].settings)'), {'direction':'rtl'})
        box = self.page.locator('.c4style-app-menu').bounding_box()
        self.assertAlmostEqual(box['x'] + box['width'], self.page.viewport_size['width'], delta=1)
        self.page.get_by_role('button', name='Switch to left-to-right').click()
        self.assertEqual(self.page.locator('html').get_attribute('dir'), 'ltr')

    def test_persistent_menu_can_be_disabled_without_losing_native_controls(self):
        self.enable_app_menu()
        self.page.evaluate('frappe.c4style.apply_theme({persistentMenu:false})')
        self.assertEqual(self.page.locator('.c4style-app-menu').count(), 0)
        self.assertTrue(self.page.locator('.layout-side-section').is_visible())
        self.assertTrue(self.page.get_by_role('button', name='Narrow menu', exact=True).is_visible())

    def test_lime_palette_coordinates_header_menu_and_table(self):
        self.page.add_script_tag(content=(ROOT / 'c4style/c4style/doctype/style_settings/style_settings.js').read_text(encoding='utf-8'))
        self.page.evaluate('formEvents.palette({doc:{palette:"Lime Fresh"},set_value:values=>{window.paletteValues=values;}})')
        self.assertEqual(self.page.evaluate('paletteValues.navbar_background'), '#3F6212')
        self.assertEqual(self.page.evaluate('paletteValues.table_header_background'), '#3F6212')
        self.assertEqual(self.page.evaluate('paletteValues.menu_background'), '#365314')

    def test_mobile_navigation_does_not_overflow_the_viewport(self):
        self.page.set_viewport_size({'width':390,'height':844})
        self.enable_app_menu()
        self.assertTrue(self.page.locator('.c4style-app-menu').is_visible())
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))


if __name__ == '__main__':
    unittest.main()
