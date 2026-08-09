"""Static safety contracts for the Ver.2 automation workflows."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class V2WorkflowSafetyTests(unittest.TestCase):
    def test_auto_merge_uses_app_token_not_github_token(self):
        workflow = (ROOT / ".github/workflows/pr-campaign-validation.yml").read_text(encoding="utf-8")
        self.assertIn("actions/create-github-app-token@v2", workflow)
        self.assertIn("GH_TOKEN: ${{ steps.app-token.outputs.token }}", workflow)
        self.assertNotIn("GH_TOKEN: ${{ github.token }}", workflow)

    def test_recovery_is_admin_gated_and_draft_only(self):
        workflow = (ROOT / ".github/workflows/emergency-recover-zoho-draft.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("permission !== 'admin'", workflow)
        self.assertIn("CREATE_DRAFT_RECOVERY", workflow)
        self.assertIn("state:recovery-attempt", workflow)
        self.assertIn("create_zoho_draft.py --campaign-file", workflow)
        lowered = workflow.lower()
        for forbidden in ("sendcampaign", "schedulecampaign", "test email"):
            self.assertNotIn(forbidden, lowered)

    def test_normal_pipeline_records_created_state(self):
        workflow = (ROOT / ".github/workflows/publish-and-create-draft.yml").read_text(encoding="utf-8")
        self.assertIn("state:reserved", workflow)
        self.assertIn("state:created", workflow)


if __name__ == "__main__":
    unittest.main()
