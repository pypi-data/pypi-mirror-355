import unittest
from prpolish import git_utils

class TestGitUtils(unittest.TestCase):
    def test_get_commit_messages(self):
        self.assertIsInstance(git_utils.get_commit_messages(), list)

    def test_get_changed_files(self):
        self.assertIsInstance(git_utils.get_changed_files(), list)

    def test_get_branch_name(self):
        self.assertIsInstance(git_utils.get_branch_name(), str)

if __name__ == '__main__':
    unittest.main() 