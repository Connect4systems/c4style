"""Workflow transition notifications, evaluated before a successful state change.

Rules use Notification's Custom event. Native transition permissions remain in charge;
logs are inserted in the document transaction and Frappe publishes them after commit.
"""
from contextvars import ContextVar
from hashlib import sha256

import frappe

_active_transition = ContextVar('c4style_active_transition', default=None)
_active_bulk_action = ContextVar('c4style_bulk_action', default=None)


def _schema_ready():
    """Hooks can run before this app's installer during another app's migration.

    Check physical columns, not just Custom Field metadata. Do not memoize a
    missing schema: the installer may finish later in this same process.
    """
    return (frappe.db.has_column('Notification', 'c4style_transition_key')
            and frappe.db.has_column('Workflow Transition', 'c4style_notification'))


def _require_schema():
    if not _schema_ready():
        frappe.throw('Workflow notification fields are not installed yet. Run the C4Style field installer and site migration.')


def _key(workflow, transition):
    return sha256((workflow + '\0' + transition).encode()).hexdigest()


def _row(workflow, transition):
    row = next((row for row in workflow.transitions if row.name == transition), None)
    if row is None:
        frappe.throw('This transition no longer exists. Save the Workflow and try again.')
    return row


def _defaults(workflow, row):
    return {
        'channel': 'System Notification', 'send_system_notification': 1,
        'event': 'Custom', 'document_type': workflow.document_type,
        'condition': '', 'c4style_workflow': workflow.name,
        'c4style_transition': row.name, 'c4style_transition_key': _key(workflow.name, row.name),
        'c4style_transition_condition': row.condition or '',
        'recipients': [{'receiver_by_document_field': 'owner'}, {'receiver_by_role': row.allowed}],
    }


@frappe.whitelist()
def prepare_notification(workflow, transition):
    if frappe.session.user == 'Guest':
        frappe.throw('Please sign in', frappe.PermissionError)
    _require_schema()
    workflow = frappe.get_doc('Workflow', workflow)
    workflow.check_permission('write')
    row = _row(workflow, transition)
    existing = frappe.db.get_value('Notification', {'c4style_transition_key': _key(workflow.name, row.name)}, 'name')
    if existing:
        frappe.get_doc('Notification', existing).check_permission('read')
        return {'existing': existing}
    if not frappe.has_permission('Notification', 'create'):
        frappe.throw('You need permission to create Notifications', frappe.PermissionError)
    return {'defaults': {
        **_defaults(workflow, row), 'enabled': 1,
        'subject': '{{ doc.doctype }} {{ doc.name }}: {{ transition.action }} → {{ transition.next_state }}',
        'message': '{{ doc.doctype }} {{ doc.name }} moved from {{ transition.state }} to {{ transition.next_state }}.',
    }}


def validate_notification(doc, method=None):
    workflow_name = doc.get('c4style_workflow')
    transition = doc.get('c4style_transition')
    if not _schema_ready():
        if workflow_name or transition:
            _require_schema()
        return
    if not workflow_name and not transition:
        doc.set('c4style_transition_key', None)
        return
    if not workflow_name or not transition:
        frappe.throw('Workflow and Transition Row must be specified together')
    workflow = frappe.get_doc('Workflow', workflow_name)
    workflow.check_permission('write')
    row = _row(workflow, transition)
    duplicate = frappe.db.get_value('Notification', {'c4style_transition_key': _key(workflow.name, row.name)}, 'name')
    if duplicate and duplicate != doc.name:
        frappe.throw('This transition already has a System Notification: ' + duplicate)
    # Source routing is fixed; the manager can edit enabled, subject and message.
    for field, value in _defaults(workflow, row).items():
        doc.set(field, value)
    doc.set('send_to_all_assignees', 0)
    doc.set('set_property_after_alert', None)


def link_notification(doc, method=None):
    if not doc.get('c4style_workflow') or not _schema_ready():
        return
    frappe.db.set_value('Workflow Transition', doc.c4style_transition,
                        'c4style_notification', doc.name, update_modified=False)
    frappe.clear_document_cache('Workflow', doc.c4style_workflow)


def unlink_notification(doc, method=None):
    if not _schema_ready():
        return
    if doc.get('c4style_transition') and frappe.db.get_value(
            'Workflow Transition', doc.c4style_transition, 'c4style_notification') == doc.name:
        frappe.db.set_value('Workflow Transition', doc.c4style_transition,
                            'c4style_notification', None, update_modified=False)
        frappe.clear_document_cache('Workflow', doc.c4style_workflow)


def sync_workflow_notifications(doc, method=None):
    """Keep generated routing in step with edits to the Workflow rows."""
    if not _schema_ready():
        return
    for row in doc.transitions:
        name = frappe.db.get_value('Notification', {'c4style_transition_key': _key(doc.name, row.name)}, 'name')
        if name:
            rule = frappe.get_doc('Notification', name)
            rule.save(ignore_permissions=True)


