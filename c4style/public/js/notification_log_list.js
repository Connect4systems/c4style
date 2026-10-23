(() => {
    const settings = frappe.listview_settings['Notification Log'] ||= {};
    const previous = settings.onload;
    settings.onload = function (listview) {
        if (previous) previous.call(this, listview);
        listview.page.add_action_item(__('Delete selected notifications'), () => {
            const names = listview.get_checked_items().map(row => row.name);
            if (!names.length) {
                frappe.msgprint(__('Select notifications to delete first.'));
                return;
            }
            frappe.confirm(__('Delete the {0} selected notifications?', [names.length]), () => {
                frappe.call({method: 'c4style.notifications.delete_notifications',
                    args: {names: JSON.stringify(names)}, freeze: true,
                    callback: () => {
                        listview.refresh();
                        frappe.c4style?.refresh_notifications?.();
                        frappe.show_alert({message: __('Selected notifications deleted'), indicator: 'green'});
                    },
                });
            });
        });
    };
})();
