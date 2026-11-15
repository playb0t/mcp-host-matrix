"""Check the rendered statements against the two retained historical sources."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from test_matrix_receipts import Fixture, REPO, V
from cohort_ground import evaluate as evaluate_windows


class ReaderStatementTests(unittest.TestCase):
    def test_visible_changes_rejected_after_rehash(self) -> None:
        f = Fixture()
        self.addCleanup(f.cleanup)
        path = f.root / "grounds/README.md"
        original = path.read_text(encoding="utf8")
        for case, change, wrong in [("R01", "12 of 12", "13 of 13"),
                                    ("R04", "127 ms", "128 ms"),
                                    ("R04", "after success.", "before success.")]:
            with self.subTest(case=case):
                self.assertEqual(original.count(change), 1)
                path.write_text(original.replace(change, wrong), encoding="utf8", newline="\n")
                V.write_manifest(f.root)
                with self.assertRaisesRegex(V.ValidationError, "reader page"):
                    V.validate(f.root)
        path.write_text(original, encoding="utf8", newline="\n")
        V.write_manifest(f.root)
        self.assertEqual(V.validate(f.root)["historical_grounds"], 2)

    def test_ground_cannot_inject_literal_claim(self) -> None:
        f = Fixture()
        self.addCleanup(f.cleanup)
        for row, bogus in [("R01", "13 of 13 windows"), ("R04", "128 ms before exit")]:
            with self.subTest(row=row):
                path = f"grounds/{row}.json"
                ground = f.read(path)
                ground["statement"] = bogus
                f.write(path, ground)
                f.index()
                command = [sys.executable, "-B", str(f.root/"tools/receipt_import.py"),
                           "--root", str(f.root), "--ground", row]
                run = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(run.returncode, 1, run.stdout)
                self.assertIn("statement", json.loads(run.stdout)["reason"])

    def test_reader_marks_one_unknown_from_real_windows(self) -> None:
        from reader_statements import render_statement
        ground = json.loads((REPO/"grounds/R01.json").read_bytes())
        sources = {ref["id"]: json.loads((REPO/ref["path"]).read_bytes()) for ref in ground["sources"]}
        row = sources["bench"]["base_cells"][0]
        entry = next(e["fields"] for e in sources["receipt"]["excerpts"]
                     if e["source_pointer"] == row["source_pointer"])
        row["observation_completed"] = entry["observation_completed"] = False
        computed = evaluate_windows(ground["parameters"], sources)
        sentence = render_statement("R01", computed)
        self.assertIn("11 of 12", sentence)
        self.assertIn("1 window remains unknown", sentence)
        self.assertNotIn("12 of 12", sentence)
        self.assertNotIn("Each of the 12", sentence)
