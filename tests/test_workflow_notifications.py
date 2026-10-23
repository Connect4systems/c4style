"""Standalone contract checks for the workflow extension; core Frappe is mocked."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock

class Attr(dict):
    __getattr__=dict.get
    __setattr__=dict.__setitem__
    def set(self,key,value): self[key]=value
    def is_new(self): return False
    def check_permission(self,*args): pass
    def get_doc_before_save(self): return self.get('before')

class WorkflowNotificationTests(unittest.TestCase):
    def setUp(self):
        self.row=Attr(name='row-one',state='Draft',action='Approve',next_state='Approved',allowed='Approver',condition='doc.amount > 0')
        self.workflow=Attr(name='Test Workflow',document_type='ToDo',workflow_state_field='workflow_state',is_active=1,transitions=[self.row])
        self.before=Attr(doctype='ToDo',name='TODO-1',owner='owner@example.com',workflow_state='Draft',amount=100)
        self.after=Attr(doctype='ToDo',name='TODO-1',owner='owner@example.com',workflow_state='Approved',amount=0,before=self.before,flags=Attr())
        self.existing=True;self.logs=[]
        self.frappe=types.ModuleType('frappe');self.frappe.whitelist=lambda **kwargs:lambda fn:fn
        self.frappe.session=Attr(user='actor@example.com');self.frappe.PermissionError=PermissionError
        def throw(message,exc=ValueError):raise exc(message)
        self.frappe.throw=throw;self.frappe.parse_json=lambda value:__import__('json').loads(value)
        self.frappe.db=Attr(get_value=Mock(side_effect=lambda doctype,filters,field: 'Rule 1' if self.existing else None),set_value=Mock())
        self.frappe.clear_document_cache=Mock();self.frappe.log_error=Mock()
        self.frappe.enqueue=Mock();self.frappe.msgprint=Mock()
        self.frappe.has_permission=Mock(side_effect=lambda *args,**kwargs:kwargs.get('user')!='denied@example.com')
        self.frappe.get_all=Mock(side_effect=lambda doctype,**kwargs: ['owner@example.com','reader@example.com','reader@example.com','denied@example.com','disabled@example.com'] if doctype=='Has Role' else ['owner@example.com','reader@example.com','denied@example.com'])
        self.frappe.render_template=Mock(side_effect=lambda text,context:'Rendered '+context['doc'].name)
        self.frappe.get_doc=Mock(side_effect=self.get_doc)
        core=types.ModuleType('frappe.model.workflow');core.get_workflow_name=Mock(return_value='Test Workflow')
        core.get_workflow=Mock(return_value=self.workflow);core.get_transitions=Mock(return_value=[self.row])
        core.has_approval_access=Mock(return_value=True);core.apply_workflow=Mock(return_value=self.after)
        core._bulk_workflow_action=Mock()
        self.core=core
        self.previous={name:sys.modules.get(name) for name in ('frappe','frappe.model','frappe.model.workflow')}
        sys.modules['frappe']=self.frappe;sys.modules['frappe.model']=types.ModuleType('frappe.model');sys.modules['frappe.model.workflow']=core
        spec=importlib.util.spec_from_file_location('workflow_under_test',Path(__file__).parents[1]/'c4style/workflow_notifications.py')
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        self.rule=Attr(name='Rule 1',enabled=1,channel='System Notification',event='Custom',document_type='ToDo',subject='{{ doc.name }}',message='Approved',c4style_workflow=self.workflow.name,c4style_transition=self.row.name,c4style_transition_key=self.module._key(self.workflow.name,self.row.name))
    def tearDown(self):
        for name,value in self.previous.items():
            if value is None:sys.modules.pop(name,None)
            else:sys.modules[name]=value
    def get_doc(self,doctype,name=None):
        if isinstance(doctype,dict):
            log=Attr(doctype)
            log.insert=lambda **kwargs:self.logs.append(log)
            return log
        if doctype=='Workflow':return self.workflow
        if doctype=='Notification':return self.rule
        return self.before
    def test_button_prefills_native_custom_rule_and_never_sends_a_notification(self):
        self.existing=False
        result=self.module.prepare_notification(self.workflow.name,self.row.name)['defaults']
        self.assertEqual(result['document_type'],'ToDo');self.assertEqual(result['event'],'Custom')
        self.assertEqual(result['channel'],'System Notification')
        self.assertEqual(result['c4style_transition_condition'],self.row.condition)
        self.assertEqual(result['recipients'],[{'receiver_by_document_field':'owner'},{'receiver_by_role':'Approver'}])
        self.assertEqual(self.logs,[])
    def test_button_reopens_existing_rule_and_rejects_missing_or_unauthorized_rows(self):
        self.assertEqual(self.module.prepare_notification(self.workflow.name,self.row.name),{'existing':'Rule 1'})
        with self.assertRaises(ValueError):self.module.prepare_notification(self.workflow.name,'missing')
        object.__setattr__(self.workflow,'check_permission',Mock(side_effect=PermissionError))
        with self.assertRaises(PermissionError):self.module.prepare_notification(self.workflow.name,self.row.name)
    def test_guests_and_users_without_notification_create_permission_cannot_prepare(self):
        self.existing=False;self.frappe.has_permission.return_value=False;self.frappe.has_permission.side_effect=None
        with self.assertRaises(PermissionError):self.module.prepare_notification(self.workflow.name,self.row.name)
        self.frappe.session.user='Guest'
        with self.assertRaises(PermissionError):self.module.prepare_notification(self.workflow.name,self.row.name)
    def test_validation_keeps_source_routing_and_detects_duplicate_rules(self):
        self.rule.recipients=[{'receiver_by_role':'System Manager'}];self.rule.event='Save';self.rule.condition='unsafe'
        self.module.validate_notification(self.rule)
        self.assertEqual(self.rule.event,'Custom');self.assertEqual(self.rule.condition,'')
        self.assertEqual(self.rule.recipients[-1],{'receiver_by_role':'Approver'})
        self.rule.name='Other rule'
        with self.assertRaises(ValueError):self.module.validate_notification(self.rule)
    def test_condition_is_evaluated_on_pre_transition_document(self):
        self.module.capture_transition(self.after)
        self.core.get_transitions.assert_called_once_with(self.before,self.workflow)
        self.assertEqual(self.before.amount,100);self.assertEqual(self.after.amount,0)
        self.assertEqual(self.after.flags.c4style_transition_notification['row'],'row-one')
    def test_false_condition_or_disallowed_role_or_self_approval_prevents_delivery(self):
        self.core.get_transitions.return_value=[]
        self.module.capture_transition(self.after);self.module.deliver_transition(self.after)
        self.assertEqual(self.logs,[])
        self.core.get_transitions.return_value=[self.row];self.core.has_approval_access.return_value=False
        self.module.capture_transition(self.after);self.module.deliver_transition(self.after)
        self.assertEqual(self.logs,[])
    def test_only_owner_and_enabled_role_users_with_document_access_receive_one_log(self):
        self.module.capture_transition(self.after)
        self.module.deliver_transition(self.after);self.module.deliver_transition(self.after)
        self.assertEqual([log.for_user for log in self.logs],['owner@example.com','reader@example.com'])
        self.assertTrue(all(log.document_type=='ToDo' and log.document_name=='TODO-1' and log.from_user=='actor@example.com' for log in self.logs))
        self.assertEqual(self.frappe.get_all.call_args_list[0].kwargs['filters'],{'role':'Approver','parenttype':'User'})
    def test_disabled_wrong_doctype_or_unlinked_rules_do_not_send(self):
        for values in ({'enabled':0},{'document_type':'User'},{'channel':'Email'},{'event':'Save'},{'c4style_transition_key':'wrong'}):
            with self.subTest(values=values):
                old={key:self.rule[key] for key in values};self.rule.update(values)
                self.module.capture_transition(self.after);self.module.deliver_transition(self.after)
                self.assertEqual(self.logs,[]);self.rule.update(old)
    def test_unrelated_saves_do_not_notify_and_ambiguous_actions_are_not_guessed(self):
        self.after.workflow_state='Draft';self.module.capture_transition(self.after)
        self.assertIsNone(self.after.flags.c4style_transition_notification)
        self.after.workflow_state='Approved'
        other=Attr(self.row);other.name='other-row';other.action='Different action'
        self.core.get_transitions.return_value=[self.row,other]
        self.module.capture_transition(self.after)
        self.assertIsNone(self.after.flags.c4style_transition_notification)
        self.frappe.log_error.assert_called_once()
    def test_wrapper_preserves_exact_action_and_restores_context_even_on_failure(self):
        def native(doc,action):
            self.assertEqual(self.module._active_transition.get(),('ToDo','TODO-1','row-one'))
            self.module.capture_transition(self.after)
            return self.after
        self.core.apply_workflow.side_effect=native
        self.assertIs(self.module.apply_workflow({'doctype':'ToDo','name':'TODO-1'},'Approve'),self.after)
        self.assertIsNone(self.module._active_transition.get())
        self.core.apply_workflow.side_effect=ValueError('Core workflow failed')
        with self.assertRaises(ValueError):self.module.apply_workflow({'doctype':'ToDo','name':'TODO-1'},'Approve')
        self.assertIsNone(self.module._active_transition.get());self.assertEqual(self.logs,[])
    def test_same_state_action_requires_explicit_matching_action_context(self):
        self.row.next_state='Draft';self.after.workflow_state='Draft'
        self.module.capture_transition(self.after);self.assertIsNone(self.after.flags.c4style_transition_notification)
        token=self.module._active_transition.set(('ToDo','TODO-1','row-one'))
        try:
            self.module.capture_transition(self.after)
            self.assertIsNotNone(self.after.flags.c4style_transition_notification)
        finally:self.module._active_transition.reset(token)

    def test_bulk_worker_keeps_exact_action_for_ambiguous_destinations(self):
        other=Attr(self.row);other.name='different';other.action='Different action'
        self.core.get_transitions.return_value=[self.row,other]
        self.core._bulk_workflow_action.side_effect=lambda *args:self.module.capture_transition(self.after)
        self.module.bulk_workflow_approval(['TODO-1'],'ToDo','Approve')
        self.assertEqual(self.after.flags.c4style_transition_notification['row'],'row-one')
        self.assertIsNone(self.module._active_bulk_action.get())
        self.module.bulk_workflow_approval(['TODO-1']*20,'ToDo','Approve')
        self.assertEqual(self.frappe.enqueue.call_args.args[0],'c4style.workflow_notifications.bulk_workflow_action')
        self.assertEqual(self.frappe.enqueue.call_args.kwargs['action'],'Approve')
        with self.assertRaises(ValueError):self.module.bulk_workflow_approval(['TODO-1']*501,'ToDo','Approve')

    def test_bulk_same_state_action_is_captured(self):
        self.row.next_state='Draft';self.after.workflow_state='Draft'
        self.core._bulk_workflow_action.side_effect=lambda *args:self.module.capture_transition(self.after)
        self.module.bulk_workflow_action(['TODO-1'],'ToDo','Approve')
        self.assertEqual(self.after.flags.c4style_transition_notification['row'],'row-one')

    def test_installer_adds_ordered_controls_and_unique_rule_identity_idempotently(self):
        name='frappe.custom.doctype.custom_field.custom_field'
        previous=sys.modules.get(name);fake=types.ModuleType(name);fake.create_custom_fields=Mock()
        sys.modules[name]=fake
        try:
            spec=importlib.util.spec_from_file_location('installer_under_test',Path(__file__).parents[1]/'c4style/install_workflow_notifications.py')
            installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)
            installer.install();installer.install()
            self.assertEqual(fake.create_custom_fields.call_args_list[0],fake.create_custom_fields.call_args_list[1])
            fields=fake.create_custom_fields.call_args.args[0]
            self.assertEqual(fields['Workflow Transition'][0]['insert_after'],'send_email_to_creator')
            identity=next(field for field in fields['Notification'] if field['fieldname']=='c4style_transition_key')
            self.assertEqual(identity['unique'],1)
            self.assertEqual(fake.create_custom_fields.call_args.kwargs,{'update':True})
        finally:
            if previous is None:sys.modules.pop(name,None)
            else:sys.modules[name]=previous

    def test_hooks_capture_all_save_submit_cancel_and_submitted_update_lifecycles(self):
        import runpy
        hooks=runpy.run_path(str(Path(__file__).parents[1]/'c4style/hooks.py'))['doc_events']['*']
        for event in ('before_validate','before_cancel','before_update_after_submit'):
            self.assertEqual(hooks[event],'c4style.workflow_notifications.capture_transition')
        for event in ('on_update','on_submit','on_cancel','on_update_after_submit'):
            self.assertEqual(hooks[event],'c4style.workflow_notifications.deliver_transition')

if __name__=='__main__':unittest.main()
