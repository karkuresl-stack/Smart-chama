from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LOANS = (ROOT / "smart_chama_loans.html").read_text(encoding="utf-8")
MEMBER = (ROOT / "smart_chama_supabase_ready-2.html").read_text(encoding="utf-8")
DASHBOARD = (ROOT / "smart_chama_live_dashboard.html").read_text(encoding="utf-8")
PORTAL = (ROOT / "smart_chama_main.html").read_text(encoding="utf-8")
PLAN = (ROOT / "docs" / "ISOLATED_TESTING_PLAN.md").read_text(encoding="utf-8")


class StaticSafetyChecks(unittest.TestCase):
    def test_loan_officer_controls_fail_closed(self):
        self.assertIn('const canReview=!roleResult.error&&authorizedGroups.size>0;', LOANS)
        self.assertIn('$("committeeCard").hidden=!canReview;', LOANS)
        self.assertIn('$("repaymentCard").hidden=!canReview;', LOANS)

    def test_loan_review_and_repayment_remain_server_rpc_calls(self):
        self.assertIn('db.rpc("review_loan_application"', LOANS)
        self.assertIn('db.rpc("record_loan_repayment"', LOANS)

    def test_application_copy_does_not_claim_disbursement(self):
        self.assertIn("Funds have NOT been disbursed", LOANS)

    def test_demo_password_not_advertised_on_member_page(self):
        self.assertNotRegex(MEMBER, re.compile(r"chama123", re.IGNORECASE))
        self.assertNotRegex(MEMBER, re.compile(r"demo\s*/\s*chama123", re.IGNORECASE))

    def test_unified_login_reuses_valid_session_and_routes_after_authentication(self):
        self.assertIn("supabaseClient.auth.getSession()", MEMBER)
        self.assertIn("if (data.session?.user) showApp(data.session.user.email)", MEMBER)
        self.assertIn("supabaseClient.auth.signInWithPassword({ email, password })", MEMBER)
        self.assertIn("smart_chama_live_dashboard.html", MEMBER)
        self.assertIn("catch (error)", MEMBER)

    def test_portal_keeps_existing_modules_and_routes_to_single_login(self):
        self.assertIn('href="smart_chama_supabase_ready-2.html"', PORTAL)
        self.assertIn("Savings & Transactions", PORTAL)
        self.assertIn("Loans & Repayments", PORTAL)
        self.assertIn("Officer Approvals", PORTAL)

    def test_dashboard_normalizes_role_names_and_keeps_server_authorization_authoritative(self):
        self.assertIn('replace(/[\s-]+/g', DASHBOARD)
        self.assertIn('if (isOwner || hasRole("treasurer", "secretary", "chairperson"', DASHBOARD)
        self.assertIn("each module and Supabase RLS/RPC must independently enforce access", DASHBOARD)

    def test_test_branch_is_not_mistaken_for_isolated_database(self):
        self.assertIn("A dedicated Supabase database branch", PLAN)
        self.assertIn("No browser-based end-to-end tests have been run", PLAN)
        self.assertIn("Do not run test signups", PLAN)


if __name__ == "__main__":
    unittest.main(verbosity=2)
