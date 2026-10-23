# Workflow transition System Notifications

## Deploy

This extension adds Custom Fields to Workflow Transition and Notification. Deploy all app files, then run from the bench directory:

```sh
bench --site your-site migrate
bench build --app c4style
bench --site your-site clear-cache
bench restart
```

Migration runs the idempotent Custom Field installer. It does not generate or enable notification rules automatically. Frappe core files are not modified.

## Configure

1. Save the Workflow, including its Transition Rules.
2. Open a transition row. **Create System Notification** appears beside **Send Email To Creator**.
3. Click it to open a new, unsaved native Notification. Review its subject/message and save. Clicking the button again opens that row's saved rule.
4. The generated rule uses the Workflow's Document Type, System Notification channel and Custom event. Its recipients are `owner` and the same transition row's `Allowed` role. The copied condition appears as the read-only **Transition Condition**.
5. Disable the native Notification rule to stop its alerts. Saving changes to the Workflow keeps the generated routing and condition snapshot synchronized.

Users need write access to the Workflow and create access to Notification to create a rule. Existing-rule access also checks the Notification's read permission. Existing Send Email To Creator behavior is left to Frappe.

## Execution

The normal workflow API delegates the actual action and permission decisions to Frappe. It carries the selected row's identity into document hooks. Before a state change, the hooks use the native workflow evaluator on the saved pre-transition document, preserving expressions using `frappe.session.user`. A false condition, missing role, self-approval restriction, inactive Workflow or disabled rule prevents delivery.

After a successful save/submit/cancel/update-after-submit, logs are created for the document owner and enabled users with the selected Allowed role. Document-level read access is checked for every recipient; duplicate recipients are removed. The actor is included when eligible. Subjects/messages support `doc` and `transition` template variables (`state`, `action`, `next_state`, `allowed`). Logs reference the document, and the existing badge/popup/bell integration receives their native realtime events after commit.

Notification log writes use the document's transaction; a failed operation does not leave a committed alert. Template or log insertion errors also fail that transaction. Core bulk processing retains its per-document commits and rollback behavior, with the action carried into both immediate and queued batches.

For direct document saves or other background calls that do not provide an action, a single eligible source/destination transition can be identified. If several actions lead to the same destination and no action context exists, the extension logs an ambiguity and skips the notification rather than guessing. Ordinary saves without a state change do not alert. Same-state workflow actions require an explicit action context.

A unique rule key prevents duplicate configurations for one row. A per-save delivery flag prevents lifecycle hooks such as on_update and on_submit from delivering twice. Actual repeated workflow executions remain separate events.

## Validation and post-deployment smoke test

Standalone checks (`python -B -m unittest discover -s tests -v`) use mocked Frappe services for backend contracts and real Chromium for the button/prefilled-form behavior. They cover permissions, condition timing, owner/role selection, disabled users, document access, duplicate recipients/rules, exact action context, bulk processing and unrelated saves. They do not substitute for a real Frappe transaction test.

A read-only pre-deployment check against oro.connect4systems.com confirmed the required channel, Custom event, transition fields and Notification Log fields. See `artifacts/workflow-review/deployed-capabilities.json`. No live Workflow, Notification or Notification Log records were created during that check.

After deploying/migrating, use a dedicated test document and Workflow:

1. Create a row with an owner/session condition and an Allowed role, then generate and save its Notification.
2. Reopen the button and verify it opens the existing rule.
3. Execute the action as an eligible user; check exactly one log per permitted recipient, including an owner who also holds the role.
4. Repeat with a false condition, disabled rule, disabled recipient and a role user without document read access. Confirm no unintended logs appear.
5. Exercise bulk transitions and a submitted-document transition on the target Frappe version. Verify that a failed transaction creates no committed notification.
