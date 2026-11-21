from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import render_matrix as R


class CoverageTitleTests(unittest.TestCase):
    def row(self, title: str, case_id: str = "SYN-TITLE") -> str:
        data = {"subjects": [{"id": "vscode", "name": "VS Code"}], "cases": [{
            "id": case_id, "topic": "R03", "title": title, "status": "measured_with_limits",
            "subject_id": "vscode", "native_hosts": ["VS Code"], "components": []}]}
        return R.section(data).splitlines()[3]

    def test_new_case_omits_its_subject_prefix(self) -> None:
        for title in ["VS Code Live tool-set picker refresh", "VS Code live tool-set picker refresh"]:
            with self.subTest(title=title):
                self.assertEqual(self.row(title), "| SYN-TITLE Live tool-set picker refresh | M |")

    def test_unprefixed_and_other_subject_titles_are_preserved(self) -> None:
        for title in ["Live tool-set picker refresh", "Cursor tool-set picker refresh"]:
            with self.subTest(title=title):
                self.assertEqual(self.row(title), "| SYN-TITLE " + title + " | M |")

    def test_legacy_title_is_unchanged(self) -> None:
        self.assertEqual(self.row("VS Code historical title", "R03"),
                         "| R03 VS Code historical title | M |")
