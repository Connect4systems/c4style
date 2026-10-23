"""Remove retired workflow controls without deleting notifications or their logs."""

import frappe


FIELDS = {
    'Workflow Transition': ('c4style_create_notification', 'c4style_notification'),
    'Notification': (
        'c4style_transition_key', 'c4style_transition_condition',
        'c4style_transition', 'c4style_workflow', 'c4style_workflow_section',
    ),
}


def execute():
    # Delete Custom Field metadata only. Frappe retains stored column data;
    # existing Notification and Notification Log records are preserved.
    for doctype, fields in FIELDS.items():
        for fieldname in fields:
            name = frappe.db.get_value('Custom Field', {
                'dt': doctype, 'fieldname': fieldname,
            }, 'name')
            if name:
                frappe.delete_doc('Custom Field', name, ignore_permissions=True)
        frappe.clear_cache(doctype=doctype)
