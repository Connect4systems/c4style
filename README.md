## C4Style

Frappe theme with an Odoo-inspired CSS design.

- Publisher: Connect 4 Systems
- Email: info@connect4systems.com

<img src="c4style.PNG">

#### For login page:
<p>
Add the css file in Website Settings, Header TAB:<br>
&lt;link rel="stylesheet" href="/assets/c4style/css/c4style.css"&gt;
</p>
<img src="login.PNG">

#### Style settings

Open **C4Style ? Style Settings** inside Desk, or search for **Style Settings**. The native Single DocType is available at `/app/style-settings`. Only **System Manager** and **Website Manager** can read and edit it. The header settings button has been removed.

Choose a palette (C4Style, Ocean, Forest, Sunset, Lime Fresh, Wine) or set individual primary, accent, page, card, header, table header, menu, icon/text, and selected item colors. Text size, font family, corner roundness, spacing, default text direction, and the menu brand name are also configurable. The form includes a preview before saving. Save to apply the shared theme; other sessions receive changes after reloading. Previous personal color overrides no longer override the manager's theme. Styling applies to Frappe Desk.

The optional persistent navigation menu remains available on workspace, list, and form pages. It builds links exclusively from Frappe's `allowed_workspaces` boot data, preserves private workspace routes and nested groups, and hides the duplicate workspace sidebar. Disable **Show workspace menu on every Desk page** to use the native workspace sidebar instead. Branding uses the existing Frappe app logo.

Every signed-in Desk user can use the arrows in the menu to switch between a full menu with icons and labels and a narrow menu with icons only, or expand/narrow the workspace. Links keep tooltips and accessible labels in narrow mode. A third button switches text direction between RTL and LTR and moves the menu to match. These preferences save separately for each account and do not grant access to theme settings. Mobile navigation uses a horizontally scrollable layout; it is omitted from print output.

After deploying the updated code, run these commands from the bench directory (replace `your-site` with your site name):

```sh
bench --site your-site migrate
bench build --app c4style
bench --site your-site clear-cache
bench restart
```

Hard-refresh the browser. Migration installs the Single DocType and the C4Style workspace shortcut. Existing `/app/c4style-settings` bookmarks redirect to the native form.

The visual direction is inspired by the [Kanak Infosystems theme walkthrough](https://www.youtube.com/watch?v=B_0SsIDih1k). This app implements its own styles and navigation; it does not include the vendor's theme code.

For standalone checks, run `python -B -m unittest discover -s tests -v`. Browser checks require Playwright and its Chromium browser. Full Frappe migration and permissions should also be verified on the target site.

#### License

mit
