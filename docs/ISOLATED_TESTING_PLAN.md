# Smart Chama Isolated Testing Plan

## Purpose
Test member access and connected modules without deleting or altering existing Smart Chama production records.

## Environment separation
- Production project: `kbrhjgnwbkszmjldbfor` (Smart chama). Treat as read-only for test setup; never seed demo rows here.
- Code-only test branch: `testing/isolated-member-access`.
- A dedicated Supabase database branch is the preferred integration-test target. The quoted cost was explicitly approved, but Supabase rejected creation because branching requires the Pro plan or above. No test branch was created. If the plan is upgraded, create a fresh branch; it applies schema migrations but does not copy production table data. Until then, continue code-only tests and do not use production for test signups or fixtures.
- Do not use the separate Kilimanjaro Campus project as a test database; it is a separate project.

## Test data policy
- Use invented names, test email inboxes controlled by the tester, and non-real phone numbers where accepted by validation.
- Never use real national ID values, real member phone numbers, actual M-Pesa payments, real receipts, or live financial references.
- Do not create fake successful Daraja callback evidence or mark payment rows as successful.
- No production data deletion, truncation, status edits, or financial reconciliation is part of testing.

## Member access acceptance tests
1. Signed-out visitor can open the portal and member-access page but cannot read group/member financial data.
2. Demo credentials do not authenticate.
3. Valid registered user can sign in and is redirected to the live dashboard.
4. Invalid password and unconfirmed account are handled without exposing sensitive account details.
5. Password reset only reports generic success and uses the configured HTTPS callback URL.
6. Sign-out clears the active Supabase session and protected views return to signed-out state.
7. A new user has no group access until a membership request is approved.
8. A member sees only their own memberships and permitted group records.
9. A chairperson/secretary sees roster data only in groups where their role is assigned; removing the role removes access after refresh.
10. A regular member cannot invoke owner/admin, membership approval, loan review, savings approval, repayment, or disbursement operations.

## Loan integration acceptance tests
1. The main portal links to the loan page.
2. The loan page detects the same signed-in Supabase session; signed-out users are directed to member access.
3. Only active/approved memberships can apply.
4. Savings eligibility is computed server-side from approved savings transactions; requested amount above three times eligible savings is rejected.
5. Application review requires a permitted group role and does not itself imply disbursement.
6. Loan schedules and repayments are visible only to the member and authorized officers under database policy.
7. Repayment requires an active, previously disbursed loan and a unique verified reference.
8. No live loan disbursement is attempted in integration testing.

## Security/release gates
- Enable Supabase leaked-password protection in Auth settings.
- Review every exposed SECURITY DEFINER function individually; do not blanket grant or revoke permissions without understanding the call path.
- Keep RLS enabled and test both positive and negative access paths.
- Verify M-Pesa callback with Daraja sandbox and idempotency tests only after callback credentials and environment are isolated.
- Do not use production keys, callback tokens, or service-role credentials in browser code or test fixtures.
- Keep secrets in Supabase Edge Function secrets; rotate callback authentication material if it may have been exposed in logs.
- Record each test result, environment ref, timestamp, and evidence without storing passwords, tokens, or personal financial data.

## Current limitations to resolve
- Main portal and loan page now have a navigation link, but shared-session behavior must still be tested in a browser.
- The legacy member page's former demo login was disabled and successful authentication now redirects to the live dashboard; verify registration, confirmation, reset, and sign-out in the isolated environment.
- The dashboard and loan page currently point to the production Supabase project. Do not run test signups or seed data against that project. Configure a dedicated test project/branch URL and publishable key for the test build before end-to-end tests.
- A test database branch has not yet been created: the user approved the quoted $0.01344/hour cost, but Supabase returned a plan restriction (Pro or above required). Production records remain untouched. The stale demo-login instructions were removed on the testing branch; verify the rendered page and login flow before release.

## Go-live rule
No production rollout until the isolated tests pass, security advisor findings are triaged, Daraja callbacks are verified in sandbox, and all user-facing modules are confirmed to share the correct authenticated session.


## Code review notes (2026-10-20)
- The member-access and loan pages both use the same Supabase project URL and publishable key. Supabase JS clients normally share the browser's persisted auth session for the same project and origin; this is a code-level expectation, not a completed browser test.
- The loan page currently shows committee-review and repayment controls before the database has established whether the current user is authorized. Database RPC authorization remains the actual security boundary, but the UI should be role-gated to reduce confusion and avoid presenting privileged actions to ordinary members.
- The loan page currently loads the production project configuration. Do not perform test signups, loan submissions, review decisions, or repayment writes from this page until a separate test backend is configured.
- No browser-based end-to-end tests have been run in this environment. Mark tests as pending rather than passed until there is an isolated backend and test account.


## Latest production security-advisor snapshot (2026-10-20)
Read-only advisor checks reported:
- Leaked-password protection is disabled. Enable it in Supabase Auth settings; this is a dashboard setting and was not changed automatically.
- Fourteen authenticated-callable SECURITY DEFINER functions are flagged. Review each function's internal authorization and intended client call path individually; do not blanket-revoke execution because legitimate member/officer workflows may depend on these RPCs.
- `public.mpesa_payments` has RLS enabled and no policies. Treat as service-role-only unless a reviewed requirement demonstrates otherwise; do not add broad policies just to clear the warning.
- Performance advisor reports overlapping permissive SELECT policies on `chama_groups`, `chama_member_roles`, `chama_members`, and `savings_transactions`. Review policy semantics and consolidate only with equivalent positive/negative authorization tests.
- Twelve indexes are reported unused at the time of the snapshot. Do not drop them until query patterns and production usage have been assessed.
- These checks were read-only. No production SQL, auth settings, records, or policies were changed.

