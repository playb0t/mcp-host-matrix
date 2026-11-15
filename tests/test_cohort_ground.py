"""R01 grounds and negative controls derived from the published observation bytes."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
from cohort_ground import evaluate


class WindowCohortTests(unittest.TestCase):
    def setUp(self) -> None:
        ground = json.loads((REPO / "grounds/R01.json").read_bytes())
        self.spec = ground["parameters"]
        self.expected = ground["expected"]
        self.sources = {}
        for ref in ground["sources"]:
            raw = (REPO / ref["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), ref["sha256"])
            self.sources[ref["id"]] = json.loads(raw)

    def result(self) -> dict:
        return evaluate(self.spec, self.sources)

    def observation(self, index: int) -> tuple[dict, dict]:
        row = self.sources["bench"]["base_cells"][index]
        fields = next(e["fields"] for e in self.sources["receipt"]["excerpts"]
                      if e["source_pointer"] == row["source_pointer"])
        return row, fields

    def test_real_base_set_and_positive_control(self) -> None:
        result = self.result()
        self.assertEqual(result, self.expected)
        self.assertEqual((result["declared"], result["confirmed"], result["unknown"]), (12, 12, 0))
        self.assertEqual(len(result["profiles_by_route"]), 6)
        self.assertTrue(all(len(profiles) == 2 for profiles in result["profiles_by_route"].values()))
        self.assertEqual(result["control"]["revoke_responses"], [200, 200])
        self.assertEqual((result["control"]["prior_refresh_before"], result["control"]["prior_refresh_after"],
                          result["control"]["error"]), (200, 400, "invalid_grant"))
        forms = [type(self.observation(i)[1]["revocation_request"]) for i in range(12)]
        self.assertEqual((forms.count(str), forms.count(dict)), (6, 6))

    def test_incomplete_window_stays_in_denominator(self) -> None:
        for r in self.observation(0):
            r["observation_completed"] = False
        result = self.result()
        self.assertEqual((result["declared"], result["confirmed"], result["unknown"]), (12, 11, 1))

    def test_short_or_unstarted_windows_cannot_qualify(self) -> None:
        for r in self.observation(0):
            r["after_ack_seconds"] = 59.999
        for r in self.observation(1):
            r["native_tool_begin_observed"] = False
        result = self.result()
        self.assertEqual((result["declared"], result["confirmed"], result["unknown"]), (12, 10, 2))

    def test_duplicate_and_swapped_variant_rejected(self) -> None:
        ids = self.spec["selection"]["run_ids"]
        ids[0] = ids[1]
        with self.assertRaisesRegex(ValueError, "duplicate planned"):
            self.result()
        ids[0] = self.sources["bench"]["operation_variants"][0]["run_id"]
        with self.assertRaisesRegex(ValueError, "cohort differs"):
            self.result()

    def test_empty_status_with_request_or_response_rejected(self) -> None:
        _, fields = self.observation(2)
        record = fields["revocation_request"]
        for key, value in [("request_ids", ["retained"]), ("responses", [{"http_status": 200}])]:
            with self.subTest(key=key):
                record[key] = value
                with self.assertRaisesRegex(ValueError, "contradictory"):
                    self.result()
                record[key] = []

    def test_disagreement_between_projection_and_receipt_rejected(self) -> None:
        row, _ = self.observation(1)
        row["revocation_request"] = "sent"
        with self.assertRaisesRegex(ValueError, "observations differ"):
            self.result()

    def test_control_must_demonstrate_refusal(self) -> None:
        row = next(r for r in self.sources["bench"]["operation_variants"]
                   if r["run_id"] == self.spec["logout_control"])
        row["controller_refresh_after"]["http_status"] = 200
        with self.assertRaisesRegex(ValueError, "logout replay control"):
            self.result()

    def test_retroactive_relabel_rejected(self) -> None:
        self.spec["selection"]["timing"] = "before_measurement"
        with self.assertRaisesRegex(ValueError, "plan and capture journal"):
            self.result()

    def with_test_journal(self) -> list[dict]:
        """Construct a format control only; historical R01 has no before-run journal."""
        selection = self.spec["selection"]
        selection.update(timing="before_measurement", plan="test_plan", journal="test_journal")
        plan = {"schema": "window-plan/1", "run_ids": selection["run_ids"]}
        digest = hashlib.sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True,
                                           separators=(",", ":")).encode()).hexdigest()
        events = [{"kind": "plan_sealed", "plan_sha256": digest}]
        for row in self.sources["bench"]["base_cells"]:
            events.extend([{"kind": "started", "run_id": row["run_id"], "plan_sha256": digest},
                           {"kind": "finished", "run_id": row["run_id"],
                            "verdict_sha256": row["source_verdict_sha256"]}])
        self.sources["test_plan"] = plan
        self.sources["test_journal"] = {"schema": "window-plan-history/1", "events": events}
        return events

    def test_before_measurement_format_and_late_seal_control(self) -> None:
        events = self.with_test_journal()
        self.assertEqual(self.result()["selection"], "before_measurement")
        events[0], events[1] = events[1], events[0]
        with self.assertRaisesRegex(ValueError, "plan must precede run starts"):
            self.result()

    def test_matching_invalid_verdict_fingerprints_rejected(self) -> None:
        events = self.with_test_journal()
        for invalid in (None, "", "0" * 63, "G" * 64, "A" * 64):
            with self.subTest(invalid=invalid):
                for entry in self.observation(0):
                    entry["source_verdict_sha256"] = invalid
                events[2]["verdict_sha256"] = invalid
                with self.assertRaisesRegex(ValueError, "verdict fingerprint"):
                    self.result()

    def test_matching_invalid_projection_fingerprints_rejected(self) -> None:
        for invalid in (None, "", "A" * 64):
            with self.subTest(invalid=invalid):
                self.sources["bench"]["source"]["results_sha256"] = invalid
                self.sources["receipt"]["sources"][0]["sha256"] = invalid
                with self.assertRaisesRegex(ValueError, "source fingerprint"):
                    self.result()
