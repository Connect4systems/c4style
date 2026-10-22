// Frappe evaluates this script after creating the route's page wrapper.
frappe.pages["c4style-settings"].on_page_load = function (wrapper) {
	frappe.c4style.build_settings_page(wrapper);
};
