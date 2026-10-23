"""Read-only live checks for edge menu, announcements and native notification tabs."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base-url',required=True)
    parser.add_argument('--session-file',required=True)
    parser.add_argument('--output',default='artifacts/menu-review')
    args=parser.parse_args()
    output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
    checks=[];errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        context=browser.new_context(storage_state=args.session_file,viewport={'width':1480,'height':960})
        def assets(route):
            relative=route.request.url.split('/assets/c4style/',1)[1].split('?',1)[0]
            path=(ROOT/'c4style/public'/relative).resolve()
            if path.is_relative_to((ROOT/'c4style/public').resolve()) and path.is_file():
                route.fulfill(body=path.read_bytes(),content_type='text/css' if path.suffix=='.css' else 'application/javascript')
            else: route.continue_()
        context.route('**/assets/c4style/**',assets)
        page=context.new_page();page.set_default_timeout(15000)
        page.on('pageerror',lambda e:errors.append(str(e)))
        def check(name,fn):
            try:
                detail=fn();checks.append(dict(name=name,passed=True,detail=detail));print('PASS '+name,flush=True)
            except Exception as e:
                checks.append(dict(name=name,passed=False,error=str(e)));print('FAIL '+name+': '+str(e)[:300],flush=True)
        page.goto(args.base_url.rstrip('/')+'/app/home',wait_until='domcontentloaded')
        page.wait_for_function('window.frappe?.c4style && frappe.boot?.c4style')
        snapshot=page.evaluate('JSON.stringify(frappe.boot.c4style)')
        def navigation():
            rail=page.locator('.c4style-app-menu');rail.wait_for(state='visible')
            page.mouse.move(900,700)
            box=rail.bounding_box();assert abs(box['x'])<1,box
            assert box['width']==72,box
            rail.locator('.c4style-brand').hover()
            page.wait_for_function('document.querySelector(".c4style-app-menu").getBoundingClientRect().width===236')
            assert rail.locator('.sidebar-item-label').first.is_visible()
            assert rail.evaluate('e=>e.contains(document.elementFromPoint(120,60))')
            expected=page.evaluate('''()=>{const e=document.createElement('span');e.style.color=frappe.c4style.get_theme().menuBackground;document.body.append(e);const c=getComputedStyle(e).color;e.remove();return c;}''')
            assert rail.evaluate('e=>getComputedStyle(e).backgroundColor')==expected
            assert rail.locator('.icon').first.evaluate('e=>getComputedStyle(e).getPropertyValue("--icon-stroke").trim()')==page.evaluate('frappe.c4style.get_theme().menuText')
            page.locator('.widget a[href]').first.wait_for(state='visible')
            page.screenshot(path=str(output/'menu-hover.png'))
            target=rail.locator('a[data-workspace="Stock"]');href=target.get_attribute('href');target.click()
            page.wait_for_url('**'+href)
            return dict(edge_x=box['x'],collapsed_width=box['width'],hover_width=236,route=href,legacy_menu_flag=page.evaluate('frappe.boot.c4style.site.persistentMenu'))
        check('edge position, hover, saved menu colors and workspace navigation',navigation)
        def announcement():
            page.evaluate('frappe.c4style.apply_theme({enableAnnouncement:true,announcementText:"Announcement stays visible",announcementSpeed:25})')
            message=page.locator('.c4style-announcement-message')
            assert message.is_visible()
            assert message.evaluate('e=>getComputedStyle(e).animationName')=='none'
            assert message.evaluate('e=>{const a=e.getBoundingClientRect(),b=e.parentElement.getBoundingClientRect();return a.left>=b.left&&a.right<=b.right+1;}')
            page.screenshot(path=str(output/'announcement.png'))
            return dict(short_text_visible=True)
        check('short announcement remains visible without blank animation intervals',announcement)
        def notifications():
            page.locator('.dropdown-notifications > button').click()
            drawer=page.locator('.dropdown-notifications > .dropdown-menu.show');drawer.wait_for(state='visible')
            assert drawer.evaluate('e=>{const b=e.getBoundingClientRect();return e.contains(document.elementFromPoint(b.x+20,b.y+20));}')
            for category,panel in [('notifications','panel-notifications'),('todays_events','panel-events'),('changelog_feed','panel-changelog-feed')]:
                drawer.locator('#'+category).click()
                drawer.locator('.'+panel+' > div').wait_for(state='visible')
            page.screenshot(path=str(output/'notifications.png'))
            drawer.get_by_role('button',name='Close',exact=True).click()
            page.wait_for_selector('.c4style-drawer-backdrop',state='detached')
            page.locator('.dropdown-navbar-user > button').click()
            page.locator('.dropdown-navbar-user > .dropdown-menu.show').wait_for(state='visible')
            page.keyboard.press('Escape')
            page.wait_for_selector('.c4style-drawer-backdrop',state='detached')
            return dict(notification_tabs=3,user_drawer=True,close=True)
        check('native notification tabs, drawer controls and user menu',notifications)
        def route_checks():
            for path in ['/app/item','/app/style-settings']:
                page.goto(args.base_url.rstrip('/')+path,wait_until='domcontentloaded')
                page.locator('.c4style-app-menu').wait_for(state='visible')
                assert abs(page.locator('.c4style-app-menu').bounding_box()['x'])<1
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            return dict(routes=2,mobile_width=390)
        check('edge menu on list and form routes and mobile overflow',route_checks)
        assert page.evaluate('JSON.stringify(frappe.boot.c4style)')==snapshot
        (output/'report.json').write_text(json.dumps(dict(base_url=args.base_url,local_asset_override=True,shared_settings_unchanged=True,checks=checks,browser_errors=errors),indent=2))
        browser.close()
    if errors or any(not c['passed'] for c in checks):raise SystemExit(1)

if __name__=='__main__':main()
