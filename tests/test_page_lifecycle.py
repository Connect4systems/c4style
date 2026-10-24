"""Browser checks for native settings and the per-user workspace menu."""
import json
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
        self.load_fixture_assets()

    def load_fixture_assets(self, site=None):
        self.page.add_style_tag(content=(ROOT / 'c4style/public/css/c4style.css').read_text(encoding='utf-8'))
        self.page.add_script_tag(content='''
            window.__ = text => text;
            window.calls = [];
            window.frappe = {
                session: {user: 'normal@example.com'},
                boot: {c4style: {site: {menuBackground:'#123456',menuDefaultCollapsed:false,headerStyle:'pill',rowStyle:'separated',inputBorderStyle:'dashed',fieldStyle:'boxed',buttonStyle:'filled',shadowStyle:'soft',menuBehavior:'click',showScrollButtons:true,nativeDrawers:true}, personal:{}, can_manage:false}},
                pages: {}, show_alert: () => {},
                ui: {form: {on: (name, events) => { window.formEvents = events; }}},
                call(options) {
                    if (options.method === 'c4style.settings.get_palettes') {
                        if (options.callback) options.callback({message:frappe.boot.c4style.palettes});
                        return;
                    }
                    if (options.method === 'c4style.settings.get_palette') {
                        const response={message:frappe.boot.c4style.palettes[options.args.name]};
                        if (options.callback) options.callback(response);
                        return Promise.resolve(response);
                    }
                    calls.push(options.args);
                    if (options.args.scope !== 'site') sessionStorage.setItem('test-personal', JSON.stringify({...frappe.c4style.get_personal(),...JSON.parse(options.args.settings)}));
                    if (options.callback) options.callback({message:{}});
                    if (options.always) options.always();
                },
                set_route: (...args) => { window.route = args; },
                container: {add_page: () => ({})}
            };
        ''')
        self.page.evaluate('values=>frappe.boot.c4style.palettes=values', json.loads((ROOT / 'c4style/palettes.json').read_text()))
        self.page.evaluate("frappe.boot.c4style.personal=JSON.parse(sessionStorage.getItem('test-personal') || '{}')")
        self.page.evaluate('values=>Object.assign(frappe.boot.c4style.site,values)', site or {})
        self.page.add_script_tag(content=(ROOT / 'c4style/public/js/c4style.js').read_text(encoding='utf-8'))
        self.page.add_script_tag(content=(ROOT / 'c4style/public/js/desk_tools.js').read_text(encoding='utf-8'))

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.page.close()

    def load_notification_fixture(self, initial, ready=True):
        self.page.evaluate('''initial=>{
            window.notificationSummary=initial;
            window.notificationHandlers={};window.bellOscillators=0;
            frappe.realtime={socket:{},on:(name,callback)=>{
                (notificationHandlers[name] ||= []).push(callback);
            }};
            const original=frappe.call;
            frappe.call=options=>{
                if(options.method!=='c4style.notifications.get_notifications') return original(options);
                options.callback({message:structuredClone(notificationSummary)});options.always();
            };
            window.AudioContext=class {
                constructor(){this.state='suspended';this.currentTime=0;this.destination={};}
                async resume(){this.state='running';}
                createOscillator(){return {frequency:{},connect(){},start(){bellOscillators++;},stop(){}};}
                createGain(){return {gain:{setValueAtTime(){},linearRampToValueAtTime(){},exponentialRampToValueAtTime(){}},connect(){}};}
            };
        }''',initial)
        if not ready:
            self.page.evaluate('frappe.realtime.socket=null')
        self.page.add_script_tag(content=(ROOT/'c4style/public/js/notifications.js').read_text())

    def test_notification_badge_and_link_use_the_signed_in_user(self):
        self.load_notification_fixture({'unread_count':7,'notifications':[{'name':'old','subject':'Existing'}]})
        self.assertEqual(self.page.locator('[data-c4style-tools] .c4style-notification-count').inner_text(),'7')
        self.assertEqual(self.page.locator('.c4style-notification-toast').count(),0)
        self.page.locator('[data-c4style-tools]').click()
        link=self.page.locator('[data-c4style-notifications-link]')
        self.assertIn('normal%40example.com',link.get_attribute('href'))
        self.assertEqual(link.locator('.c4style-notification-count').inner_text(),'7')
        link.click()
        self.assertEqual(self.page.evaluate('route'),['List','Notification Log'])
        self.assertEqual(self.page.evaluate('frappe.route_options'),{'for_user':'normal@example.com'})

    def test_notification_listener_waits_for_socket_startup_and_installs_only_once(self):
        self.page.evaluate('''()=>{
            window.jqueryHandlers={};
            window.jQuery=()=>({on:(name,callback)=>{jqueryHandlers[name]=callback;}});
        }''')
        self.load_notification_fixture({'unread_count':0,'notifications':[]},ready=False)
        self.assertEqual(self.page.evaluate('notificationHandlers.notification?.length || 0'),0)
        self.page.evaluate('''()=>{
            frappe.realtime.socket={};
            jqueryHandlers['app_ready.c4styleNotifications']();
            jqueryHandlers['app_ready.c4styleNotifications']();
        }''')
        self.assertEqual(self.page.evaluate('notificationHandlers.notification.length'),1)

    def test_new_notification_popups_ring_once_and_clear_badge_after_read(self):
        self.load_notification_fixture({'unread_count':0,'notifications':[]})
        self.page.locator('main').click()
        self.page.evaluate('''()=>{
            notificationSummary={unread_count:1,notifications:[{name:'new',subject:'<img src=x> New alert'}]};
            notificationHandlers.notification[0]();
        }''')
        popup=self.page.locator('.c4style-notification-toast')
        self.assertTrue(popup.is_visible())
        self.assertEqual(popup.locator('img').count(),0)
        self.assertEqual(self.page.evaluate('bellOscillators'),2)
        popup.get_by_role('button',name='Dismiss').click()
        self.page.evaluate('notificationHandlers.notification[0]()')
        self.assertEqual(self.page.locator('.c4style-notification-toast').count(),0)
        self.assertEqual(self.page.evaluate('bellOscillators'),2)
        self.page.evaluate('''()=>{notificationSummary={unread_count:0,notifications:[]};notificationHandlers.indicator_hide[0]();}''')
        self.assertFalse(self.page.locator('[data-c4style-tools] .c4style-notification-count').is_visible())

    def test_notification_before_first_interaction_offers_sound_unlock(self):
        self.load_notification_fixture({'unread_count':0,'notifications':[]})
        self.page.evaluate('''()=>{
            notificationSummary={unread_count:1,notifications:[{name:'new',subject:'New alert'}]};
            notificationHandlers.notification[0]();
        }''')
        self.assertEqual(self.page.evaluate('bellOscillators'),0)
        self.page.get_by_role('button',name='Enable bell sound').click()
        self.assertEqual(self.page.evaluate('bellOscillators'),2)
        self.page.get_by_role('button',name='View notifications').click()
        self.assertEqual(self.page.evaluate('route'),['List','Notification Log'])

    def test_older_unread_items_revealed_by_reading_newer_items_do_not_alert(self):
        self.load_notification_fixture({'unread_count':30,'notifications':[
            {'name':'recent','subject':'Recent','creation':'2026-10-23 12:00:00'}]})
        self.page.evaluate('''()=>{
            notificationSummary={unread_count:10,notifications:[
                {name:'older',subject:'Older unread item',creation:'2026-10-22 12:00:00'}]};
            notificationHandlers.notification[0]();
        }''')
        self.assertEqual(self.page.locator('.c4style-notification-toast').count(),0)

    def test_disabled_native_notifications_do_not_popup_or_ring(self):
        self.load_notification_fixture({'unread_count':0,'notifications':[]})
        self.page.locator('main').click()
        self.page.evaluate('''()=>{
            frappe.boot.notification_settings={enabled:0};
            notificationSummary={unread_count:1,notifications:[{name:'new',subject:'New alert'}]};
            notificationHandlers.notification[0]();
        }''')
        self.assertEqual(self.page.evaluate('bellOscillators'),0)
        self.assertEqual(self.page.locator('.c4style-notification-toast').count(),0)

    def test_notification_count_refreshes_after_native_mark_all_read(self):
        self.page.evaluate('''()=>{
            window.jqueryHandlers={};
            window.jQuery=()=>({on:(name,callback)=>{jqueryHandlers[name]=callback;}});
        }''')
        self.load_notification_fixture({'unread_count':3,'notifications':[{'name':'old','subject':'Existing'}]})
        self.page.evaluate('''()=>{
            notificationSummary={unread_count:0,notifications:[]};
            jqueryHandlers['ajaxComplete.c4styleNotifications']({}, {status:200},
                {url:'/api/method/frappe.desk.doctype.notification_log.notification_log.mark_all_as_read'});
        }''')
        self.assertFalse(self.page.locator('[data-c4style-tools] .c4style-notification-count').is_visible())

    def test_notification_popup_is_visible_above_appearance_dialog_and_can_navigate(self):
        self.load_notification_fixture({'unread_count':0,'notifications':[]})
        self.page.locator('[data-c4style-tools]').click()
        self.page.evaluate('''()=>{
            notificationSummary={unread_count:1,notifications:[{name:'new',subject:'While tools are open'}]};
            notificationHandlers.notification[0]();
        }''')
        popup=self.page.locator('.c4style-notification-toast')
        self.assertTrue(popup.evaluate('el=>{const b=el.getBoundingClientRect();return el.contains(document.elementFromPoint(b.x+20,b.y+20));}'))
        popup.get_by_role('button',name='View notifications').click()
        self.assertEqual(self.page.get_by_role('dialog').count(),0)
        self.assertEqual(self.page.evaluate('route'),['List','Notification Log'])

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
        self.page.evaluate('async()=>await formEvents.palette({doc:{palette:"Ocean"}, set_value: values => {window.paletteValues = values;}})')
        self.assertEqual(self.page.evaluate('paletteValues.menu_background'), '#153747')
        self.assertEqual(self.page.evaluate('paletteValues.primary'), '#155E75')

    def test_database_palette_changes_are_fetched_for_settings_and_personal_picker(self):
        self.page.evaluate('''()=>{
            const colors={...frappe.boot.c4style.palettes.Ocean,primary:'#123ABC'};
            frappe.boot.c4style.palettes={'Company theme':colors};
            frappe.c4style.apply_theme({allowUserThemes:true});
        }''')
        self.page.add_script_tag(content=(ROOT / 'c4style/c4style/doctype/style_settings/style_settings.js').read_text())
        self.page.evaluate('''async()=>await formEvents.palette({doc:{palette:'Company theme'},
            set_value:values=>{window.paletteValues=values;}})''')
        self.assertEqual(self.page.evaluate('paletteValues.primary'),'#123ABC')
        self.page.get_by_role('button',name='Appearance tools',exact=True).click()
        self.page.get_by_role('button',name='Choose my theme',exact=True).click()
        self.assertEqual(self.page.get_by_role('button',name='Ocean',exact=True).count(),0)
        self.page.get_by_role('button',name='Company theme',exact=True).click()
        self.assertEqual(self.page.evaluate('frappe.c4style.get_theme().primary'),'#123ABC')

    def test_breadcrumbs_allow_unresolved_startup_route(self):
        self.page.evaluate('''() => {
            document.querySelector('.navbar').innerHTML='<div class="container"></div>';
            frappe.get_route=()=>null;
            frappe.c4style.sync_tools();
        }''')
        self.assertEqual(self.page.locator('.c4style-breadcrumbs').inner_text(), 'Home')

    def test_theme_is_loaded_when_desk_boot_arrives_after_assets(self):
        self.page.reload()
        self.page.add_script_tag(content='''
            window.__=text=>text;
            window.frappe={boot:{},pages:{}};
            window.jQuery=()=>({on:(event,callback)=>{window.deskReady=callback;}});
        ''')
        self.page.add_script_tag(content=(ROOT / 'c4style/public/js/c4style.js').read_text())
        self.page.evaluate('''() => {
            frappe.boot.c4style={site:{primary:'#831843',menuDefaultCollapsed:false,
                enableAnnouncement:true,announcementText:'Ready',nativeDrawers:true},
                personal:{direction:'rtl'},can_manage:false};
            deskReady();
        }''')
        self.assertEqual(self.page.evaluate('frappe.c4style.get_theme().primary'), '#831843')
        self.assertEqual(self.page.locator('html').get_attribute('dir'), 'rtl')
        self.assertFalse(self.page.evaluate('frappe.c4style.get_personal().menuCollapsed'))

    def test_all_palette_colors_match_server_defaults(self):
        import json
        expected = json.loads((ROOT / 'c4style/palettes.json').read_text())
        self.assertEqual(self.page.evaluate('frappe.c4style.palettes'), expected)
        for name in expected:
            values = self.page.evaluate('name=>frappe.c4style.palette_settings(name)', name)
            self.assertEqual(len(values), len(expected[name]))
            self.assertTrue(all(values.values()))

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

    def test_obsolete_menu_switch_cannot_disable_the_edge_menu(self):
        self.enable_app_menu()
        self.page.evaluate('frappe.c4style.apply_theme({persistentMenu:false})')
        self.assertTrue(self.page.locator('.c4style-app-menu').is_visible())
        self.assertFalse(self.page.locator('.layout-side-section').is_visible())
        self.assertAlmostEqual(self.page.locator('.c4style-app-menu').bounding_box()['x'], 0, delta=1)

    def test_lime_palette_coordinates_header_menu_and_table(self):
        self.page.add_script_tag(content=(ROOT / 'c4style/c4style/doctype/style_settings/style_settings.js').read_text(encoding='utf-8'))
        self.page.evaluate('async()=>await formEvents.palette({doc:{palette:"Lime Fresh"},set_value:values=>{window.paletteValues=values;}})')
        self.assertEqual(self.page.evaluate('paletteValues.navbar_background'), '#3F6212')
        self.assertEqual(self.page.evaluate('paletteValues.table_header_background'), '#3F6212')
        self.assertEqual(self.page.evaluate('paletteValues.menu_background'), '#365314')

    def test_mobile_navigation_does_not_overflow_the_viewport(self):
        self.page.set_viewport_size({'width':390,'height':844})
        self.enable_app_menu()
        self.assertTrue(self.page.locator('.c4style-app-menu').is_visible())
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))

    def test_capsule_header_and_dashed_inputs_match_component_settings(self):
        self.page.evaluate('''() => {
            document.body.insertAdjacentHTML('beforeend','<input class="form-control" aria-label="Reference input"><button class="btn btn-default" id="secondary-test">Filter</button>');
            frappe.c4style.apply_theme({secondaryBackground:'#A58F7A',secondaryText:'#FFFFFF'});
        }''')
        self.assertEqual(self.page.locator('.navbar').evaluate('(el) => getComputedStyle(el).borderRadius'), '999px')
        self.assertEqual(self.page.get_by_role('textbox',name='Reference input').evaluate('(el) => getComputedStyle(el).borderTopStyle'), 'dashed')
        self.assertEqual(self.page.locator('#secondary-test').evaluate('(el) => getComputedStyle(el).backgroundColor'), 'rgb(165, 143, 122)')

    def test_announcement_is_plain_text_and_can_be_dismissed(self):
        self.page.evaluate('frappe.c4style.apply_theme({enableAnnouncement:true,announcementText:"<b>Test announcement</b>",announcementSpeed:18})')
        self.assertEqual(self.page.locator('.c4style-announcement-message').inner_text(), '<b>Test announcement</b>')
        self.assertEqual(self.page.locator('.c4style-announcement b').count(),0)
        self.page.get_by_role('button',name='Dismiss announcement').click()
        self.assertEqual(self.page.locator('.c4style-announcement').count(),0)
        self.page.evaluate('frappe.c4style.sync_tools()')
        self.assertEqual(self.page.locator('.c4style-announcement').count(),0)

    def test_short_announcement_moves_and_uses_its_font_size(self):
        self.page.evaluate('frappe.c4style.apply_theme({enableAnnouncement:true,announcementText:"Visible now",announcementSpeed:25,announcementFontSize:26})')
        message = self.page.locator('.c4style-announcement-message')
        self.assertEqual(message.evaluate('(el)=>getComputedStyle(el).animationName'), 'c4style-announcement-scroll')
        self.assertEqual(message.evaluate('(el)=>getComputedStyle(el).fontSize'), '26px')
        positions = [message.evaluate('(el,t)=>{const a=el.getAnimations()[0];a.pause();a.currentTime=t;return el.getBoundingClientRect().left}', t) for t in (0,12500)]
        self.assertGreater(abs(positions[1]-positions[0]), 20)
        self.assertTrue(message.evaluate('el=>{const a=el.getBoundingClientRect(),b=el.parentElement.getBoundingClientRect();return a.left>=b.left && a.top>=b.top;}'))

    def test_long_announcement_moves_without_leaving_an_empty_viewport(self):
        self.page.evaluate('frappe.c4style.apply_theme({enableAnnouncement:true,announcementText:"Long announcement ".repeat(40),announcementSpeed:25})')
        message = self.page.locator('.c4style-announcement-message')
        for time in (0, 12500, 25000, 37500):
            self.assertTrue(message.evaluate('''(el,time)=>{
                const animation=el.getAnimations()[0];animation.pause();animation.currentTime=time;
                const a=el.getBoundingClientRect(),b=el.parentElement.getBoundingClientRect();
                return a.left<=b.left+1 && a.right>=b.right-1;
            }''',time))

    def test_normal_user_tools_do_not_offer_shared_theme_edits(self):
        self.page.get_by_role('button',name='Appearance tools',exact=True).click()
        self.assertTrue(self.page.get_by_role('dialog',name='Appearance tools').is_visible())
        self.assertEqual(self.page.get_by_role('button',name='Choose site theme').count(),0)
        self.assertEqual(self.page.get_by_role('button',name='Style Settings',exact=True).count(),0)
        self.assertTrue(self.page.get_by_role('button',name='My sticky notes').is_visible())
        for name in ('Switch text direction', 'Expand / narrow workspace', 'Expand / narrow menu'):
            self.assertEqual(self.page.get_by_role('dialog').get_by_role('button', name=name, exact=True).count(), 0)
        self.page.keyboard.press('Escape')
        self.assertEqual(self.page.get_by_role('dialog').count(),0)

    def test_manager_palette_picker_requires_confirmation(self):
        self.page.evaluate('''() => {
            frappe.boot.c4style.can_manage=true;
            frappe.confirm=(message,confirm)=>{window.pendingConfirmation=confirm;};
        }''')
        self.page.get_by_role('button',name='Appearance tools',exact=True).click()
        self.page.get_by_role('button',name='Choose site theme',exact=True).click()
        self.page.get_by_role('button',name='Lime Fresh',exact=True).click()
        self.assertEqual(self.page.evaluate('calls.length'),0)
        self.page.evaluate('pendingConfirmation()')
        self.assertEqual(self.page.evaluate('calls[0].scope'),'site')
        self.assertEqual(self.page.evaluate('calls[0].palette'),'Lime Fresh')

    def test_personal_theme_choice_restores_after_refresh_and_obeys_site_switch(self):
        self.page.evaluate('frappe.c4style.apply_theme({allowUserThemes:true,primary:"#112233"})')
        self.page.get_by_role('button',name='Appearance tools',exact=True).click()
        self.page.get_by_role('button',name='Choose my theme',exact=True).click()
        self.page.get_by_role('button',name='Ocean',exact=True).click()
        self.assertEqual(self.page.evaluate('frappe.c4style.get_theme().primary'), '#155E75')
        self.assertEqual(self.page.evaluate('frappe.c4style.get_site_theme().primary'), '#112233')
        self.assertEqual(self.page.evaluate('JSON.parse(calls[0].settings)'), {'themePalette':'Ocean'})
        self.assertIsNone(self.page.evaluate('calls[0].scope'))
        self.page.reload()
        self.load_fixture_assets({'allowUserThemes':True,'primary':'#112233'})
        self.assertEqual(self.page.evaluate('frappe.c4style.get_theme().primary'), '#155E75')
        self.page.evaluate('frappe.c4style.apply_theme({allowUserThemes:false})')
        self.assertEqual(self.page.evaluate('frappe.c4style.get_theme().primary'), '#112233')
        self.page.get_by_role('button',name='Appearance tools',exact=True).click()
        self.assertEqual(self.page.get_by_role('button',name='Choose my theme',exact=True).count(),0)
        self.page.keyboard.press('Escape')
        self.page.evaluate('frappe.c4style.apply_theme({allowUserThemes:true})')
        self.assertEqual(self.page.evaluate('frappe.c4style.get_theme().primary'), '#155E75')
        self.page.get_by_role('button',name='Appearance tools',exact=True).click()
        self.page.get_by_role('button',name='Choose my theme',exact=True).click()
        self.page.get_by_role('button',name='Use site theme',exact=True).click()
        self.assertEqual(self.page.evaluate('frappe.c4style.get_theme().primary'), '#112233')

    def test_failed_personal_theme_save_restores_site_colors(self):
        self.page.evaluate('frappe.c4style.apply_theme({allowUserThemes:true,primary:"#112233"})')
        self.page.evaluate('()=>{frappe.call=options=>{if(options.method === "c4style.settings.get_palettes"){options.callback({message:frappe.boot.c4style.palettes});return;}options.error();options.always();};}')
        self.page.get_by_role('button',name='Appearance tools',exact=True).click()
        self.page.get_by_role('button',name='Choose my theme',exact=True).click()
        self.page.get_by_role('button',name='Ocean',exact=True).click()
        self.assertEqual(self.page.evaluate('frappe.c4style.get_theme().primary'), '#112233')
        self.assertTrue(self.page.get_by_role('button',name='Ocean',exact=True).is_enabled())

    def test_app_launcher_filters_allowed_workspaces(self):
        self.enable_app_menu()
        self.page.get_by_role('button',name='Appearance tools',exact=True).click()
        self.page.get_by_role('button',name='Apps and workspaces',exact=True).click()
        self.page.get_by_role('searchbox',name='Find a workspace').fill('private')
        self.assertEqual(self.page.locator('.c4style-app-tile:visible').count(),1)
        self.assertEqual(self.page.locator('.c4style-app-tile:visible').get_attribute('href'),'/app/private/private-notes')

    def test_sticky_notes_are_saved_only_on_explicit_save(self):
        self.page.get_by_role('button',name='Appearance tools',exact=True).click()
        self.page.get_by_role('button',name='My sticky notes',exact=True).click()
        self.page.get_by_role('button',name='Add note').click()
        self.page.get_by_role('textbox',name='Note text').fill('Call supplier <script>hello</script>')
        self.assertEqual(self.page.evaluate('calls.length'),0)
        self.page.get_by_role('button',name='Save notes').click()
        self.assertEqual(self.page.evaluate('JSON.parse(calls[0].settings).notes[0].text'),'Call supplier <script>hello</script>')

    def test_direct_note_save_does_not_save_other_unfinished_notes(self):
        self.page.get_by_role('button',name='Appearance tools',exact=True).click()
        self.page.get_by_role('button',name='My sticky notes',exact=True).click()
        self.page.get_by_role('button',name='Add note').click()
        self.page.get_by_role('button',name='Add note').click()
        notes = self.page.locator('.c4style-notes-grid .c4style-note')
        notes.nth(0).get_by_role('textbox').fill('Save only this')
        notes.nth(1).get_by_role('textbox').fill('Unfinished draft')
        self.assertEqual(notes.nth(0).locator('button').count(), 3)
        notes.nth(0).get_by_role('button',name='Save note',exact=True).click()
        self.assertEqual(self.page.evaluate('frappe.c4style.get_personal().notes.map(note=>note.text)'), ['Save only this'])

    def test_note_minimize_refresh_restore_save_and_delete(self):
        self.page.evaluate('frappe.c4style.save_personal("notes",[{id:"one",text:"Saved reminder",color:"mint"}])')
        note = self.page.locator('.c4style-note-window')
        self.assertEqual(note.locator('button').count(), 3)
        note.get_by_role('textbox').fill('Unsaved draft')
        note.get_by_role('button',name='Minimize',exact=True).click()
        self.assertFalse(note.get_by_role('textbox',include_hidden=True).is_visible())
        self.assertEqual(self.page.evaluate('frappe.c4style.get_personal().notes[0].text'), 'Saved reminder')
        note.get_by_role('button',name='Restore',exact=True).click()
        self.assertEqual(note.get_by_role('textbox').input_value(), 'Unsaved draft')
        note.get_by_role('button',name='Save note',exact=True).click()
        note.get_by_role('button',name='Minimize',exact=True).click()
        self.page.reload()
        self.load_fixture_assets()
        note = self.page.locator('.c4style-note-window')
        self.assertTrue(note.is_visible())
        self.assertTrue(note.get_by_role('button',name='Restore',exact=True).is_visible())
        note.get_by_role('button',name='Restore',exact=True).click()
        self.assertEqual(note.get_by_role('textbox').input_value(), 'Unsaved draft')
        note.get_by_role('button',name='Delete note',exact=True).click()
        self.assertEqual(self.page.locator('.c4style-note-window').count(), 0)
        self.page.reload()
        self.load_fixture_assets()
        self.assertEqual(self.page.locator('.c4style-note-window').count(), 0)

    def test_failed_note_minimize_and_delete_preserve_the_note(self):
        self.page.evaluate('frappe.c4style.save_personal("notes",[{id:"one",text:"Keep this",color:"mint"}])')
        self.page.evaluate('()=>{frappe.call=options=>{if(options.method === "c4style.settings.get_palettes"){options.callback({message:frappe.boot.c4style.palettes});return;}options.error();options.always();};}')
        note = self.page.locator('.c4style-note-window')
        note.get_by_role('button',name='Minimize',exact=True).click()
        self.assertTrue(note.get_by_role('textbox').is_visible())
        note.get_by_role('button',name='Delete note',exact=True).click()
        self.assertEqual(note.get_by_role('textbox').input_value(), 'Keep this')
        note.get_by_role('textbox').fill('Keep this draft too')
        note.get_by_role('button',name='Save note',exact=True).click()
        self.assertEqual(note.get_by_role('textbox').input_value(), 'Keep this draft too')
        self.assertEqual(self.page.evaluate('frappe.c4style.get_personal().notes[0].text'), 'Keep this')

    def test_editor_keeps_saved_note_when_delete_or_minimize_fails(self):
        self.page.evaluate('frappe.c4style.save_personal("notes",[{id:"one",text:"Keep this",color:"mint"}])')
        self.page.get_by_role('button',name='Appearance tools',exact=True).click()
        self.page.get_by_role('button',name='My sticky notes',exact=True).click()
        self.page.evaluate('()=>{frappe.call=options=>{if(options.method === "c4style.settings.get_palettes"){options.callback({message:frappe.boot.c4style.palettes});return;}options.error();options.always();};}')
        editor = self.page.get_by_role('dialog',name='My sticky notes')
        editor.get_by_role('button',name='Minimize',exact=True).click()
        self.assertTrue(editor.get_by_role('textbox').is_visible())
        editor.get_by_role('button',name='Delete note',exact=True).click()
        self.assertEqual(editor.get_by_role('textbox').input_value(), 'Keep this')

    def test_list_header_keeps_space_before_first_record_and_sort_remains_clickable(self):
        self.page.evaluate('''()=>{
            const list=document.createElement('div');list.className='frappe-list';
            list.style.cssText='height:220px;overflow:auto';
            list.innerHTML='<div class="level list-row-head"><button id="sort-column">ID</button></div>'+
                '<div class="list-row-container"><div class="list-row">First record</div></div>'+
                '<div style="height:800px"></div>';
            document.querySelector('main').appendChild(list);
            document.querySelector('#sort-column').onclick=()=>{window.sorted=true;};
        }''')
        for style in ('separated','flat'):
            self.page.evaluate('value=>document.body.dataset.rowStyle=value',style)
            self.assertTrue(self.page.evaluate('''()=>{
                const header=document.querySelector('.list-row-head').getBoundingClientRect();
                const first=document.querySelector('.list-row-container').getBoundingClientRect();
                return first.top >= header.bottom + 12;
            }'''))
        self.page.locator('#sort-column').click()
        self.assertTrue(self.page.evaluate('sorted'))

    def test_notification_list_delete_asks_confirmation_and_refreshes(self):
        self.page.evaluate('''()=>{
            frappe.listview_settings={'Notification Log':{onload:()=>{window.originalLoaded=true;}}};
            window.listview={page:{add_action_item:(label,action)=>{window.deleteAction=action;}},
                get_checked_items:()=>[{name:'alert-one'},{name:'alert-two'}],
                refresh:()=>{window.listRefreshed=true;}};
            frappe.confirm=(text,callback)=>{window.confirmDelete=callback;};
            frappe.call=options=>{window.deleteRequest=options;options.callback({message:{deleted:2}});};
            frappe.c4style.refresh_notifications=()=>{window.badgeRefreshed=true;};
        }''')
        self.page.add_script_tag(content=(ROOT/'c4style/public/js/notification_log_list.js').read_text())
        self.page.evaluate("frappe.listview_settings['Notification Log'].onload(listview);deleteAction()")
        self.assertTrue(self.page.evaluate('originalLoaded'))
        self.assertFalse(self.page.evaluate('Boolean(window.deleteRequest)'))
        self.page.evaluate('confirmDelete()')
        self.assertEqual(self.page.evaluate('deleteRequest.method'),'c4style.notifications.delete_notifications')
        self.assertEqual(self.page.evaluate('JSON.parse(deleteRequest.args.names)'),['alert-one','alert-two'])
        self.assertTrue(self.page.evaluate('listRefreshed && badgeRefreshed'))

    def test_grouping_loaded_rows_preserves_links_selection_and_ungroup_order(self):
        self.page.evaluate('''() => {
            const result=document.createElement('div');result.id='group-result';
            const data=[{name:'A',item_group:'Hardware'},{name:'B',item_group:'Services'},{name:'C',item_group:'Hardware'}];
            result.innerHTML=data.map(doc=>`<div class="list-row-container"><input type="checkbox" data-name="${doc.name}"><a href="/app/item/${doc.name}">${doc.name}</a></div>`).join('');
            document.body.appendChild(result);
            window.cur_list={$result:[result],data,columns:[{df:{fieldname:'item_group',fieldtype:'Link',label:'Item group'}}]};
            frappe.c4style.sync_tools();
        }''')
        self.page.get_by_role('combobox',name='Group loaded rows').select_option('item_group')
        self.assertEqual(self.page.locator('.c4style-list-group').count(),2)
        self.page.get_by_role('button',name='Hardware (2)',exact=True).click()
        self.assertEqual(self.page.locator('#group-result .list-row-container:visible').count(),1)
        self.page.get_by_role('combobox',name='Group loaded rows').select_option('')
        self.assertEqual(self.page.locator('#group-result a').all_text_contents(),['A','B','C'])
        self.assertEqual(self.page.locator('#group-result input[type="checkbox"]').count(),3)

    def test_hover_mode_expands_collapsed_menu_without_changing_saved_preference(self):
        self.enable_app_menu()
        self.page.evaluate('frappe.c4style.apply_theme({menuBehavior:"hover"})')
        self.page.get_by_role('button',name='Narrow menu',exact=True).click()
        self.page.mouse.click(900,500)
        self.assertFalse(self.page.locator('.c4style-app-menu .sidebar-item-label').first.is_visible())
        self.page.locator('.c4style-brand').hover()
        self.assertTrue(self.page.locator('.c4style-app-menu .sidebar-item-label').first.is_visible())
        self.assertTrue(self.page.evaluate('frappe.c4style.get_personal().menuCollapsed'))

    def test_native_user_drawer_opens_and_closes_with_backdrop(self):
        self.page.add_style_tag(content='.dropdown-menu{display:none}.dropdown-menu.show{display:block}.navbar{perspective:3200px}.sticky-top{position:sticky;z-index:1020}')
        self.page.evaluate('''() => {
            const navbar=document.querySelector('.navbar');
            const main=document.createElement('div');main.className='main-section';
            const sticky=document.createElement('div');sticky.className='sticky-top';
            navbar.before(main);main.appendChild(sticky);sticky.appendChild(navbar);
        }''')
        self.page.evaluate('''() => {
            const dropdown=document.createElement('div');dropdown.className='dropdown-navbar-user';
            dropdown.innerHTML='<button data-toggle="dropdown" aria-label="User Menu">User</button><div class="dropdown-menu" id="toolbar-user"><a class="dropdown-item" href="/app/user">My profile</a></div>';
            document.querySelector('.navbar').appendChild(dropdown);
            dropdown.querySelector('button').addEventListener('click',()=>{dropdown.classList.toggle('show');dropdown.querySelector('.dropdown-menu').classList.toggle('show');});
            frappe.c4style.sync_tools();
        }''')
        self.page.get_by_role('button',name='User Menu',exact=True).click()
        self.page.wait_for_selector('.c4style-drawer-backdrop')
        box=self.page.locator('#toolbar-user').bounding_box()
        self.assertAlmostEqual(box['x']+box['width'],self.page.viewport_size['width'],delta=1)
        self.assertAlmostEqual(box['height'],self.page.viewport_size['height'],delta=1)
        self.assertAlmostEqual(box['y'],0,delta=1)
        self.assertTrue(self.page.locator('#toolbar-user').evaluate('(el) => {const b=el.getBoundingClientRect();return el.contains(document.elementFromPoint(b.x+20,b.y+20));}'))
        self.page.locator('.c4style-drawer-backdrop').click(position={'x':20,'y':200})
        self.page.wait_for_selector('.c4style-drawer-backdrop',state='detached')
        self.assertFalse(self.page.get_by_role('link',name='My profile').is_visible())

    def test_scroll_buttons_scroll_page_in_reduced_motion(self):
        self.page.emulate_media(reduced_motion='reduce')
        self.page.evaluate('document.body.style.minHeight="3000px"')
        self.page.get_by_role('button',name='Scroll to bottom',exact=True).click()
        self.assertGreater(self.page.evaluate('window.scrollY'),1000)
        self.page.get_by_role('button',name='Scroll to top',exact=True).click()
        self.assertEqual(self.page.evaluate('window.scrollY'),0)

    def test_saved_notes_open_automatically_and_can_be_moved_saved_and_deleted(self):
        self.page.get_by_role('button',name='Appearance tools',exact=True).click()
        self.page.get_by_role('button',name='My sticky notes',exact=True).click()
        self.page.get_by_role('button',name='Add note').click()
        self.page.get_by_role('textbox',name='Note text',exact=True).fill('Private reminder')
        self.page.get_by_role('button',name='Save notes',exact=True).click()
        self.page.get_by_role('dialog',name='My sticky notes').get_by_role('button',name='Close',exact=True).click()
        window=self.page.locator('.c4style-note-window')
        self.assertTrue(window.is_visible())
        before=window.bounding_box()
        self.page.get_by_role('button',name='Move note with arrow keys or drag').focus()
        self.page.keyboard.press('ArrowRight')
        self.assertAlmostEqual(window.bounding_box()['x'],before['x']+10,delta=1)
        self.page.get_by_role('textbox',name='Pinned note text',exact=True).fill('Updated reminder')
        self.page.get_by_role('button',name='Save note',exact=True).click()
        self.assertEqual(self.page.evaluate('JSON.parse(calls[1].settings).notes[0].text'),'Updated reminder')
        self.page.get_by_role('button',name='Delete note',exact=True).click()
        self.assertEqual(self.page.locator('.c4style-note-window').count(),0)

    def test_menu_offset_overrides_frappe_important_body_reset(self):
        self.page.add_style_tag(content='body {padding:0!important}')
        self.enable_app_menu()
        self.assertEqual(self.page.locator('body').evaluate('(el)=>getComputedStyle(el).paddingInlineStart'),'236px')
        self.page.get_by_role('button',name='Narrow menu',exact=True).click()
        self.assertEqual(self.page.locator('body').evaluate('(el)=>getComputedStyle(el).paddingInlineStart'),'72px')


if __name__ == '__main__':
    unittest.main()
