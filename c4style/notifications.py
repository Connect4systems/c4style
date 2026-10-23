"""The signed-in user's notification summary for Desk tools."""
import frappe


@frappe.whitelist(methods=['POST'])
def delete_notifications(names):
    """Recipients may clear selected personal alerts, never another inbox."""
    user = frappe.session.user
    if not user or user == 'Guest':
        frappe.throw('Please sign in', frappe.PermissionError)
    names = frappe.parse_json(names) if isinstance(names, str) else names
    if (not isinstance(names, list) or not names or len(names) > 500
            or any(not isinstance(name, str) or not name for name in names)):
        frappe.throw('Select between 1 and 500 notifications')
    names = list(dict.fromkeys(names))
    # Validate the entire selection before deleting, including requests forged
    # outside the list UI. Row locks keep ownership stable during this operation.
    for name in names:
        doc = frappe.get_doc('Notification Log', name, for_update=True)
        if doc.for_user != user:
            frappe.throw('You can only delete your own notifications', frappe.PermissionError)
    for name in names:
        frappe.delete_doc('Notification Log', name, ignore_permissions=True)
    return {'deleted': len(names)}


@frappe.whitelist()
def get_notifications():
    user = frappe.session.user
    if not user or user == 'Guest':
        frappe.throw('Please sign in', frappe.PermissionError)
    filters = {'for_user': user, 'read': 0}
    count = frappe.db.count('Notification Log', filters=filters)
    records = frappe.get_all('Notification Log', filters=filters,
                             fields=['name', 'subject', 'creation'], order_by='creation desc, name desc', limit_page_length=20)
    return {'unread_count': count, 'notifications': [
        {'name': row['name'], 'subject': frappe.utils.strip_html(row.get('subject') or '')[:240],
         'creation': str(row.get('creation') or '')}
        for row in records
    ]}