## Privileged RPC review — read-only inventory (2026-10-20)
A read-only inspection of the 14 advisor-flagged function definitions confirmed that they are SECURITY DEFINER routines and are executable by authenticated users. This advisor finding is not, by itself, proof of an exploit: these routines may be intentionally callable through the client, but each must enforce authorization inside the function.

- **Authorization checks visibly present in the inspected excerpt:** `admin_create_chama_group` checks `auth.uid()` and the system-admin table; `assign_chama_role` restricts role assignment to the group chairperson and requires an active target member; `record_loan_repayment` checks an allowed officer role and requires an active, disbursed loan; `review_loan_application` checks a loan-committee role and rechecks eligibility before approval; `submit_savings_deposit` binds the member ID to `auth.uid()` and validates the amount.
- **Needs complete-body review before any permission change:** `approve_chama_member`, `officer_approve_savings_deposit`, `officer_delete_pending_deposit`, `officer_reject_savings_deposit`, `owner_assign_group_role`, `owner_update_member_status`, `remove_chama_member`, `request_chama_membership`, and `review_chama_membership`. Their excerpts contain some authentication/authorization logic, but the excerpt-only inspection is not sufficient to certify every branch or side effect.
- Some older functions set `search_path` to `public`, while newer hardened functions use an empty search path and schema-qualify objects. Review and migrate individually after inspecting the full function body and call sites; do not perform a blanket rewrite.
- No function definitions, grants, records, or production settings were changed by this inspection.

## Manual acceptance checklist — run only after an isolated backend exists
Use a dedicated test project/branch and test accounts. Do not use the production project for any write test.

1. **Authentication:** sign in through Member Access, open Dashboard and Loans in the same browser, refresh both, and verify the session remains signed in. Sign out from Dashboard and verify the other page no longer grants access after refresh.
2. **Member permissions:** a regular member should see only their own permitted information; direct attempts to view another member's roster or submit for another member must fail.
3. **Loan UI and RPC authorization:** a regular member must not be able to approve/reject applications or record repayments. An assigned officer may review only applications in their group. Approval must not mark funds as disbursed.
4. **Loan eligibility:** reject zero/negative amounts and amounts above three times current approved savings; confirm approval rechecks savings and generates the schedule. Do not test by creating production applications.
5. **Repayment:** reject repayments for undistributed/inactive loans, duplicate references, non-positive amounts, and amounts above outstanding balance. Verify schedule allocation and balance after a successful test repayment.
6. **Daraja sandbox:** use sandbox credentials and a controlled test number; verify callback authentication, checkout ID, amount, phone and receipt checks; replay the same callback and confirm idempotency. Never simulate or manually claim a real payment.
7. **Security regression:** confirm unauthenticated access is denied, non-member and wrong-group access is denied, and authorized users retain only intended actions. Record screenshots and request IDs without exposing credentials or callback tokens.

**Current test status:** all items above are pending. The production project must remain read-only for testing until a separate backend is available. Do not treat static review or a successful Pages build as end-to-end verification.

## Test-branch UI change (2026-10-20)
- Updated `smart_chama_loans.html` on `testing/isolated-member-access` to check the signed-in user's `chama_member_roles` for the groups where they have an approved membership.
- The committee-review and repayment sections are hidden unless a recognized loan-officer role is returned. If the role lookup errors, both sections stay hidden (fail-closed UI behavior).
- This is a usability/defense-in-depth measure only. Database authorization remains authoritative; UI hiding is not a security boundary.
- Static source verification confirmed the new role gate and both section toggles are present. No browser execution, role-account test, or end-to-end test has been run. This branch remains un-deployed and uses the production Supabase configuration; do not submit/write test data from it.

## Automated static-check result (2026-10-20)
- GitHub Actions workflow `Smart Chama Test-Branch Static Safety Checks` completed successfully for commit `c3399f8288f83e0fcab011773e5954d5d2cd4754` (run ID `39429434100`).
- The run exercised the repository's five static assertions. It does not execute the HTML in a browser, connect to Supabase as a user, or exercise Daraja callbacks.
- Latest read-only Supabase branch listing still shows only the production project's default `main` branch. No isolated Supabase test database exists yet.
- Continue treating the GitHub branch as code-only and production as read-only for testing.

## Unified login preparation update (2026-10-20)
- The central sign-in now checks for an existing Supabase session after the browser client loads and routes an already-authenticated user to the live dashboard.
- Login submission handles authentication errors, prevents duplicate submits while checking credentials, and routes successful authentication to the same dashboard.
- Added static assertions for session reuse, sign-in routing, role-normalized workspace navigation, and local HTML link targets.
- Latest static workflow: https://github.com/karkuresl-stack/Smart-chama/actions/runs/39435205386 (success).
- These are code/static checks only. They do not prove browser session behavior, production authorization, or financial workflows. Keep the pull request in draft and do not run test signups or financial writes against production.
