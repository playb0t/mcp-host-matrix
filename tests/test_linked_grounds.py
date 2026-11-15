"""Exercise optional grounds through the ordinary projection and historical CLI."""
from __future__ import annotations
import json
import subprocess
import sys
import unittest

from test_matrix_receipts import Fixture, I, REPO


class LinkedGroundTests(unittest.TestCase):
    def test_real_replays(self) -> None:
        for row in ("R01", "R04"):
            with self.subTest(row=row):
                proc = subprocess.run([sys.executable, "-B", str(REPO/"tools/receipt_import.py"),
                                       "--ground", row], capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
                result = json.loads(proc.stdout)
                self.assertEqual(result["case_id"], row)
                self.assertTrue(result["computed"])
                self.assertTrue(result["statement"])

    def test_readable_prose_survives_optional_atomic_evidence(self) -> None:
        f = Fixture()
        self.addCleanup(f.cleanup)
        pr = f.read(f.projection_name)
        case, receipt = pr["cases"][0], pr["receipts"][0]
        prose = "The connection was established for the selected object."
        original = case["observations"]
        case["observations"] = [prose]
        ground = {"schema":"matrix-ground/1", "case_id":f.case_id, "kind":"atomic_events",
                  "statement":prose, "parameters":{"claims":receipt.pop("claims")},
                  "expected":{"events":original},
                  "sources":[{"id":"fixture.source","path":f.source_name,"sha256":f.ref(f.source_name)["sha256"]}]}
        path = "work/fixture/ground.json"
        f.write(path, ground)
        receipt["grounds"] = [{"observation_index":0, **f.ref(path)}]
        f.write(f.projection_name, pr)
        work = f.read(f.receipt_name)
        work["artifacts"].append({"logical_path":path, "visibility":"public"})
        def rebind() -> dict:
            for a in work["artifacts"]:
                name = a["logical_path"]
                a.update(f.ref(name), size=(f.root/name).stat().st_size)
            f.write(f.receipt_name,work)
            f.index()
            return I.material(I.P.Snapshot(f.root), f.ref(f.receipt_name), f.case_id)
        self.assertEqual(rebind()["case"]["observations"], [prose])
        case["observations"] = ["Different editorial conclusion."]
        f.write(f.projection_name, pr)
        with self.assertRaisesRegex(ValueError, "statement"):
            rebind()
        case["observations"] = [prose]
        ground["expected"]["events"] = []
        f.write(path, ground)
        receipt["grounds"][0].update(f.ref(path))
        f.write(f.projection_name, pr)
        with self.assertRaisesRegex(ValueError, "computed"):
            rebind()

    def test_unregistered_cells_reject_free_text_for_both_computed_kinds(self) -> None:
        f = Fixture()
        self.addCleanup(f.cleanup)
        case = {"id": f.case_id, "subject_id": "fixture-service", "versions": {"fixture": "1"}}
        for row, text in (("R01", "Confirmed in 13 of 13 windows."),
                          ("R04", "The helper exited 128 ms after success.")):
            with self.subTest(row=row):
                ground = f.read(f"grounds/{row}.json")
                ground.pop("statement_form")
                ground.update(case_id=case["id"], statement=text)
                allowed = {}
                for ref in ground["sources"]:
                    path = ref["path"]
                    source = f.read(path)
                    if ref["id"] == ground["parameters"]["receipt"]:
                        source.update(case_id=case["id"], subject_id=case["subject_id"], versions=case["versions"])
                    elif source.get("case_id") == row:
                        source["case_id"] = case["id"]
                    f.write(path, source)
                    ref["sha256"] = allowed[path] = f.ref(path)["sha256"]
                f.index()
                with self.assertRaisesRegex(ValueError, "no registered statement form"):
                    I.evaluate_ground(I.P.Snapshot(f.root), ground, case, allowed)
