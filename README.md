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

Open **Style settings** from the desk navbar or visit `/app/c4style-settings` to choose a color palette, customize primary/accent/background colors, adjust text size and corner roundness, switch between compact and comfortable spacing, or toggle the workspace between narrow and wide. Changes preview immediately. Choose **Save my preferences** to store them against your signed-in account across browsers. **Administrator** and users with the **System Manager** role can choose **Apply style for all users** and confirm to publish shared Desk defaults. Personal preferences take priority. Workspace width and text direction stay personal. Choose automatic, left-to-right, or right-to-left text direction; the expand/narrow arrow follows the reading direction. Reset restores the site defaults; save afterward to keep them. The theme applies to Frappe Desk, not public website pages.

After installing or updating the app, run these commands from the bench directory (replace `your-site` with your site name):

```sh
bench --site your-site migrate
bench build --app c4style
bench --site your-site clear-cache
bench restart
```

Hard-refresh the browser, then open `/app/c4style-settings`. Settings are implemented as a **Page**, so an empty DocType list for the C4Style module is expected.

#### License

mit
