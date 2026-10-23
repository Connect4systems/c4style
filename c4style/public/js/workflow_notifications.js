/* Transition-specific System Notification setup; Frappe retains Workflow permissions. */
(() => {
    function rowActions(frm, cdt, cdn) {
        const row = frm.fields_dict.transitions?.grid.grid_rows_by_docname[cdn];
        const fields = row?.grid_form?.fields_dict;
        const email = fields?.send_email_to_creator?.$wrapper?.[0];
        const create = fields?.c4style_create_notification?.$wrapper?.[0];
        if (!email || !create || create.parentElement?.classList.contains('c4style-transition-actions')) return;
        const actions = document.createElement('div'); actions.className = 'c4style-transition-actions';
        email.before(actions); actions.append(email, create);
    }
    frappe.ui.form.on('Workflow Transition', {
        form_render: rowActions,
        c4style_create_notification(frm, cdt, cdn) {
            if (frm.is_new() || frm.is_dirty()) {
                frappe.msgprint(__('Save the Workflow first, then create its System Notification.')); return;
            }
            frappe.call({ method: 'c4style.workflow_notifications.prepare_notification',
                args: { workflow: frm.doc.name, transition: cdn }, freeze: true,
                callback: response => {
                    const result = response.message;
                    if (result.existing) { frappe.set_route('Form', 'Notification', result.existing); return; }
                    frappe.model.with_doctype('Notification', () => {
                        const doc = frappe.model.get_new_doc('Notification');
                        const { recipients, ...values } = result.defaults;
                        Object.assign(doc, values);
                        (recipients || []).forEach(values => Object.assign(frappe.model.add_child(doc, 'Notification Recipient', 'recipients'), values));
                        frappe.set_route('Form', 'Notification', doc.name);
                    });
                },
            });
        },
    });
})();
