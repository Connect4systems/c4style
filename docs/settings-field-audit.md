# Style Settings field audit - 23 October 2026

Removed `persistent_menu` from the form and server mapping. Its disabled state routed users into a centered native workspace sidebar, bypassing the edge menu on list/form pages. Permitted workspaces now use one edge menu consistently; existing stored values of this removed field cannot disable it.

The remaining 40 data controls have active consumers. They are retained rather than deleting settings that do affect the app. Announcement details are hidden when the announcement is disabled. New-user menu width and personal-direction precedence are documented in the form.

| Field | Applied effect |
| --- | --- |
| `palette` | Loads all preset colors; Custom preserves manual colors. |
| `allow_user_themes` | Enables an account-specific palette chooser in Appearance tools. Off by default; disabled preferences are ignored and the server rejects new personal selections. |
| `primary` | Primary action buttons, selected accents and palette preview. |
| `accent` | Secondary accent, focus outlines and native selection colors. |
| `background` | Desk page background. |
| `menu_background` | Edge menu and inner menu background. |
| `menu_text` | Menu labels and icon stroke/fill tokens. |
| `menu_active` | Selected and hovered menu items. |
| `font_size` | Root and base text size. |
| `radius` | Inputs, cards, buttons and menu item corners. |
| `density` | Native row height and form control spacing. |
| `navbar_background` | Header and drawer heading background. |
| `navbar_text` | Header text and icons. |
| `panel_background` | Cards, forms, preview and drawer panels. |
| `table_header_background` | List, grid and data table headings. |
| `table_header_text` | List, grid and data table heading text. |
| `brand_name` | Menu brand label, visible on expansion and hover. |
| `font_family` | Desk, button and input font stack. |
| `text_direction` | Site direction when a user has no personal direction override. |
| `menu_default_collapsed` | Initial width only for accounts without a saved menu preference. |
| `menu_behavior` | Hover/focus expansion or explicit width controls. |
| `show_scroll_buttons` | Scroll-to-top and scroll-to-bottom controls. |
| `native_drawers` | Native notification/user content presented as side drawers. |
| `header_style` | Capsule header sizing/margins or flat header. |
| `row_style` | Separated list cards or standard flat rows. |
| `input_border_style` | Solid, dashed or absent native input borders. |
| `field_style` | Boxed controls or underline fields. |
| `button_style` | Filled or outline secondary actions, including custom actions. |
| `shadow_style` | Standard soft shadows or no shadows. |
| `secondary_background` | Secondary action fill or outline. |
| `secondary_text` | Filled secondary action text. |
| `row_hover_background` | Hovered separated list rows. |
| `row_border` | Separated list borders, boxed fields and preview rows. |
| `input_background` | Native input background. |
| `input_border` | Native input border color; visible with solid/dashed borders. |
| `enable_announcement` | Shows the announcement when nonempty text is configured. |
| `announcement_text` | Plain text strip. Short text stays visible; overflowing text moves within its viewport. |
| `announcement_speed` | Overflowing text animation duration. No motion for text that already fits. |
| `announcement_background` | Announcement strip background. |
| `announcement_color` | Announcement text and close control. |

`theme_preview` is a rendered HTML field rather than stored configuration. Tab/section fields organize the form. A schema test requires every stored data control to have a corresponding server mapping (apart from the palette selector), preventing orphan controls.

Read-only authenticated checks in `artifacts/menu-review/report.json` use updated browser-local assets against the deployed site and leave shared/personal settings unchanged. They verify the existing disabled legacy-menu state, x=0 menu edge placement, 72px collapsed / 236px hover width, menu colors and icon tokens, header hit testing, workspace links, notification tabs, drawer controls, announcements and list/form/mobile routes. The updated schema and Python mapping require deployment and migration by the site operator.