@frappe.whitelist()
def apply_workflow(doc, action):
    """Delegate the actual action to core, carrying its exact selected row to hooks."""
    from frappe.model.workflow import apply_workflow as native_apply, get_transitions, get_workflow

    source = frappe.parse_json(doc) if isinstance(doc, str) else doc
    if isinstance(source, dict):
        before = frappe.get_doc(source['doctype'], source['name'])
    else:
        before = frappe.get_doc(source.doctype, source.name)
    workflow = get_workflow(before.doctype)
    # Core chooses the last eligible row for this action; preserve that selection.
    matches = [row for row in get_transitions(before, workflow) if row.action == action]
    selected = matches[-1] if matches else None
    context = (before.doctype, before.name, selected.name) if selected else None
    token = _active_transition.set(context)
    try:
        return native_apply(doc, action)
    finally:
        _active_transition.reset(token)


@frappe.whitelist(methods=['POST'])
def bulk_workflow_approval(docnames, doctype, action):
    """Keep core's bulk worker and its per-document commits, carrying the action."""
    names = frappe.parse_json(docnames) if isinstance(docnames, str) else docnames
    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        frappe.throw('Document names must be a list')
    if len(names) < 20:
        return bulk_workflow_action(names, doctype, action)
    if len(names) > 500:
        frappe.throw('Bulk approval supports up to 500 documents')
    frappe.enqueue('c4style.workflow_notifications.bulk_workflow_action', docnames=names,
                   doctype=doctype, action=action, queue='short', timeout=1000)
    frappe.msgprint('Workflow action queued', alert=True)


def bulk_workflow_action(docnames, doctype, action):
    from frappe.model.workflow import _bulk_workflow_action

    token = _active_bulk_action.set((doctype, action))
    try:
        return _bulk_workflow_action(docnames, doctype, action)
    finally:
        _active_bulk_action.reset(token)


def capture_transition(doc, method=None):
    from frappe.model.workflow import get_transitions, get_workflow, get_workflow_name, has_approval_access

    doc.flags.c4style_transition_notification = None
    if doc.is_new() or not _schema_ready() or not get_workflow_name(doc.doctype):
        return
    workflow = get_workflow(doc.doctype)
    if not workflow.is_active:
        return
    before = doc.get_doc_before_save()
    if before is None:
        return
    old_state = before.get(workflow.workflow_state_field)
    next_state = doc.get(workflow.workflow_state_field)
    context = _active_transition.get()
    exact = context and context[:2] == (doc.doctype, doc.name)
    bulk = _active_bulk_action.get()
    bulk_matches = bulk and bulk[0] == doc.doctype
    if old_state == next_state and not (exact or bulk_matches):
        return
    candidates = [row for row in get_transitions(before, workflow)
                  if row.state == old_state and row.next_state == next_state
                  and has_approval_access(frappe.session.user, before, row)]
    if exact:
        candidates = [row for row in candidates if row.name == context[2]]
    elif bulk_matches:
        candidates = [row for row in candidates if row.action == bulk[1]][-1:]
    if len(candidates) != 1:
        # Direct saves/background execution may not carry an action. Never guess
        # between two different actions that happen to have the same destination.
        if len(candidates) > 1:
            frappe.log_error('Cannot identify the exact action for {0} {1}: {2} → {3}'.format(
                doc.doctype, doc.name, old_state, next_state), 'C4Style workflow notification: ambiguous action')
        return
    row = candidates[0]
    rule_name = frappe.db.get_value('Notification', {'c4style_transition_key': _key(workflow.name, row.name)}, 'name')
    if rule_name:
        doc.flags.c4style_transition_notification = {
            'notification': rule_name, 'workflow': workflow.name, 'row': row.name,
            'actor': frappe.session.user, 'transition': {
                'state': row.state, 'action': row.action, 'next_state': row.next_state, 'allowed': row.allowed,
            },
        }


def _recipients(doc, allowed_role):
    candidates = {doc.get('owner')}
    candidates.update(frappe.get_all('Has Role', filters={
        'role': allowed_role, 'parenttype': 'User'}, pluck='parent'))
    candidates.discard(None)
    candidates.discard('Guest')
    if not candidates:
        return []
    enabled = frappe.get_all('User', filters={'name': ['in', sorted(candidates)], 'enabled': 1}, pluck='name')
    return sorted({user for user in enabled if frappe.has_permission(doc.doctype, 'read', doc=doc, user=user)})


def deliver_transition(doc, method=None):
    pending = doc.flags.get('c4style_transition_notification')
    if not pending or pending.get('delivered') or not _schema_ready():
        return
    rule = frappe.get_doc('Notification', pending['notification'])
    if (not rule.enabled or rule.channel != 'System Notification' or rule.event != 'Custom'
            or rule.document_type != doc.doctype
            or rule.get('c4style_transition_key') != _key(pending['workflow'], pending['row'])):
        return
    context = {'doc': doc, 'transition': pending['transition']}
    subject = frappe.render_template(rule.subject or 'Workflow updated: {{ doc.name }}', context)
    message = frappe.render_template(rule.message or '', context)
    for user in _recipients(doc, pending['transition']['allowed']):
        frappe.get_doc({
            'doctype': 'Notification Log', 'for_user': user, 'from_user': pending['actor'],
            'type': 'Alert', 'subject': subject, 'email_content': message,
            'document_type': doc.doctype, 'document_name': doc.name,
        }).insert(ignore_permissions=True)
    pending['delivered'] = True
