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
previous=sys.modules.get('frappe');sys.modules['frappe']=fake
spec.loader.exec_module(notifications)
if previous is None:del sys.modules['frappe']
else:sys.modules['frappe']=previous

class NotificationTests(unittest.TestCase):
    def setUp(self):
        fake.session.user='user@example.com'
        fake.db.count.reset_mock();fake.get_all.reset_mock()
        fake.get_all.return_value=[{'name':'note-one','subject':'<b>Reminder</b>'}]
    def test_summary_has_exact_count_and_session_recipient_filters(self):
        result=notifications.get_notifications()
        self.assertEqual(result,{'unread_count':37,'notifications':[{'name':'note-one','subject':'Reminder','creation':''}]})
        fake.db.count.assert_called_once_with('Notification Log',filters={'for_user':fake.session.user,'read':0})
        self.assertEqual(fake.get_all.call_args.kwargs['filters'],{'for_user':fake.session.user,'read':0})
        self.assertEqual(fake.get_all.call_args.kwargs['limit_page_length'],20)
    def test_guest_cannot_read_and_administrator_still_only_gets_own_notifications(self):
        fake.session.user='Guest'
        with self.assertRaises(PermissionError):notifications.get_notifications()
        fake.db.count.assert_not_called()
        fake.session.user='Administrator'
        notifications.get_notifications()
        self.assertEqual(fake.get_all.call_args.kwargs['filters']['for_user'],'Administrator')

if __name__=='__main__':unittest.main()
