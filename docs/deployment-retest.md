# Deployed-site retest - 23 October 2026

The authenticated browser loaded the production CSS and JavaScript directly from oro.connect4systems.com. No local file overrides or shared settings writes were used. All three public assets matched the latest workspace files before the new cache-invalidation change. A fresh 1840px session rendered a 72px menu at x=0 with the saved Dark Green colors and no legacy header settings button.

The deployed regression check passed: edge position, 236px hover expansion, saved menu/icon colors, workspace navigation, the saved short announcement, all three native notification tabs, Close/Escape, list/form placement and mobile overflow. No browser errors occurred. Evidence is in `artifacts/deployed-review/report.json` and its screenshots. The session uses the supplied test account; the user's existing browser cache was not accessible.

The asset responses use `Cache-Control: max-age=31536000`, while Desk currently includes stable, unversioned C4Style asset URLs. The supplied screenshot shows older UI behavior even though a fresh browser receives working current assets. This strongly suggests cached earlier CSS/JavaScript in that browser.

The local follow-up change adds content fingerprints to the hook asset URLs. Changed public files automatically receive a new URL after deployment and hook-cache clearing/restart. An automated check verifies that a changed file gets a new URL while unchanged files keep their URL. This hook change has not yet been deployed by the site operator. An InPrivate window or browser cache refresh can load the already deployed UI immediately.
