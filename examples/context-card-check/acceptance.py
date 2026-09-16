"""Same deterministic acceptance checks for both workflow variants."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from repo_context_card.cli import main


class CheckAcceptance(unittest.TestCase):
    def test_stable_missing_and_stale_outputs(self):
        for output_format in ("markdown", "json"):
            with (
                self.subTest(output_format=output_format),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                (root / "README.md").write_text("# Example\n", encoding="utf-8")
                card = root / ("CARD." + ("md" if output_format == "markdown" else "json"))
                args = [directory, "--format", output_format, "--output", str(card)]
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(args + ["--check"]), 1)
                    self.assertFalse(card.exists())
                    self.assertEqual(main(args), 0)
                    original = card.read_bytes()
                    self.assertEqual(main(args + ["--check"]), 0)
                    (root / "added.py").write_text("print(1)\n", encoding="utf-8")
                    self.assertEqual(main(args + ["--check"]), 1)
                    self.assertEqual(card.read_bytes(), original)

    def test_check_requires_output(self):
        with tempfile.TemporaryDirectory() as directory:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main([directory, "--check"])
            self.assertEqual(error.exception.code, 2)
