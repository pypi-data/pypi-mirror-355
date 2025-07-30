import unittest
from prpolish import vibe_check

class TestVibeCheck(unittest.TestCase):
    def test_run_vibe_checks(self):
        warnings = vibe_check.run_vibe_checks([
            "wip: trying something",
            "Add tests"
        ], ["main.py", "test_main.py"])
        self.assertIsInstance(warnings, list)
        self.assertTrue(all(isinstance(w, str) for w in warnings))

if __name__ == '__main__':
    unittest.main() 