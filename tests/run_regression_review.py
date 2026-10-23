"""Live regression checks; overrides local assets only in the test browser.

Shared settings are snapshotted and restored in finally. No records or notes are seeded.
"""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--session-file', required=True)
    parser.add_argument('--output', default='artifacts/regression-review')
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    checks, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(storage_state=args.session_file, viewport={'width':1480,'height':960})
        def asset(route):
            relative = route.request.url.split('/assets/c4style/',1)[1].split('?',1)[0]
            path = (ROOT/'c4style/public'/relative).resolve()
            if path.is_relative_to((ROOT/'c4style/public').resolve()) and path.is_file():
                route.fulfill(body=path.read_bytes(), content_type='text/css' if path.suffix=='.css' else 'application/javascript')
            else: route.continue_()
        context.route('**/assets/c4style/**',asset)
        page=context.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(args.base_url.rstrip('/')+'/app/style-settings')
        page.wait_for_function('window.cur_frm && cur_frm.doc && cur_frm.doctype==="Style Settings"')
        # Native DocType scripts use a server endpoint rather than the public asset URL.
        page.evaluate('frappe.ui.form.handlers["Style Settings"] = {}')
        page.add_script_tag(content='(()=>{'+(ROOT/'c4style/c4style/doctype/style_settings/style_settings.js').read_text()+'})();')
        snapshot=page.evaluate('({settings:(frappe.c4style.get_site_theme || frappe.c4style.get_theme)(),palette:cur_frm.doc.palette})')
        def case(name,fn):
            try:
                detail=fn(); checks.append({'name':name,'passed':True,'detail':detail}); print('PASS '+name,flush=True)
            except Exception as exc:
                checks.append({'name':name,'passed':False,'error':str(exc)}); print('FAIL '+name+': '+str(exc)[:400],flush=True)
        def save(values,palette=None):
            return page.evaluate('''async ({values,palette})=>{
                const args={scope:'site',settings:JSON.stringify(values)};
                if(palette) args.palette=palette;
                const r=await frappe.call({method:'c4style.settings.save_settings',args});
                frappe.c4style.apply_theme(r.message);return r.message;
            }''',{'values':values,'palette':palette})
        try:
            def tabs():
                result=[]
                for name,field in [('Theme','palette'),('Navigation','menu_behavior'),('Components','header_style'),('Announcement','enable_announcement'),('Preview','theme_preview')]:
                    page.locator('.form-tabs .nav-link').filter(has_text=name).click()
                    page.locator(f'.frappe-control[data-fieldname="{field}"]').wait_for(state='visible')
                    result.append(name)
                return result
            case('all five native settings tabs reveal their controls',tabs)
            def native_save():
                page.evaluate('cur_frm.refresh()')
                page.get_by_role('button',name='Reset palette colors',exact=True).click()
                page.evaluate('async()=>{await cur_frm.save();}')
                page.wait_for_function('frappe.c4style.get_theme().primary===cur_frm.doc.primary')
                page.locator('.form-tabs .nav-link').filter(has_text='Preview').click()
                page.locator('.c4style-theme-preview').wait_for(state='visible')
                page.screenshot(path=str(output/'desktop.png'))
                return {'native_form_save':True}
            if snapshot['palette'] != 'Custom':
                case('native Reset palette colors and Save apply the preset',native_save)
            def palettes():
                names=page.evaluate('Object.keys(frappe.c4style.palettes)')
                for name in names:
                    values=page.evaluate('name=>frappe.c4style.palette_settings(name)',name)
                    saved=save(values,name)
                    assert all(saved[k].lower()==v.lower() for k,v in values.items()),name
                    assert page.locator('.c4style-app-menu .desk-sidebar').evaluate('(el)=>getComputedStyle(el).backgroundColor')==page.evaluate('color=>{const e=document.createElement("div");e.style.color=color;document.body.append(e);const c=getComputedStyle(e).color;e.remove();return c;}',values['menuBackground'])
                return {'presets':len(names),'colors_per_preset':len(values)}
            case('17 palettes persist every menu, component and announcement color',palettes)
            def components():
                options={'headerStyle':['flat','pill'],'rowStyle':['flat','separated'],'inputBorderStyle':['solid','none','dashed'],'fieldStyle':['underline','boxed'],'buttonStyle':['outline','filled'],'shadowStyle':['none','soft'],'menuBehavior':['click','hover']}
                count=0
                for key,choices in options.items():
                    for value in choices:
                        assert save({key:value})[key]==value
                        assert page.evaluate('key=>document.body.dataset[key]',key)==value
                        count+=1
                return {'choices':count}
            case('all 15 component and menu behavior choices save and apply',components)
            def menu():
                page.mouse.move(900,800)
                rail=page.locator('.c4style-app-menu')
                before=rail.bounding_box()['width']
                rail.locator('.c4style-brand').hover()
                page.wait_for_timeout(250)
                assert rail.bounding_box()['width']>before
                anchor=rail.locator('a[data-workspace]').filter(has_text='Stock').first
                if not anchor.count(): anchor=rail.locator('a[data-workspace]').first
                href=anchor.get_attribute('href');anchor.click()
                page.wait_for_url('**'+href)
                page.wait_for_timeout(500)
                return {'workspace_route':href,'hover_expands':True}
            case('menu expands on hover and workspace links navigate',menu)
            def drawers():
                for selector in ['.dropdown-notifications','.dropdown-navbar-user']:
                    page.locator(selector+' > button').click()
                    page.wait_for_selector('.c4style-drawer-backdrop')
                    drawer=page.locator(selector+' > .dropdown-menu')
                    box=drawer.bounding_box()
                    assert abs(box['y'])<1 and abs(box['height']-960)<1,box
                    assert drawer.evaluate('(el)=>{const b=el.getBoundingClientRect();return el.contains(document.elementFromPoint(b.x+20,b.y+20));}')
                    drawer.get_by_role('button',name='Close',exact=True).click()
                    page.wait_for_selector('.c4style-drawer-backdrop',state='detached')
                return {'native_drawers':2}
            case('notifications and user drawers open, stay clickable and close',drawers)
            def announcement():
                save({'enableAnnouncement':True,'announcementText':'C4Style QA <b>plain text</b>'})
                assert page.locator('.c4style-announcement-message').inner_text()=='C4Style QA <b>plain text</b>'
                assert page.locator('.c4style-announcement b').count()==0
                page.get_by_role('button',name='Dismiss announcement').click()
                assert page.locator('.c4style-announcement').count()==0
                return {'show':True,'dismiss':True,'escaped':True}
            case('announcement renders safely and dismisses',announcement)
            def responsive():
                page.set_viewport_size({'width':390,'height':844})
                page.wait_for_timeout(200)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                page.screenshot(path=str(output/'mobile.png'))
                page.set_viewport_size({'width':1480,'height':960})
                return {'width':390}
            case('mobile view has no horizontal page overflow',responsive)
        finally:
            save(snapshot['settings'],snapshot['palette'])
            page.reload()
            page.wait_for_function('window.frappe && frappe.boot && frappe.boot.c4style')
            restored=page.evaluate('frappe.boot.c4style.site')
            assert restored==snapshot['settings'],'Shared settings were not restored exactly'
            checks.append({'name':'original shared settings restored and verified after reload','passed':True})
            (output/'report.json').write_text(json.dumps({'base_url':args.base_url,'local_asset_override':True,'checks':checks,'browser_errors':errors},indent=2))
            browser.close()
    if errors or any(not c['passed'] for c in checks): raise SystemExit(1)

if __name__=='__main__': main()
