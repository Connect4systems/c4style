"""Authorized test-site audit. Uses an existing Playwright session; contains no credentials.

Example: python -B tests/run_live_review.py --base-url https://test.example.com \
    --session-file /temporary/session.json --local-assets
The caller is responsible for restoring site settings and removing seeded records.
"""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--session-file', required=True)
    parser.add_argument('--local-assets', action='store_true')
    parser.add_argument('--output', default=str(ROOT / 'artifacts/live-review'))
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    results, errors = [], []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=args.session_file, viewport={'width': 1440, 'height': 1000})
        if args.local_assets:
            def asset(route):
                relative = route.request.url.split('/assets/c4style/', 1)[1].split('?', 1)[0]
                path = (ROOT / 'c4style/public' / relative).resolve()
                public = (ROOT / 'c4style/public').resolve()
                if path.is_relative_to(public) and path.is_file():
                    route.fulfill(body=path.read_bytes(), content_type='text/css; charset=utf-8' if path.suffix == '.css' else 'application/javascript; charset=utf-8')
                else:
                    route.continue_()
            context.route('**/assets/c4style/**', asset)
        page = context.new_page()
        page.set_default_timeout(8000)
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(args.base_url.rstrip('/') + '/app/item', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_function('window.frappe && frappe.boot && frappe.boot.c4style && window.cur_list && cur_list.data', timeout=60000)

        def case(name, action):
            try:
                detail = action()
                results.append(dict(name=name, passed=True, detail=detail))
                print('PASS ' + name, flush=True)
            except Exception as exc:
                results.append(dict(name=name, passed=False, error=str(exc)[:1500]))
                print('FAIL ' + name + ': ' + str(exc)[:250], flush=True)
            (output / 'report.json').write_text(json.dumps(dict(local_asset_override=args.local_assets, checks=results, browser_errors=errors), indent=2), encoding='utf-8')

        def save_site(values):
            return page.evaluate('''async settings => {
                const response = await frappe.call({method:'c4style.settings.save_settings',args:{scope:'site',settings:JSON.stringify(settings)}});
                frappe.c4style.apply_theme(response.message); return response.message;
            }''', values)

        def save_personal(values):
            page.evaluate('''async settings => {
                await frappe.call({method:'c4style.settings.save_settings',args:{settings:JSON.stringify(settings)}});
            }''', values)

        def native_settings():
            page.evaluate('frappe.set_route("Form","Style Settings")')
            page.wait_for_function('window.cur_frm && cur_frm.doctype === "Style Settings" && cur_frm.doc', timeout=30000)
            page.evaluate('''async()=>{
                await cur_frm.set_value('palette','Lime Fresh');
                await cur_frm.set_value({header_style:'pill',row_style:'separated',input_border_style:'dashed',field_style:'boxed',button_style:'filled',font_family:'arial',menu_behavior:'hover',show_scroll_buttons:1,native_drawers:1});
                await cur_frm.save();
            }''')
            page.wait_for_function('frappe.c4style.get_theme().primary === "#3F6212"')
            tabs = page.locator('.form-tabs .nav-link')
            assert tabs.count() == 5
            for index in range(5):
                tabs.nth(index).click()
            assert page.locator('.c4style-theme-preview').is_visible()
            page.screenshot(path=str(output / '06-live-settings-preview.png'), full_page=True)
            return dict(tabs=5, fields=page.evaluate('cur_frm.meta.fields.length'))
        case('native Single form saves and all five tabs open', native_settings)

        def palettes():
            names = page.evaluate('Object.keys(frappe.c4style.palettes)')
            for name in names:
                page.evaluate('''async name=>{
                    const response=await frappe.call({method:'c4style.settings.save_settings',args:{scope:'site',palette:name,settings:JSON.stringify(frappe.c4style.palette_settings(name))}});
                    frappe.c4style.apply_theme(response.message);
                }''', name)
                assert page.evaluate('document.documentElement.style.getPropertyValue("--primary")') == page.evaluate('name=>frappe.c4style.palettes[name].primary', name)
            return dict(palettes=len(names))
        case('every built-in palette persists through the real server', palettes)

        def components():
            options = dict(headerStyle=['pill', 'flat'], rowStyle=['separated', 'flat'], inputBorderStyle=['dashed', 'solid', 'none'], fieldStyle=['boxed', 'underline'], buttonStyle=['filled', 'outline'], shadowStyle=['soft', 'none'], menuBehavior=['hover', 'click'])
            count = 0
            for key, values in options.items():
                for value in values:
                    saved = save_site({key: value})
                    assert saved[key] == value
                    assert page.evaluate('key=>document.body.dataset[key]', key) == value
                    count += 1
            for font in ['system', 'arial', 'tahoma', 'georgia']:
                save_site({'fontFamily': font})
                assert page.evaluate('document.documentElement.style.getPropertyValue("--font-stack")')
            for size in [12, 18]:
                save_site({'fontSize': size})
                assert page.locator('html').evaluate('(el)=>getComputedStyle(el).fontSize') == str(size) + 'px'
            for radius in [2, 16]:
                save_site({'radius': radius})
                assert page.evaluate('document.documentElement.style.getPropertyValue("--c4style-radius")') == str(radius) + 'px'
            return dict(component_choices=count, fonts=4, font_sizes=2, radii=2)
        case('all component styles and typography choices persist', components)

        # Restore a consistent visual reference between independent scenarios.
        baseline = page.evaluate('frappe.c4style.palette_settings("Lime Fresh")')
        baseline.update(headerStyle='pill', rowStyle='separated', inputBorderStyle='dashed', fieldStyle='boxed', buttonStyle='filled', shadowStyle='soft', menuBehavior='click', fontFamily='arial', fontSize=14, radius=10, nativeDrawers=True, showScrollButtons=True)
        save_site(baseline)
        save_personal({'direction': 'ltr', 'workspaceWide': True, 'menuCollapsed': True})
        page.reload(wait_until='domcontentloaded', timeout=60000)
        page.wait_for_function('window.cur_list && cur_list.doctype==="Item" && cur_list.data.length>=6', timeout=30000)

        def list_layout():
            page.mouse.move(800, 900)
            header = page.locator('.navbar').bounding_box()
            menu = page.locator('.c4style-app-menu').bounding_box()
            assert header['x'] >= menu['x'] + menu['width']
            assert page.locator('.c4style-breadcrumbs').is_visible()
            assert page.locator('.list-row-container').count() >= 6
            assert page.locator('.list-row-container').first.evaluate('(el)=>getComputedStyle(el).borderTopColor') != 'rgba(0, 0, 0, 0)'
            footer = page.locator('.c4style-menu-controls').bounding_box()
            assert footer['y'] + footer['height'] <= page.viewport_size['height'] + 1
            assert page.locator('.c4style-app-menu .icon').first.evaluate('(el)=>getComputedStyle(el).getPropertyValue("--icon-stroke").trim()') == '#F7FEE7'
            page.screenshot(path=str(output / '07-live-reference-item-list.png'), full_page=True)
            return dict(rows=page.locator('.list-row-container').count(), menu_width=menu['width'], header_x=header['x'])
        case('real Item list matches reference spacing, cards and icon rail', list_layout)

        def grouping():
            selector = page.get_by_role('combobox', name='Group loaded rows')
            selector.select_option('item_group')
            assert page.locator('.c4style-list-group').count() >= 2
            first = page.locator('.c4style-list-group').first
            first.click()
            assert first.get_attribute('aria-expanded') == 'false'
            first.click()
            selector.select_option('')
            checkbox = page.locator('.list-row-checkbox').first
            checkbox.check()
            assert checkbox.is_checked()
            checkbox.uncheck()
            return dict(groups=2, native_selection=True)
        case('grouping, expanding and native row selection', grouping)

        def density():
            save_site({'density': 'comfortable'})
            normal = page.locator('.list-row').first.bounding_box()['height']
            save_site({'density': 'compact'})
            compact = page.locator('.list-row').first.bounding_box()['height']
            assert compact < normal, (normal, compact)
            save_site({'density': 'comfortable'})
            return dict(comfortable=normal, compact=compact)
        case('compact density actually reduces native row height', density)

        def drawers():
            for selector in ['.dropdown-navbar-user', '.dropdown-notifications']:
                page.locator(selector + ' > button').click()
                page.wait_for_selector('.c4style-drawer-backdrop')
                menu = page.locator(selector + ' > .dropdown-menu')
                box = menu.bounding_box()
                assert abs(box['y']) < 1 and abs(box['height'] - page.viewport_size['height']) < 1, box
                assert menu.evaluate('(el)=>{const b=el.getBoundingClientRect();return el.contains(document.elementFromPoint(b.x+20,b.y+20));}')
                menu.get_by_role('button', name='Close', exact=True).click()
                page.wait_for_selector('.c4style-drawer-backdrop', state='detached')
            return dict(drawers=2, backdrop_below_drawer=True)
        case('real Bootstrap notification and user drawers remain clickable', drawers)

        def announcement():
            save_site({'enableAnnouncement': True, 'announcementText': 'ORO - C4Style live comparison', 'announcementSpeed': 24})
            assert page.locator('.c4style-announcement').is_visible()
            page.screenshot(path=str(output / '08-live-announcement.png'), full_page=True)
            page.get_by_role('button', name='Dismiss announcement').click()
            assert page.locator('.c4style-announcement').count() == 0
            save_site({'enableAnnouncement': False})
            return dict(show=True, dismiss=True)
        case('announcement rendering and dismissal', announcement)

        def tools_and_notes():
            page.get_by_role('button', name='Appearance tools', exact=True).click()
            page.get_by_role('button', name='Choose site theme', exact=True).click()
            assert page.locator('.c4style-palette-choice').count() == 17
            page.keyboard.press('Escape')
            page.locator('.c4style-brand').click()
            assert page.get_by_role('dialog', name='Apps and workspaces').is_visible()
            page.get_by_role('searchbox', name='Find a workspace').fill('stock')
            assert page.locator('.c4style-app-tile:visible').count() >= 1
            page.keyboard.press('Escape')
            page.get_by_role('button', name='Appearance tools', exact=True).click()
            page.get_by_role('button', name='My sticky notes', exact=True).click()
            page.get_by_role('button', name='Add note').click()
            page.get_by_role('textbox', name='Note text', exact=True).last.fill('C4Style live QA note - remove after testing')
            page.get_by_role('button', name='Save notes', exact=True).click()
            page.wait_for_timeout(400)
            page.get_by_role('dialog', name='My sticky notes').get_by_role('button', name='Close', exact=True).click()
            assert page.locator('.c4style-note-window').count() >= 1
            handle = page.get_by_role('button', name='Move note with arrow keys or drag').last
            handle.focus()
            before = page.locator('.c4style-note-window').last.bounding_box()
            page.keyboard.press('ArrowRight')
            after = page.locator('.c4style-note-window').last.bounding_box()
            assert after['x'] > before['x']
            page.get_by_role('button', name='Delete note', exact=True).last.click()
            return dict(palettes=17, launcher=True, notes_saved_and_pinned=True)
        case('actual theme picker, searchable launcher and saved pinned note', tools_and_notes)

        def rtl_and_mobile():
            page.get_by_role('button', name='Switch to right-to-left').click()
            page.wait_for_function('document.documentElement.dir === "rtl"')
            rail = page.locator('.c4style-app-menu').bounding_box()
            header = page.locator('.navbar').bounding_box()
            assert header['x'] + header['width'] <= rail['x'] + 1
            page.screenshot(path=str(output / '09-live-rtl-item-list.png'), full_page=True)
            page.get_by_role('button', name='Switch to left-to-right').click()
            page.set_viewport_size({'width': 390, 'height': 844})
            page.wait_for_timeout(200)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
            page.screenshot(path=str(output / '10-live-mobile.png'), full_page=True)
            page.set_viewport_size({'width': 1440, 'height': 1000})
            return dict(rtl=True, mobile_width=390)
        case('RTL placement and real mobile viewport', rtl_and_mobile)

        def persistence():
            save_personal({'menuCollapsed': True, 'workspaceWide': True, 'direction': 'ltr'})
            page.reload(wait_until='domcontentloaded', timeout=60000)
            page.wait_for_function('window.frappe && frappe.boot && frappe.boot.c4style', timeout=30000)
            personal = page.evaluate('frappe.boot.c4style.personal')
            assert personal['workspaceWide'] and personal['menuCollapsed'] and personal['direction'] == 'ltr'
            return dict(reload_restored=True)
        case('preferences persist through authenticated reload', persistence)

        summary = dict(base_url=args.base_url, local_asset_override=args.local_assets, checks=results, browser_errors=errors)
        (output / 'report.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
        browser.close()
        if errors or any(not result['passed'] for result in results):
            raise SystemExit(1)


if __name__ == '__main__':
    main()
