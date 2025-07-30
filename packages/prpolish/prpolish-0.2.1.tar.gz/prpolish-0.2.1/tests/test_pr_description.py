import unittest
from prpolish import pr_description
import os

class TestPRDescription(unittest.TestCase):
    def test_generate_pr_description(self):
        desc = pr_description.generate_pr_description([
            "Add login endpoint",
            "Refactor user model"
        ], ["app/auth.py", "app/models/user.py"], "feature/auth-refactor")
        self.assertIsInstance(desc, str)

    def test_generate_pr_description_with_template(self):
        template = "Branch: {branch_name}\nCommits:\n{commit_messages}\nFiles:\n{changed_files}"
        desc = pr_description.generate_pr_description([
            "Add login endpoint",
            "Refactor user model"
        ], ["app/auth.py", "app/models/user.py"], "feature/auth-refactor", template=template)
        self.assertIn("Branch: feature/auth-refactor", desc)
        self.assertIn("Add login endpoint", desc)
        self.assertIn("app/auth.py", desc)

    def test_generate_pr_title(self):
        # Good commit message (conventional)
        title = pr_description.generate_pr_title([
            "feat: add search functionality to dashboard (closes #456)",
            "fix: correct typo"
        ], ["dashboard.py"], "feature/search")
        self.assertTrue(title.startswith("feat:"))
        # Good commit message (non-conventional)
        title2 = pr_description.generate_pr_title([
            "Add login endpoint for users"], ["auth.py"], "feature/login")
        self.assertIn("feat", title2)
        # Fallback to branch name
        title3 = pr_description.generate_pr_title([], ["file.py"], "fix/bug-123")
        self.assertTrue(title3.startswith("fix:"))
        # Bad commit messages, fallback
        title4 = pr_description.generate_pr_title(["wip", "fix bug"], [], "chore/update")
        self.assertTrue(title4.startswith("chore:"))

    def test_generate_pr_title_llm_fallback(self):
        # Simulate no API key (should fallback to heuristic)
        old_key = os.environ.get("OPENAI_API_KEY")
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        title = pr_description.generate_pr_title_llm([
            "feat: add search functionality to dashboard (closes #456)"
        ], ["dashboard.py"], "feature/search")
        self.assertTrue(isinstance(title, str) and len(title) > 0)
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key

if __name__ == '__main__':
    unittest.main() 