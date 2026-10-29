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
    """Live actionable documents; never infer eligibility from notification logs."""
    from frappe.model.workflow import get_transitions, has_approval_access

    user = frappe.session.user
    if not user or user == 'Guest':
        frappe.throw('Please sign in', frappe.PermissionError)
    roles = set(frappe.get_roles(user))
    records = []
    seen = set()
    for row in frappe.get_all('Workflow', filters={'is_active': 1}, fields=['name']):
        workflow = frappe.get_doc('Workflow', row.name)
        states = list({t.state for t in workflow.transitions if t.allowed in roles})
        if not states or not frappe.has_permission(workflow.document_type, "read"):
            continue
        start = 0
        while True:
            # get_list applies the current user's document and user permissions.
            candidates = frappe.get_list(workflow.document_type,
                filters={workflow.workflow_state_field: ['in', states], 'docstatus': ['<', 2]},
                fields=['name'], order_by='modified desc, name desc',
                limit_start=start, limit_page_length=200)
            for candidate in candidates:
                doc = frappe.get_doc(workflow.document_type, candidate.name)
                transitions = [t for t in get_transitions(doc, workflow)
                               if has_approval_access(user, doc, t)]
                key = (doc.doctype, doc.name)
                if not transitions or key in seen:
                    continue
                seen.add(key)
                state = doc.get(workflow.workflow_state_field)
                records.append({'name': frappe.as_json([doc.doctype, doc.name, state]),
                    'doctype': doc.doctype, 'document_name': doc.name, 'state': state,
                    'subject': f'{doc.doctype} {doc.name}: {state}',
                    'actions': list(dict.fromkeys(t.action for t in transitions)),
                    'creation': str(doc.modified)})
            if len(candidates) < 200:
                break
            start += len(candidates)
    records.sort(key=lambda item: (item['creation'], item['name']), reverse=True)
    return {'pending_count': len(records), 'notifications': records}


def notify_workflow_owner(doc, method=None):
    """Deliver committed workflow state changes to the owner as popups only."""
    from frappe.model.workflow import get_workflow_name

    workflow_name = get_workflow_name(doc.doctype)
    if not workflow_name:
        return
    before = doc.get_doc_before_save()
    if not before:
        return
    workflow = frappe.get_cached_doc('Workflow', workflow_name)
    field = workflow.workflow_state_field
    previous, current = before.get(field), doc.get(field)
    if previous == current or not doc.owner or doc.owner == 'Guest':
        return
    frappe.publish_realtime('c4style_workflow_owner_update', {
        'doctype': doc.doctype, 'document_name': doc.name,
        'subject': f'{doc.doctype} {doc.name}: {previous} ? {current} ({frappe.session.user})',
    }, user=doc.owner, after_commit=True)
