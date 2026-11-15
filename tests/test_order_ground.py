"""Order checks over the retained evidence for the real R04 bridge run."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from order_ground import evaluate


class RealLogOrderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ground = json.loads((ROOT / "grounds/R04.json").read_bytes())
        self.params = self.ground["parameters"]
        self.sources = {s["id"]: json.loads((ROOT / s["path"]).read_bytes())
                        for s in self.ground["sources"]}

    def test_exact_order_and_durations(self) -> None:
        result = evaluate(self.params, self.sources)
        self.assertEqual(result, self.ground["expected"])
        self.assertEqual(result["intervals_ms"], [1, 127])
        self.assertEqual(result["lines"], [120, 122, 138])

    def test_other_run_cannot_supply_event_even_with_same_timestamp_and_pid(self) -> None:
        # Reuse the unchanged event and reference the archived negative run at its locator.
        params = copy.deepcopy(self.params)
        params["events"][-1]["run_source"] = "r04.raw.negative-uri"
        with self.assertRaisesRegex(ValueError, "run or log"):
            evaluate(params, self.sources)

    def test_relabelling_entire_capture_to_negative_run_conflicts_with_receipt(self) -> None:
        params = copy.deepcopy(self.params)
        sources = copy.deepcopy(self.sources)
        capture = sources["bridge-log"]
        receipt = sources["r04-receipt"]
        other = next(item for item in receipt["sources"] if item["id"] == "r04.raw.negative-uri")
        capture.update(run_source=other["id"], run_sha256=other["sha256"])
        for event in params["events"]:
            event["run_source"] = other["id"]
        with self.assertRaisesRegex(ValueError, "receipt run selector"):
            evaluate(params, sources)

    def test_different_clock_or_log_fingerprint_is_rejected(self) -> None:
        for field, value in [("clock", "os-process-clock"), ("log_sha256", "f" * 64)]:
            with self.subTest(field=field):
                params = copy.deepcopy(self.params)
                params["events"][0][field] = value
                with self.assertRaisesRegex(ValueError, "run or log"):
                    evaluate(params, self.sources)

    def test_inverted_order_and_false_message_are_rejected(self) -> None:
        params = copy.deepcopy(self.params)
        params["events"][0], params["events"][1] = params["events"][1], params["events"][0]
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            evaluate(params, self.sources)
        params = copy.deepcopy(self.params)
        params["events"][1]["message"] = "The browser process opened."
        with self.assertRaisesRegex(ValueError, "message"):
            evaluate(params, self.sources)

    def test_changed_extract_with_rebound_outer_source_is_rejected(self) -> None:
        stream = self.sources["bridge-log"]
        stream["extract_text"] = stream["extract_text"].replace("28.884Z", "28.885Z")
        with self.assertRaisesRegex(ValueError, "extract digest"):
            evaluate(self.params, self.sources)
