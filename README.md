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

Open **C4Style > Style Settings** inside Desk, or search for **Style Settings**. The native Single DocType is available at `/app/style-settings`. Only **System Manager** and **Website Manager** can read and edit it. The header settings button has been removed.

Each built-in palette supplies defaults for every theme color, including menu, component and announcement colors. **Reset palette colors** restores the selected preset before saving; explicit manager customizations remain saved until changed. Choose one of 17 palettes or customize primary, accent, page, card, header, table, menu and text/icon colors. The Single DocType has Theme, Navigation, Components, Announcement and Preview tabs. Components include capsule/flat headers, separated/flat rows, dashed/solid/no input borders, boxed/underline fields, filled/outline buttons and optional shadows. Typography, spacing and direction are configurable. Save to apply the shared Desk theme; other sessions receive changes after reloading. Old personal color overrides no longer override the manager's theme.

The edge-aligned navigation menu is available on workspace, list, and form pages. It builds links exclusively from Frappe's `allowed_workspaces` boot data, preserves private workspace routes and nested groups, and hides the duplicate workspace sidebar. New users start with an icon-only menu by default. Optional hover/focus expansion keeps their saved width preference. The legacy menu-mode switch has been removed so the menu position, colors and hover behavior stay consistent on every Desk page. The existing app logo opens a searchable workspace launcher.

Every signed-in Desk user can use the arrows in the menu to switch between a full menu with icons and labels and a narrow menu with icons only, or expand/narrow the workspace. Links keep tooltips and accessible labels in narrow mode. A third button switches text direction between RTL and LTR and moves the menu to match. These preferences save separately for each account and do not grant access to theme settings. Mobile navigation uses a horizontally scrollable layout; it is omitted from print output.

The floating **Appearance tools** button offers personal layout controls, a searchable app launcher and private colored sticky notes. Save notes, then choose **Pin saved notes** for draggable/resizable windows with keyboard movement. Note text/colors persist per account; pinned window positions last for the page session. Managers also get a shared palette chooser with confirmation and a link to Style Settings. The header has no added settings button.

Configure the plain-text announcement (short messages stay visible; overflowing messages scroll) in its own tab. Users can dismiss it for the page session. Navigation settings control scroll-to-top/bottom buttons and native notification/user side drawers. Animation respects reduced-motion preferences.

List views offer **Group loaded rows** for supported columns. Counts refer to currently loaded records. Filtering, sorting, selection and permissions remain managed by Frappe.

See [the video comparison](docs/video-reference-review.md) for implemented features, remaining differences and the synthetic layout preview.

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

Authenticated regression checks with browser-local assets can be run with:

```sh
python -B tests/run_regression_review.py --base-url https://your-site --session-file /temporary/session.json
```

This check temporarily saves shared style options and restores the original settings in `finally`, then verifies them after reload. It does not deploy local app files. Use a test site or an agreed testing window.
