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
