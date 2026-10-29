"""Notification summaries must be restricted to the authenticated recipient."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock

fake=types.ModuleType('frappe')
fake.whitelist=lambda **kwargs: lambda fn: fn
fake.PermissionError=PermissionError
fake.session=types.SimpleNamespace(user='user@example.com')
fake.throw=Mock(side_effect=PermissionError)
fake.db=types.SimpleNamespace(count=Mock(return_value=37))
fake.get_all=Mock(return_value=[{'name':'note-one','subject':'Reminder'}])
fake.utils=types.SimpleNamespace(strip_html=lambda text:text.replace('<b>','').replace('</b>',''))
spec=importlib.util.spec_from_file_location('notifications_under_test',Path(__file__).parents[1]/'c4style/notifications.py')
notifications=importlib.util.module_from_spec(spec)
native=types.ModuleType('frappe.model.workflow')
native.get_transitions=Mock()
native.has_approval_access=Mock()
native.get_workflow_name=Mock(return_value='Approval')
sys.modules['frappe.model.workflow']=native
previous=sys.modules.get('frappe');sys.modules['frappe']=fake
spec.loader.exec_module(notifications)
if previous is None:del sys.modules['frappe']
else:sys.modules['frappe']=previous

class NotificationTests(unittest.TestCase):
    def setUp(self):
        fake.session.user='user@example.com'
        fake.db.count.reset_mock();fake.get_all.reset_mock()
        fake.get_all.return_value=[{'name':'note-one','subject':'<b>Reminder</b>'}]
        fake.parse_json=__import__('json').loads
        fake.get_doc=Mock(return_value=types.SimpleNamespace(for_user=fake.session.user))
        fake.delete_doc=Mock()
    def test_guest_cannot_read_pending_workflows(self):
        fake.session.user='Guest'
        with self.assertRaises(PermissionError): notifications.get_notifications()

    def test_pending_uses_native_conditions_and_approval_access(self):
        workflow=types.SimpleNamespace(document_type='Order', workflow_state_field='status',
            transitions=[types.SimpleNamespace(state='Pending', allowed='Approver')])
        doc=types.SimpleNamespace(doctype='Order', name='ORDER-1', docstatus=0, modified='2026-10-29',
            get=lambda field: 'Pending')
        fake.get_roles=Mock(return_value=['Approver'])
        fake.has_permission=Mock(return_value=True)
        fake.get_all.return_value=[types.SimpleNamespace(name='Approval')]
        fake.get_list=Mock(return_value=[types.SimpleNamespace(name='ORDER-1')])
        fake.get_doc.side_effect=lambda dt, name: workflow if dt=='Workflow' else doc
        fake.as_json=__import__('json').dumps
        native.get_transitions.return_value=[types.SimpleNamespace(action='Approve')]
        native.has_approval_access.return_value=True
        result=notifications.get_notifications()
        self.assertEqual(result['pending_count'],1)
        self.assertEqual(result['notifications'][0]['actions'],['Approve'])
        native.has_approval_access.return_value=False
        self.assertEqual(notifications.get_notifications()['pending_count'],0)
        native.has_approval_access.return_value=True
        native.get_transitions.return_value=[]
        self.assertEqual(notifications.get_notifications()['pending_count'],0)

    def test_draft_workflow_states_are_excluded_but_pending_drafts_remain(self):
        workflow=types.SimpleNamespace(document_type='Order', workflow_state_field='status',
            transitions=[types.SimpleNamespace(state=state, allowed='Approver')
                         for state in ('Draft', ' draft ', 'DRAFT', 'Pending')])
        docs={state:types.SimpleNamespace(doctype='Order',name=state,modified='2026-10-29',
                    docstatus=0,get=lambda field,state=state:state)
              for state in ('Draft',' draft ','DRAFT','Pending')}
        fake.get_roles=Mock(return_value=['Approver'])
        fake.has_permission=Mock(return_value=True)
        fake.get_all.return_value=[types.SimpleNamespace(name='Approval')]
        fake.get_list=Mock(return_value=[types.SimpleNamespace(name=name) for name in docs])
        fake.get_doc.side_effect=lambda dt,name: workflow if dt=='Workflow' else docs[name]
        fake.as_json=__import__('json').dumps
        native.get_transitions.return_value=[types.SimpleNamespace(action='Approve')]
        native.has_approval_access.return_value=True
        result=notifications.get_notifications()
        self.assertEqual(result['pending_count'],1)
        self.assertEqual(result['notifications'][0]['state'],'Pending')
        self.assertEqual(fake.get_list.call_args.kwargs['filters']['status'],['in',['Pending']])

    def test_submitted_and_cancelled_documents_never_enter_pending_list(self):
        workflow=types.SimpleNamespace(document_type='Order',workflow_state_field='status',
            transitions=[types.SimpleNamespace(state='Approved',allowed='Approver')])
        doc=types.SimpleNamespace(doctype='Order',name='ORDER-1',docstatus=1,
            modified='2026-10-29',get=lambda field:'Approved')
        fake.get_roles=Mock(return_value=['Approver'])
        fake.has_permission=Mock(return_value=True)
        fake.get_all.return_value=[types.SimpleNamespace(name='Approval')]
        fake.get_list=Mock(return_value=[types.SimpleNamespace(name=doc.name)])
        fake.get_doc.side_effect=lambda dt,name:workflow if dt=='Workflow' else doc
        native.get_transitions.reset_mock()
        for docstatus in (1,2):
            doc.docstatus=docstatus
            result=notifications.get_notifications()
            self.assertEqual(result,{'pending_count':0,'notifications':[]})
            self.assertEqual(fake.get_list.call_args.kwargs['filters']['docstatus'],0)
        native.get_transitions.assert_not_called()

    def test_owner_popup_only_after_state_changes_and_commit(self):
        fake.get_cached_doc=Mock(return_value=types.SimpleNamespace(workflow_state_field='status'))
        fake.publish_realtime=Mock()
        doc=types.SimpleNamespace(doctype='Order',name='ORDER-1',docstatus=1,owner='owner@example.com',
            get_doc_before_save=lambda: types.SimpleNamespace(get=lambda field:'Pending'),
            get=lambda field:'Approved')
        notifications.notify_workflow_owner(doc)
        self.assertEqual(fake.publish_realtime.call_args.kwargs,
                         {'user':'owner@example.com','after_commit':True})
        fake.publish_realtime.reset_mock()
        doc.get=lambda field:'Pending'
        notifications.notify_workflow_owner(doc)
        fake.publish_realtime.assert_not_called()

    def test_delete_only_selected_own_notifications_and_deduplicate(self):
        self.assertEqual(notifications.delete_notifications('["one","two","one"]'), {'deleted':2})
        self.assertEqual([call.args for call in fake.delete_doc.call_args_list],
            [('Notification Log','one'),('Notification Log','two')])
        self.assertTrue(all(call.kwargs['for_update'] for call in fake.get_doc.call_args_list))

    def test_mixed_ownership_selection_deletes_nothing(self):
        fake.get_doc.side_effect=[types.SimpleNamespace(for_user=fake.session.user),
                                  types.SimpleNamespace(for_user='another@example.com')]
        with self.assertRaises(PermissionError): notifications.delete_notifications(['own','other'])
        fake.delete_doc.assert_not_called()

    def test_guest_and_invalid_deletions_are_rejected(self):
        for names in ([], {}, [''], [1], ['one']*501):
            with self.assertRaises(PermissionError): notifications.delete_notifications(names)
        fake.session.user='Guest'
        with self.assertRaises(PermissionError): notifications.delete_notifications(['one'])
        fake.get_doc.assert_not_called()
        fake.delete_doc.assert_not_called()

if __name__=='__main__':unittest.main()
