import unittest
from unittest.mock import patch

from scripts.check import CHECKS, main


class IntegrationPrerequisiteTests(unittest.TestCase):
    @patch("builtins.print")
    def test_failed_build_prevents_tests_using_stale_assets(self, _print) -> None:
        with patch("sys.argv", ["check.py", "--only", "python-tests"]):
            with patch("scripts.check.subprocess.run") as run:
                run.return_value.returncode = 1
                self.assertEqual(main(), 1)
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.args[0][1:], CHECKS["frontend-build"])

    @patch("builtins.print")
    def test_python_group_builds_before_tests_and_full_run_builds_once(self, _print) -> None:
        for selection in [[], ["--only", "python"]]:
            with self.subTest(selection=selection), patch("sys.argv", ["check.py", *selection]):
                with patch("scripts.check.subprocess.run") as run:
                    run.return_value.returncode = 0
                    self.assertEqual(main(), 0)
                    commands = [call.args[0][1:] for call in run.call_args_list]
                    self.assertEqual(commands.count(CHECKS["frontend-build"]), 1)
                    self.assertLess(commands.index(CHECKS["frontend-build"]), commands.index(CHECKS["python-tests"]))
