"""Static safety contracts for the Ver.2 automation workflows."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class V2WorkflowSafetyTests(unittest.TestCase):
    def _discover_script(self, before, after, include_deleted=False):
        workflow = (ROOT / ".github/workflows/publish-and-create-draft.yml").read_text(encoding="utf-8")
        step = workflow.split("      - id: changed\n", 1)[1].split("\n\n  publish-and-draft:", 1)[0]
        script = step.split("        run: |\n", 1)[1]
        script = "\n".join(line[10:] for line in script.splitlines())
        script = script.replace("${{ github.event.before }}", before).replace("${{ github.sha }}", after)
        if include_deleted:
            script = script.replace("--diff-filter=ACMR", "--diff-filter=ACMRD")
        return script

    def _commit(self, repo, message):
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", message],
            cwd=repo,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    def _run_discover(self, repo, before, after, include_deleted=False):
        output = repo / "github-output"
        output.unlink(missing_ok=True)
        env = {**os.environ, "GITHUB_OUTPUT": str(output)}
        subprocess.run(
            ["bash", "-eu", "-o", "pipefail", "-c", self._discover_script(before, after, include_deleted)],
            cwd=repo,
            env=env,
            check=True,
        )
        return json.loads(output.read_text(encoding="utf-8").removeprefix("campaigns=").strip())

    def test_discover_selects_additions_and_updates_but_not_deletions(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            (repo / "README").write_text("initial\n", encoding="utf-8")
            initial = self._commit(repo, "initial")

            added_file = repo / "campaigns/new-campaign/campaign.json"
            added_file.parent.mkdir(parents=True)
            added_file.write_text('{}\n', encoding="utf-8")
            added = self._commit(repo, "add campaign")
            self.assertEqual(["new-campaign"], self._run_discover(repo, initial, added))

            added_file.write_text('{"subject":"updated"}\n', encoding="utf-8")
            updated = self._commit(repo, "update campaign")
            self.assertEqual(["new-campaign"], self._run_discover(repo, added, updated))

            added_file.unlink()
            deleted = self._commit(repo, "delete campaign")
            self.assertEqual([], self._run_discover(repo, updated, deleted))

    def test_discover_fail_safe_excludes_campaign_missing_from_current_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            campaign_file = repo / "campaigns/removed/campaign.json"
            campaign_file.parent.mkdir(parents=True)
            campaign_file.write_text('{}\n', encoding="utf-8")
            present = self._commit(repo, "add campaign")
            campaign_file.unlink()
            deleted = self._commit(repo, "delete campaign")

            # Include D in the test-only diff to prove the existence guard is independent.
            self.assertEqual([], self._run_discover(repo, present, deleted, include_deleted=True))

    def test_auto_merge_uses_app_token_not_github_token(self):
        workflow = (ROOT / ".github/workflows/pr-campaign-validation.yml").read_text(encoding="utf-8")
        self.assertIn("actions/create-github-app-token@v2", workflow)
        self.assertIn("GH_TOKEN: ${{ steps.app-token.outputs.token }}", workflow)
        self.assertNotIn("GH_TOKEN: ${{ github.token }}", workflow)
        self.assertNotIn("Regenerate checked-in HTML", workflow)
        self.assertNotIn("build_email.py --campaign-slug", workflow)
        self.assertIn("Validate fixed campaign HTML", workflow)

    def test_auto_merge_targets_repository_without_checkout_dependency(self):
        workflow = (ROOT / ".github/workflows/pr-campaign-validation.yml").read_text(encoding="utf-8")
        auto_merge_job = workflow.split("  enable-auto-merge:\n", 1)[1]
        self.assertIn('gh pr merge "${{ github.event.pull_request.number }}" --auto --squash --repo "${{ github.repository }}"', auto_merge_job)
        self.assertIn("needs: validate-campaign", auto_merge_job)
        self.assertIn("github.event.pull_request.base.ref == 'main'", auto_merge_job)

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
        self.assertIn("if: needs.discover.outputs.campaigns != '[]'", workflow)
        self.assertIn("state:reserved", workflow)
        self.assertIn("state:created", workflow)
        self.assertIn("reserved but not created", workflow)

    def test_chat_image_import_is_admin_gated_and_reuses_batch_importer(self):
        workflow = (ROOT / ".github/workflows/chat-image-import.yml").read_text(encoding="utf-8")
        self.assertIn("issues:", workflow)
        self.assertIn("types: [opened]", workflow)
        self.assertIn("github.event.issue.title == '[automation:image-import]'", workflow)
        escaped_title = "[automation" + chr(92) + ":image-import]"
        self.assertNotIn(escaped_title, workflow)
        self.assertIn("access.data.permission !== 'admin'", workflow)
        self.assertIn("scripts/import_drive_images.py", workflow)
        self.assertIn("destination already exists", (ROOT / "scripts/import_drive_images.py").read_text())
        self.assertIn("github_pages_url", workflow)
        self.assertIn("if: failure()", workflow)

    def test_image_only_push_cannot_select_a_zoho_draft_campaign(self):
        workflow = (ROOT / ".github/workflows/publish-and-create-draft.yml").read_text(encoding="utf-8")
        self.assertIn("-- 'campaigns/*/campaign.json'", workflow)

if __name__ == "__main__":
    unittest.main()
