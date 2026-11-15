"""Run paired claims through the normal, hash-verified importer CLI."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest

from test_matrix_receipts import Fixture, I, REPO


def label(record: dict, claim: dict) -> str:
    return (f"{record['operation']} [{claim['source_id']}, {record['boundary']}, {record['observer']}, "
            f"{claim['attempt']}, control {claim['control']}]: {claim['channel']}({claim['object']}) {claim['predicate']}.")


def bind(f: Fixture, example: dict, claims: list[dict], *, legacy: bool = False,
         observations: list[str] | None = None) -> str:
    record = example["observation"]
    f.write(f.source_name, {"observation": record})
    source = f.ref(f.source_name)
    card = f.read("work/fixture/card.json")
    card["contract"]["inputs"] = [source]
    for check in card["checks"]:
        check["evidence_refs"] = [source]
    f.write("work/fixture/card.json", card)
    projection = f.read(f.projection_name)
    case, receipt = projection["cases"][0], projection["receipts"][0]
    case["observations"] = observations if observations is not None else [label(record, c) for c in claims]
    receipt["sources"][0]["sha256"] = source["sha256"]
    receipt.update(excerpts=[], derived_checks=[])
    receipt.pop("claims", None)
    if not legacy:
        receipt["claims"] = claims
    f.write(f.projection_name, projection)
    work = f.read(f.receipt_name)
    work["contract_ref"] = f.ref("work/fixture/card.json")
    for artifact in work["artifacts"]:
        path = artifact["logical_path"]
        artifact.update(sha256=f.ref(path)["sha256"], size=(f.root / path).stat().st_size)
    f.write(f.receipt_name, work)
    f.index()
    return source["sha256"]


def check(f: Fixture) -> tuple[int, dict]:
    run = subprocess.run([sys.executable, "-B", str(f.root / "tools/receipt_import.py"),
                          "--root", str(f.root), "--receipt", f.receipt_name,
                          "--sha256", f.ref(f.receipt_name)["sha256"], "--case", f.case_id],
                         capture_output=True, text=True, timeout=60)
    return run.returncode, json.loads(run.stdout)


class ClaimTests(unittest.TestCase):
    def setUp(self) -> None:
        self.f = Fixture()
        self.addCleanup(self.f.cleanup)

    def example(self, name: str) -> dict:
        return json.loads((REPO / "examples/claims" / (name + ".json")).read_bytes())

    def test_paired_claims(self) -> None:
        for name, error in [("connection", "event not observed"), ("objects", "event not observed"),
                            ("window", "incomplete window")]:
            with self.subTest(name=name):
                ex = self.example(name)
                observed = bind(self.f, ex, ex["accepted"])
                self.assertEqual(check(self.f)[0], 0)
                self.assertEqual(bind(self.f, ex, ex["rejected"]), observed)
                code, result = check(self.f)
                self.assertEqual(code, 1)
                self.assertIn(error, result["reason"])

    def test_optional_claims_and_rendered_text(self) -> None:
        ex = self.example("connection")
        bind(self.f, ex, ex["accepted"], legacy=True, observations=["Editorial observation."])
        self.assertEqual(check(self.f)[0], 0)
        bind(self.f, ex, ex["accepted"], observations=["The handler executed."])
        self.assertIn("observation text", check(self.f)[1]["reason"])

    def test_retry_and_controls(self) -> None:
        ex = self.example("window")
        claim = dict(ex["rejected"][0], attempt="retry")
        bind(self.f, ex, [claim])
        self.assertEqual(check(self.f)[0], 0)
        bind(self.f, ex, [dict(claim, control="retry")])
        self.assertIn("control", check(self.f)[1]["reason"])
        bind(self.f, ex, [dict(claim, predicate="present")])
        self.assertIn("event not observed", check(self.f)[1]["reason"])

    def test_prior_receipt_source_cannot_be_relabelled(self) -> None:
        ex = self.example("objects")
        ex["observation"]["subject_id"] = "another-fixture"
        bind(self.f, ex, ex["accepted"])
        self.assertIn("subject", check(self.f)[1]["reason"])

    def test_two_sources_with_same_attempt_name_stay_distinguishable(self) -> None:
        ex = self.example("window")
        record = ex["observation"]
        other = self.example("window")["observation"]
        other["attempts"]["first"]["window"] = "complete"
        other["attempts"]["first"]["events"] = []
        claims = [ex["accepted"][0], dict(ex["accepted"][0], source_id="second", predicate="absent")]
        case = {"id": record["case_id"], "subject_id": record["subject_id"], "versions": record["versions"],
                "status": "measured", "observations": [label(record, claim) for claim in claims]}
        sources = {"fixture.source": {"observation": record}, "second": {"observation": other}}
        I.check_claims(case, {"claims": claims}, sources)
        case["observations"][1] = case["observations"][1].replace("[second,", "[fixture.source,")
        with self.assertRaisesRegex(ValueError, "observation text"):
            I.check_claims(case, {"claims": claims}, sources)
