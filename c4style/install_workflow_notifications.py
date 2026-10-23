"""Install workflow notification controls without changing Frappe core DocTypes."""
def install():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    create_custom_fields({
        'Workflow Transition': [
            {'fieldname': 'c4style_create_notification', 'label': 'Create System Notification',
             'fieldtype': 'Button', 'insert_after': 'send_email_to_creator'},
            {'fieldname': 'c4style_notification', 'label': 'System Notification',
             'fieldtype': 'Link', 'options': 'Notification', 'read_only': 1,
             'no_copy': 1, 'insert_after': 'c4style_create_notification'},
        ],
        'Notification': [
            {'fieldname': 'c4style_workflow_section', 'label': 'Workflow Transition',
             'fieldtype': 'Section Break', 'insert_after': 'from_attach_field',
             'depends_on': 'c4style_workflow'},
            {'fieldname': 'c4style_workflow', 'label': 'Workflow', 'fieldtype': 'Link',
             'options': 'Workflow', 'read_only': 1, 'no_copy': 1,
             'insert_after': 'c4style_workflow_section', 'depends_on': 'c4style_workflow'},
            {'fieldname': 'c4style_transition', 'label': 'Transition Row', 'fieldtype': 'Data',
             'read_only': 1, 'no_copy': 1, 'insert_after': 'c4style_workflow',
             'depends_on': 'c4style_workflow'},
            {'fieldname': 'c4style_transition_condition', 'label': 'Transition Condition',
             'fieldtype': 'Code', 'options': 'Python', 'read_only': 1,
             'insert_after': 'c4style_transition', 'depends_on': 'c4style_workflow',
             'description': 'Checked by the workflow against the document before its state changes, in the acting user\'s session.'},
            {'fieldname': 'c4style_transition_key', 'label': 'Transition Notification Key',
             'fieldtype': 'Data', 'hidden': 1, 'read_only': 1, 'no_copy': 1,
             'unique': 1, 'insert_after': 'c4style_transition_condition'},
        ],
    }, update=True)
