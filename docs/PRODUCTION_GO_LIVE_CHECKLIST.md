# Smart Chama V4 — Production Go-Live Checklist

This checklist records the current production gates. A successful GitHub Pages build confirms the static site was published; it does not certify financial workflows or backend security.

## Current known status

- GitHub Pages deployment workflow: latest checked run succeeded.
- Supabase project: `kbrhjgnwbkszmjldbfor`.
- M-Pesa Edge Functions are active, but the complete Daraja flow has not been verified end-to-end.
- `smooth-action` currently defaults `MPESA_ENVIRONMENT` to `sandbox` when the variable is absent. Production must use an explicit, validated environment setting.
- Callback failure paths currently acknowledge some server/configuration failures with a success-shaped Daraja response. Review retry and recovery semantics before go-live.
- The M-Pesa callback endpoint is unauthenticated at the platform JWT layer, so its callback-specific authentication and replay protection must be tested carefully. Never put callback tokens in source control, client code, or logs.
- The loan disbursement RPC is intentionally not executable by `authenticated` or `anon` roles while the disbursement confirmation workflow is redesigned.
- Leaked-password protection is reported disabled in Supabase Auth and must be enabled in the dashboard.
- No live payment, payment reconciliation, loan approval, or loan disbursement test has been performed as part of this checklist.

## Gate A — Authentication and access control

- [ ] Enable leaked-password protection in Supabase Auth.
- [ ] Test sign-up, sign-in, sign-out, password reset, and expired-session behavior.
- [ ] Test every officer/admin RPC with an ordinary member, a different group's officer, and an unauthenticated client.
- [ ] Confirm RLS blocks cross-group member, savings, loan, and audit-record reads.
- [ ] Review each SECURITY DEFINER function individually; do not remove grants in bulk without checking UI dependencies and function-level authorization.
- [ ] Rotate callback authentication material if it may have appeared in historical URLs or logs; update the configured callback consistently.

## Gate B — Daraja sandbox verification

Use a dedicated sandbox group/member and Safaricom test credentials. Never use a real member's live payment as a test.

- [ ] Confirm environment is explicitly configured and is not silently defaulted.
- [ ] Test a successful STK request and retain its CheckoutRequestID.
- [ ] Test user cancellation, timeout, invalid phone, insufficient funds/sandbox failure, and malformed callback payloads.
- [ ] Verify callback authentication, CheckoutRequestID binding, receipt, amount, and phone validation.
- [ ] Deliver the same callback twice and confirm it cannot create duplicate savings transactions.
- [ ] Simulate database/Daraja lookup failure and verify the system can recover/reconcile later rather than silently losing a payment.
- [ ] Verify logs never contain access tokens, passkeys, callback tokens, full sensitive payloads, or unnecessary phone data.
- [ ] Confirm payment status changes only after server-side Daraja verification; do not trust the browser's success message.

## Gate C — Existing payment records

The last reviewed database snapshot contained 9 M-Pesa payment records, including pending and failed records. Their database status alone does not establish whether Safaricom charged the customer.

- [ ] Match each pending/failed CheckoutRequestID against authoritative Daraja records.
- [ ] Reconcile only with verified transaction evidence using the approved server-side workflow.
- [ ] Never manually mark a payment successful to clear a dashboard warning.
- [ ] Preserve the audit trail for any correction or recovery.

## Gate D — Loans

- [ ] Test server-side savings eligibility and the 3x savings cap.
- [ ] Test committee authorization and rejection/approval paths.
- [ ] Verify installment schedule totals and due dates.
- [ ] Design a verified, audited disbursement process before re-enabling the disbursement RPC.
- [ ] Require authoritative transfer evidence before recording a disbursement; do not treat an officer-entered reference alone as proof of transfer.
- [ ] Verify repayment idempotency, reference uniqueness, outstanding-balance limits, and allocation totals.
- [ ] Test with isolated synthetic records in a non-production environment; do not create fake live financial history.

## Gate E — Release and operations

- [ ] Confirm the latest GitHub Actions site deployment is successful.
- [ ] Smoke-test the deployed sign-in, group selection, savings, loans, and reporting screens on mobile and desktop.
- [ ] Verify backup/restore procedure and establish incident-response contacts.
- [ ] Review Supabase Security and Performance Advisors and document accepted exceptions.
- [ ] Configure a custom domain only after DNS, HTTPS, and canonical URL behavior can be verified.
- [ ] Go live only after all critical gates above have evidence attached.

## Evidence log

Record date, environment, test case, expected result, actual result, and operator for each test. Do not store secrets, passkeys, or full payment credentials in this file.
