"""Render a synthetic Frappe-shaped preview, not a screenshot of the deployed site."""
from pathlib import Path
from test_page_lifecycle import MenuTests

ROOT = Path(__file__).parents[1]
MenuTests.setUpClass()
test = MenuTests()
try:
    test.setUp()
    page = test.page
    page.set_viewport_size({'width': 1360, 'height': 800})
    page.evaluate('''() => {
        const items=['Tools','Accounting','Buying','Selling','Stock','Assets','Projects','HR','Manufacturing'];
        frappe.boot.allowed_workspaces=items.map(title=>({name:title,title,public:1,icon:'folder-normal'}));
        frappe.utils={icon:()=>'<svg class="icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="4" y="5" width="16" height="15" rx="3"/><path d="M8 5V3m8 2V3M4 10h16M8 14h8"/></svg>'};
        document.querySelector('.navbar').innerHTML='<div class="container"><span>Stock › Item</span><input class="form-control" aria-label="Search" placeholder="Search or type a command (Ctrl + G)"><span>&#9831; &nbsp; Help &#8964; &nbsp; &#9673;</span></div>';
        document.querySelector('.layout-main').outerHTML=`
        <main class="preview-main"><div class="page-head"><h2>&#9776; Item</h2><div><button class="btn btn-default">&#9776; List View &#8964;</button> <button class="btn btn-default">&#8635;</button> <button class="btn btn-default">•••</button> <button class="btn btn-primary">+ Add Item</button></div></div>
        <div class="layout-main"><aside class="filter-sidebar"><p>Filter By</p><select class="form-control"><option>Assigned To</option></select><select class="form-control"><option>Created By</option></select><p>Edit Filters</p><select class="form-control"><option>Tags</option></select><p>Show Tags</p><p style="margin-top:42px">Save Filter</p><input class="form-control" placeholder="Filter Name"></aside>
        <section class="layout-main-section frappe-list"><div class="filters"><input class="form-control" placeholder="ID"><input class="form-control" placeholder="Item Name"><input class="form-control" placeholder="Item Group"><button class="btn btn-default">+ Filter ×</button><button class="btn btn-default">&#8595; Last Updated On</button></div><div class="list-row-head level"><span>&#9633; &nbsp;Item Name</span><span>Status</span><span>Brand</span><span>Item Group</span><span>Maintain Stock</span><span>Pos Category</span><span>ID</span></div><div id="preview-rows"></div></section></div></main>`;
        const names=['4700 BC INSTANT P','FORTUNE KACHI GH','FRESH AURAA FOO','FROOTI TETRA MIC CY','FULL MILK PASTEUR','GOLDEN HARVEST','GREEN TEA PREMIUM','HIMALAYAN WATER'];
        document.querySelector('#preview-rows').innerHTML=names.map((name,index)=>`<div class="list-row-container"><div class="list-row"><span>&#9633; &#9998; ${name}</span><span class="status">Enabled</span><span>—</span><span>Food Items</span><span>&#9745;</span><span>Food Items</span><span>${470000+index}…</span></div></div>`).join('');
        frappe.c4style.apply_theme({...frappe.c4style.palette_settings('Lime Fresh'),persistentMenu:true,enableAnnouncement:true,announcementText:'This is a test announcement',announcementSpeed:24,menuBehavior:'hover',radius:10});
        frappe.c4style.save_personal('menuCollapsed',true);
    }''')
    page.add_style_tag(content='''
        * {box-sizing:border-box}body{margin:0;color:#56624c;font-size:14px}
        .navbar .container{display:flex;align-items:center;justify-content:space-between;gap:24px;height:100%;color:white}
        .navbar input{width:330px;height:30px;font-size:12px}.preview-main{padding:0 22px}
        .page-head{display:flex;justify-content:space-between;align-items:center;height:72px;position:sticky}
        .page-head h2{font-size:21px;color:#34442e;margin:0}.btn{padding:6px 12px;font-size:14px;cursor:pointer}
        .btn-primary{background:var(--primary);color:white}.layout-main{display:flex;gap:20px;padding-block:8px}
        .filter-sidebar{flex:0 0 200px;background:var(--c4style-panel-bg);padding:20px;border-radius:12px}
        .filter-sidebar .form-control{margin-block:12px;width:100%;padding:8px}.filter-sidebar p{font-size:13px}
        .layout-main-section{flex:1;min-width:0;padding:12px}.filters{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}
        .filters input{width:145px;padding:7px}.list-row-head,.list-row{display:grid!important;grid-template-columns:2.5fr 1fr .7fr 1.3fr 1.2fr 1.2fr 1fr;align-items:center;gap:10px}
        .list-row-head{padding:9px 12px;font-size:13px}.list-row{font-size:13px}.list-row>span{overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
        .status{color:#267388}.list-row-container{border:1px solid #edf0e8!important}.list-row-container:first-child{border-color:#a8b39e!important}
        .c4style-app-menu .item-anchor{color:inherit;text-decoration:none}.c4style-app-menu .standard-sidebar-item{margin-block:10px}
    ''')
    page.mouse.move(1000, 780)
    # Keep the announcement readable in the static preview.
    page.add_style_tag(content='.c4style-announcement-message{animation:none;text-align:right}')
    page.screenshot(path=str(ROOT / 'artifacts/reference-layout-preview.png'), full_page=True)
    print('Preview:', ROOT / 'artifacts/reference-layout-preview.png')
    test.tearDown()
finally:
    MenuTests.tearDownClass()

