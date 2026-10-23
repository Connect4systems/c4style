"""The signed-in user's notification summary for Desk tools."""
import frappe


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
