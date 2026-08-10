"""Tests for fail-closed campaign auto-merge scope classification."""
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_pr_scope.py"


class CheckPrScopeTests(unittest.TestCase):
    def _commit(self, repo: Path, message: str) -> str:
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", message],
            cwd=repo,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    def _classify(self, repo: Path, base: str, head: str) -> str:
        return subprocess.check_output(
            ["python3", str(SCRIPT), "--base", base, "--head", head], cwd=repo, text=True
        )

    def test_added_image_is_not_auto_merge_eligible(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            (repo / "README").write_text("initial\n", encoding="utf-8")
            base = self._commit(repo, "initial")
            campaign = repo / "campaigns/example"
            (campaign / "images").mkdir(parents=True)
            (campaign / "campaign.json").write_text("{}\n", encoding="utf-8")
            (campaign / "mail.html").write_text("<html></html>\n", encoding="utf-8")
            (campaign / "images/banner.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            head = self._commit(repo, "campaign with image")

            self.assertIn("eligible=false", self._classify(repo, base, head))

    def test_modified_image_is_not_auto_merge_eligible(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            campaign = repo / "campaigns/example"
            (campaign / "images").mkdir(parents=True)
            (campaign / "campaign.json").write_text("{}\n", encoding="utf-8")
            (campaign / "mail.html").write_text("<html></html>\n", encoding="utf-8")
            image = campaign / "images/banner.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            base = self._commit(repo, "initial campaign")
            image.write_bytes(b"\x89PNG\r\n\x1a\nupdated")
            (campaign / "campaign.json").write_text('{"subject":"updated"}\n', encoding="utf-8")
            (campaign / "mail.html").write_text("<html>updated</html>\n", encoding="utf-8")
            head = self._commit(repo, "modify image")

            self.assertIn("eligible=false", self._classify(repo, base, head))

    def test_image_deletion_keeps_existing_scope_behavior(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            campaign = repo / "campaigns/example"
            (campaign / "images").mkdir(parents=True)
            (campaign / "campaign.json").write_text("{}\n", encoding="utf-8")
            (campaign / "mail.html").write_text("<html></html>\n", encoding="utf-8")
            image = campaign / "images/banner.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            base = self._commit(repo, "initial campaign")
            image.unlink()
            (campaign / "campaign.json").write_text('{"subject":"updated"}\n', encoding="utf-8")
            (campaign / "mail.html").write_text("<html>updated</html>\n", encoding="utf-8")
            head = self._commit(repo, "remove image")

            self.assertIn("eligible=true", self._classify(repo, base, head))


if __name__ == "__main__":
    unittest.main()
