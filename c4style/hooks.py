from hashlib import sha256 as _sha256
from pathlib import Path as _Path


def _asset_url(relative_path):
    content = (_Path(__file__).parent / "public" / relative_path).read_bytes()
    return f"/assets/c4style/{relative_path}?v={_sha256(content).hexdigest()[:12]}"


app_name = "c4style"
app_title = "C4Style"
app_publisher = "Connect 4 Systems"
app_description = "C4Style Frappe Theme"
app_email = "info@connect4systems.com"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = _asset_url("css/c4style.css")
app_include_js = [_asset_url("js/c4style.js"), _asset_url("js/desk_tools.js"), _asset_url("js/notifications.js")]

# include js, css files in header of web template
# web_include_css = "/assets/c4style/css/c4style.css"
# web_include_js = "/assets/c4style/js/c4style.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "c4style/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "c4style/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "c4style.utils.jinja_methods",
# 	"filters": "c4style.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "c4style.install.before_install"
# after_install = "c4style.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "c4style.uninstall.before_uninstall"
# after_uninstall = "c4style.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "c4style.utils.before_app_install"
# after_app_install = "c4style.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "c4style.utils.before_app_uninstall"
# after_app_uninstall = "c4style.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "c4style.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"c4style.tasks.all"
# 	],
# 	"daily": [
# 		"c4style.tasks.daily"
# 	],
# 	"hourly": [
# 		"c4style.tasks.hourly"
# 	],
# 	"weekly": [
# 		"c4style.tasks.weekly"
# 	],
# 	"monthly": [
# 		"c4style.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "c4style.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "c4style.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "c4style.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["c4style.utils.before_request"]
# after_request = ["c4style.utils.after_request"]

# Job Events
# ----------
# before_job = ["c4style.utils.before_job"]
# after_job = ["c4style.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"c4style.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Include saved site and user appearance in the Desk boot payload.
extend_bootinfo = "c4style.settings.boot_session"

# Remove retired workflow notification controls from existing installations.
after_migrate = "c4style.remove_workflow_notifications.execute"
after_install = "c4style.install_palettes.execute"
doctype_list_js = {"Notification Log": "public/js/notification_log_list.js"}
