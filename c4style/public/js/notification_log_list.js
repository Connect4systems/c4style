(() => {
    const settings = frappe.listview_settings['Notification Log'] ||= {};
    let activeList;
    settings.add_fields = [...new Set([...(settings.add_fields || []), 'read', 'for_user'])];
    const previousRender = settings.before_render;
    settings.before_render = function (listview) {
        if (previousRender) previousRender.apply(this, arguments);
        // Frappe v15 invokes before_render without a listview argument.
        listview = listview || activeList || window.cur_list;
        if (!listview?.$result) return;
        // Run after Frappe has replaced the list rows, including pagination/filter changes.
        requestAnimationFrame(() => {
            const records = new Map(listview.data.map(row => [row.name, row]));
            listview.$result.find('.list-row-container').each(function () {
                const name = this.getAttribute('data-name') || this.querySelector('[data-name]')?.getAttribute('data-name');
                const record = records.get(name);
                this.classList.toggle('c4style-notification-unread', !!record && Number(record.read) === 0);
                this.classList.toggle('c4style-notification-read', !!record && Number(record.read) === 1);
                const subject = this.querySelector('.list-subject');
                if (!subject) return;
                let status = subject.querySelector('.c4style-notification-status');
                if (!record || ![0, 1].includes(Number(record.read))) { status?.remove(); return; }
                if (!status) {
                    status = document.createElement('span');
                    status.className = 'c4style-notification-status';
                    subject.appendChild(status);
                }
                const label = Number(record.read) === 1 ? __('Read') : __('Unread');
                if (status.textContent !== label) status.textContent = label;
            });
        });
    };
    const previous = settings.onload;
    settings.onload = function (listview) {
        activeList = listview;
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
