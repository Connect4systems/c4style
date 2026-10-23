(()=>{
    frappe.ui.form.on('Notification', {
        refresh(frm) {
            if (!frm.doc.c4style_workflow) return;
            ['channel', 'document_type', 'event', 'condition', 'recipients', 'send_to_all_assignees',
                'send_system_notification', 'set_property_after_alert', 'property_value'].forEach(field => {
                frm.set_df_property(field, 'read_only', 1);
            });
            frm.set_intro(__('This rule runs only after its matching workflow transition succeeds. Its role, owner recipient and condition follow the Workflow. You can edit the message or disable the rule.'));
        },
    });
})();
