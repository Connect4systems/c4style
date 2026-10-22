// Legacy bookmarks redirect to the native Single DocType.
frappe.pages["c4style-settings"].on_page_load = function () {
    frappe.set_route("Form", "Style Settings");
};
