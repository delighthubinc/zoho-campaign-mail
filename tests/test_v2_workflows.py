"""Static safety contracts for the Ver.2 automation workflows."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class V2WorkflowSafetyTests(unittest.TestCase):
    def setUp(self):
        self.diagnostic = (ROOT / ".github/workflows/diagnostic-retry-zoho-draft.yml").read_text(encoding="utf-8")

    def test_auto_merge_uses_app_token_not_github_token(self):
        workflow = (ROOT / ".github/workflows/pr-campaign-validation.yml").read_text(encoding="utf-8")
        self.assertIn("actions/create-github-app-token@v2", workflow)
        self.assertIn("GH_TOKEN: ${{ steps.app-token.outputs.token }}", workflow)
        self.assertNotIn("GH_TOKEN: ${{ github.token }}", workflow)

    def test_recovery_is_admin_gated_and_draft_only(self):
        workflow = (ROOT / ".github/workflows/emergency-recover-zoho-draft.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("access.data.permission !== 'admin'", workflow)
        self.assertNotIn("access.data.user.permission", workflow)
        self.assertIn("CREATE_DRAFT_RECOVERY", workflow)
        self.assertIn("state:recovery-attempt", workflow)
        self.assertIn("failed_commit_sha:", workflow)
        self.assertIn("git merge-base --is-ancestor", workflow)
        self.assertIn("create_zoho_draft.py --campaign-file", workflow)
        lowered = workflow.lower()
        for forbidden in ("sendcampaign", "schedulecampaign", "test email"):
            self.assertNotIn(forbidden, lowered)

    def test_normal_pipeline_records_created_state(self):
        workflow = (ROOT / ".github/workflows/publish-and-create-draft.yml").read_text(encoding="utf-8")
        self.assertIn("state:reserved", workflow)
        self.assertIn("state:created", workflow)
        self.assertIn("reserved but not created", workflow)

    def test_diagnostic_retry_is_admin_gated_and_exactly_targeted(self):
        workflow = self.diagnostic
        self.assertIn("workflow_dispatch:", workflow)
        for required_input in ("campaign_slug:", "failed_commit_sha:", "confirmation:"):
            self.assertIn(required_input, workflow)
        self.assertIn("access.data.permission !== 'admin'", workflow)
        self.assertIn("DIAGNOSTIC_RETRY_ONCE_CONFIRMED", workflow)
        self.assertIn("process.env.CONFIRMATION !==", workflow)
        self.assertIn("context.ref !== 'refs/heads/main'", workflow)
        self.assertIn("process.env.SLUG !== 'forum-20260910'", workflow)
        self.assertIn("process.env.FAILED_SHA !== 'bfff863d28c97c1c24f78ee5e7802750e31985dc'", workflow)

    def test_diagnostic_retry_requires_prior_states_and_rejects_terminal_states(self):
        workflow = self.diagnostic
        self.assertIn("if (!hasState('reserved'))", workflow)
        self.assertIn("if (!hasState('recovery-attempt'))", workflow)
        for state in (
            "'created'", "'created-by-recovery'",
            "'created-by-recovery-reconciliation'", "'created-by-diagnostic-retry'",
        ):
            self.assertIn(state, workflow)
        self.assertIn("if (completedStates.some(hasState))", workflow)
        self.assertIn("if (hasState('diagnostic-retry-attempt'))", workflow)

    def test_diagnostic_attempt_is_recorded_before_the_only_api_step(self):
        workflow = self.diagnostic
        attempt = workflow.index("state:diagnostic-retry-attempt\\nactor:")
        api = workflow.index("run: python scripts/create_zoho_draft.py --campaign-file")
        created = workflow.index("state:created-by-diagnostic-retry\\nactor:")
        self.assertLess(attempt, api)
        self.assertLess(api, created)
        self.assertEqual(workflow.count("create_zoho_draft.py --campaign-file"), 1)

    def test_diagnostic_retry_uses_normal_sha256_marker_rule(self):
        workflow = self.diagnostic
        self.assertIn("crypto.createHash('sha256')", workflow)
        self.assertIn("`${process.env.FAILED_SHA}\\0${data.campaign_slug}\\0${data.zoho_campaign_name}`", workflow)
        self.assertIn("git merge-base --is-ancestor", workflow)

    def test_diagnostic_retry_remains_draft_only_and_preserves_safe_diagnostics(self):
        workflow = self.diagnostic
        lowered = workflow.lower()
        for forbidden in ("sendcampaign", "schedulecampaign", "test email"):
            self.assertNotIn(forbidden, lowered)
        script = (ROOT / "scripts/create_zoho_draft.py").read_text(encoding="utf-8")
        self.assertIn("transport_http_status=", script)
        self.assertIn("provider_code=", script)
        self.assertIn("provider_outcome=non_success", script)
        self.assertIn("Do not print the response body", script)


if __name__ == "__main__":
    unittest.main()
