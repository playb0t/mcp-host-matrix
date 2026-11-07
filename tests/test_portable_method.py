from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import unittest
from uuid import uuid4

REPO = Path(__file__).resolve().parents[1]
LAB = REPO.parent
STATE = LAB / ".portable-tests"
spec = importlib.util.spec_from_file_location("portable_test_module", REPO / "method/v1/portable.py")
assert spec and spec.loader
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)


class PortableMethodTests(unittest.TestCase):
    def setUp(self) -> None:
        STATE.mkdir(exist_ok=True)
        self.root = STATE / uuid4().hex
        self.root.mkdir()
        assert self.root.resolve().is_relative_to(STATE.resolve())
        self.addCleanup(self.cleanup)
        for folder in ("method/v1", "method/examples"):
            shutil.copytree(REPO / folder, self.root / folder)
        self.manifest()

    def cleanup(self) -> None:
        assert self.root.resolve().is_relative_to(STATE.resolve()) and self.root != STATE
        def retry(function, name, info):
            path = Path(name)
            assert path.resolve().is_relative_to(self.root.resolve())
            if not isinstance(info[1], PermissionError):raise info[1]
            path.chmod(stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
            function(name)
        shutil.rmtree(self.root, onerror=retry)

    def write(self, name: str, value: object) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, bytes):path.write_bytes(value)
        else:path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf8", newline="\n")

    def read(self, name: str) -> dict:
        return json.loads((self.root / name).read_text(encoding="utf8"))

    def ref(self, name: str) -> dict:
        return {"logical_path": name, "sha256": hashlib.sha256((self.root / name).read_bytes()).hexdigest()}

    def manifest(self) -> None:
        entries = []
        for path in sorted(self.root.rglob("*")):
            if path.is_file() and ".git" not in path.relative_to(self.root).parts and path.name != "MANIFEST.sha256":
                entries.append(hashlib.sha256(path.read_bytes()).hexdigest() + "  " + path.relative_to(self.root).as_posix())
        (self.root / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf8", newline="\n")

    def verify(self, profile: str = "publication") -> dict:
        return P.verify_receipt(P.Snapshot(self.root), self.ref("method/examples/receipts/" + profile + ".json"))

    def mutate_receipt(self, profile: str, mutation) -> None:
        name = "method/examples/receipts/" + profile + ".json"
        value = self.read(name);mutation(value);self.write(name, value);self.manifest()

    def card(self, profile: str = "research") -> dict:
        return self.read("method/examples/cards/" + profile + ".json")

    def git(self, *args: str) -> bytes:
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        result = subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false",
            "-c", "core.hooksPath=" + str(self.root / ".empty-hooks"), "-c", "user.name=Fixture",
            "-c", "user.email=fixture@example.invalid", "-C", str(self.root), *args],
            capture_output=True, timeout=30, env=env)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        return result.stdout

    def commit(self) -> str:
        self.git("add", ".");self.git("commit", "-m", "Synthetic integrity fixture")
        return self.git("rev-parse", "HEAD").decode().strip()

    def test_four_profiles_form_a_verified_public_chain(self) -> None:
        result = self.verify()
        self.assertEqual(len(result["nodes"]), 4)
        self.assertEqual({node["profile"] for node in result["nodes"]}, set(P.PROFILES))
        self.assertEqual(result["receipt"]["outcome"], "prepared")
        self.assertEqual(result["card"]["profile"], "publication")
        self.assertTrue(all(item["visibility"] == "public" for item in result["artifacts"]))

    def test_examples_declare_observed_expected_verdicts(self) -> None:
        for case in self.read("method/examples/INDEX.json")["cases"]:
            if case["expected"] == "PASS":P.verify_receipt(P.Snapshot(self.root), case["ref"])
            else:
                with self.assertRaises(P.ValidationError):P.verify_receipt(P.Snapshot(self.root), case["ref"])

    def test_source_mutation_fails_after_rebuilding_repository_manifest(self) -> None:
        self.write("method/examples/data/measurement.json", b'{"synthetic":false}\n');self.manifest()
        with self.assertRaises(P.ValidationError):self.verify("research")

    def test_source_fingerprint_substitution_is_not_a_public_source_proof(self) -> None:
        self.mutate_receipt("research", lambda value: value["artifacts"][0].update(sha256="0" * 64))
        with self.assertRaises(P.ValidationError):self.verify("research")

    def test_receipt_fingerprint_mutation_fails(self) -> None:
        name = "method/examples/receipts/research.json";old = self.ref(name)
        value = self.read(name);value["withheld"]["internal_artifacts"] += 1
        self.write(name, value);self.manifest()
        with self.assertRaises(P.ValidationError):P.verify_receipt(P.Snapshot(self.root), old)

    def test_card_mutation_is_bound_by_its_receipt(self) -> None:
        name = "method/examples/cards/research.json";value = self.read(name)
        value["contract"]["scope"] = "Changed after review";self.write(name, value);self.manifest()
        with self.assertRaises(P.ValidationError):self.verify("research")

    def test_unmanifested_receipt_is_not_accepted(self) -> None:
        path = self.root / "MANIFEST.sha256"
        path.write_text("\n".join(line for line in path.read_text().splitlines() if not line.endswith("method/examples/receipts/research.json")) + "\n", encoding="utf8")
        with self.assertRaises(P.ValidationError):self.verify("research")

    def test_unmanifested_public_source_is_not_accepted(self) -> None:
        path = self.root / "MANIFEST.sha256"
        path.write_text("\n".join(line for line in path.read_text().splitlines() if not line.endswith("method/examples/data/measurement.json")) + "\n", encoding="utf8")
        with self.assertRaises(P.ValidationError):self.verify("research")

    def test_method_file_mutation_fails(self) -> None:
        name = "method/v1/portable.py";self.write(name, (self.root / name).read_bytes() + b"\n# changed\n");self.manifest()
        with self.assertRaises(P.ValidationError):self.verify("research")

    def test_method_manifest_changed_under_its_reference_fails(self) -> None:
        name = "method/v1/MANIFEST.json";value = self.read(name);value["version"] = "1.0.1"
        self.write(name, value);self.manifest()
        with self.assertRaises(P.ValidationError):self.verify("research")

    def test_artifact_size_must_match_public_bytes(self) -> None:
        self.mutate_receipt("research", lambda value: value["artifacts"][0].update(size=999))
        with self.assertRaises(P.ValidationError):self.verify("research")

    def test_nonpublic_visibility_and_additional_metadata_are_rejected(self) -> None:
        for change in [lambda v: v["artifacts"][0].update(visibility="private"),
                       lambda v: v["artifacts"][0].update(source="hidden-name"),
                       lambda v: v.update(local_report_sha256="0" * 64)]:
            original = (REPO / "method/examples/receipts/research.json").read_bytes()
            self.write("method/examples/receipts/research.json", original)
            self.mutate_receipt("research", change)
            with self.assertRaises(P.ValidationError):self.verify("research")

    def test_withheld_accepts_counts_only(self) -> None:
        for change in [lambda v: v["withheld"].update(private_hashes=["0" * 64]),
                       lambda v: v["withheld"].update(private_artifacts=True),
                       lambda v: v["withheld"].update(internal_artifacts=-1)]:
            self.write("method/examples/receipts/research.json", (REPO / "method/examples/receipts/research.json").read_bytes())
            self.mutate_receipt("research", change)
            with self.assertRaises(P.ValidationError):self.verify("research")

    def test_research_basis_cannot_point_to_engineering(self) -> None:
        self.mutate_receipt("document", lambda value: value["parents"][0].update(relation="research_basis"))
        with self.assertRaises(P.ValidationError):self.verify("document")

    def test_research_derived_patch_requires_the_correct_relation(self) -> None:
        self.mutate_receipt("engineering", lambda value: value["parents"][0].update(relation="input"))
        with self.assertRaises(P.ValidationError):self.verify("engineering")

    def test_publication_requires_a_receipt_input(self) -> None:
        self.mutate_receipt("publication", lambda value: value.update(parents=[]))
        with self.assertRaises(P.ValidationError):self.verify()

    def test_publication_payload_cannot_come_from_input_only_parent(self) -> None:
        self.mutate_receipt("publication", lambda value: value.update(parents=[
            {"ref": self.ref("method/examples/receipts/research.json"), "relation": "publication_input"},
            {"ref": self.ref("method/examples/receipts/document.json"), "relation": "input"}]))
        with self.assertRaises(P.ValidationError):self.verify()

    def test_publication_cannot_introduce_new_output_bytes(self) -> None:
        art = self.read("method/examples/receipts/research.json")["artifacts"][0]
        self.mutate_receipt("publication", lambda value: value.update(artifacts=[art]))
        with self.assertRaises(P.ValidationError):self.verify()

    def test_shared_parent_is_deduplicated_and_duplicate_edge_rejected(self) -> None:
        self.mutate_receipt("document", lambda value: value["parents"].append({"ref": self.ref("method/examples/receipts/engineering.json"), "relation": "publication_input"}))
        self.assertEqual(len(self.verify("document")["nodes"]), 3)
        self.mutate_receipt("document", lambda value: value["parents"].append(copy.deepcopy(value["parents"][0])))
        with self.assertRaises(P.ValidationError):self.verify("document")

    def test_only_four_profiles_and_research_mcp_variant(self) -> None:
        card = self.card();card["variant"] = "mcp";P.validate_card(card)
        for profile in ["general", "mcp-research", "vendor-specific", None]:
            bad = self.card();bad["profile"] = profile
            with self.assertRaises(P.ValidationError):P.validate_card(bad)
        bad = self.card("engineering");bad["variant"] = "mcp"
        with self.assertRaises(P.ValidationError):P.validate_card(bad)

    def test_experimental_research_cannot_skip_controls(self) -> None:
        card = self.card();card["contract"]["options"]["mode"] = "experimental"
        with self.assertRaises(P.ValidationError):P.validate_card(card)

    def test_required_kind_and_purpose_cannot_be_substituted(self) -> None:
        card = self.card();card["contract"]["plans"][0]["kind"] = "artifact"
        with self.assertRaises(P.ValidationError):P.validate_card(card)
        card = self.card();card["contract"]["plans"].pop();card["checks"].pop()
        with self.assertRaises(P.ValidationError):P.validate_card(card)

    def test_red_checks_cannot_be_reported_verified(self) -> None:
        card = self.card("engineering");card["checks"][0]["state"] = "failed"
        with self.assertRaises(P.ValidationError):P.validate_card(card)
        card["contract"]["completion"] = "bounded";card["outcome"] = "bounded"
        P.validate_card(card)
        card["limits"] = []
        with self.assertRaises(P.ValidationError):P.validate_card(card)

    def test_refuted_research_is_a_completed_assessment(self) -> None:
        card = self.card()
        self.assertEqual(card["checks"][-1]["verdict"], "refuted")
        P.validate_card(card)
        card["checks"][-1]["verdict"] = "inconclusive";P.validate_card(card)
        card["checks"][-1]["verdict"] = "positive"
        with self.assertRaises(P.ValidationError):P.validate_card(card)

    def test_prepared_publication_cannot_be_relabelled_published(self) -> None:
        card = self.card("publication");card["outcome"] = "published"
        with self.assertRaises(P.ValidationError):P.validate_card(card)
        card["contract"]["options"]["stage"] = "published"
        with self.assertRaises(P.ValidationError):P.validate_card(card)

    def test_bad_paths_are_rejected_without_resolution(self) -> None:
        bad = ["/absolute", "../traversal", "a/../b", "a//b", "a/./b", "a\\b", "nul.txt", "a. ", "a:stream", "con/receipt.json", ".git/config", "nested/.GIT/config", chr(68) + ":" + "/private"]
        for name in bad:
            with self.subTest(name=name):
                with self.assertRaises(P.ValidationError):P.logical_path(name)

    def test_duplicate_manifest_alias_and_json_keys_are_rejected(self) -> None:
        path = self.root / "MANIFEST.sha256";raw = path.read_text()
        line = raw.splitlines()[0];path.write_text(raw + line[:66] + line[66:].upper() + "\n", encoding="utf8")
        with self.assertRaises(P.ValidationError):P.Snapshot(self.root)
        for raw in [b'{"a":1,"a":2}', b'{"a":NaN}', b'[]', b'\xff']:
            with self.assertRaises(P.ValidationError):P.load_json(raw)

    def test_snapshot_does_not_mix_a_later_manifest(self) -> None:
        snapshot = P.Snapshot(self.root)
        self.write("later.txt", b"later");self.manifest()
        with self.assertRaises(P.ValidationError):snapshot.read("method/examples/data/measurement.json")

    def test_hardlinked_artifact_is_rejected(self) -> None:
        path = self.root / "method/examples/data/measurement.json"
        alias = self.root / "alias.json"
        try:os.link(path, alias)
        except OSError as exc:self.skipTest("Host could not create fixture hardlink: " + str(exc))
        with self.assertRaises(P.ValidationError):self.verify("research")

    def test_symlinked_artifact_is_rejected(self) -> None:
        path = self.root / "method/examples/data/measurement.json"
        backup = self.root / "measurement-original.json";path.rename(backup)
        try:path.symlink_to(backup)
        except OSError as exc:
            backup.rename(path);self.skipTest("Host could not create fixture symlink: " + str(exc))
        with self.assertRaises(P.ValidationError):self.verify("research")

    def test_canonical_candidate_spelling_rejects_windows_case_alias(self) -> None:
        if os.name != "nt":self.skipTest("Windows filename spelling control")
        name = "method/examples/data/measurement.json"
        alias = "method/examples/data/MEASUREMENT.json"
        manifest = self.root / "MANIFEST.sha256"
        text = manifest.read_text(encoding="utf8")
        self.assertTrue((self.root / alias).is_file())
        manifest.write_text(text.replace("  " + name + "\n", "  " + alias + "\n"), encoding="utf8", newline="\n")
        with self.assertRaises(P.ValidationError):P.Snapshot(self.root).read(alias)

    def test_windows_short_name_alias_is_rejected(self) -> None:
        if os.name != "nt":self.skipTest("Windows short-name control")
        import ctypes
        path = self.root / "long-synthetic-measurement-file.json"
        path.write_bytes(b"synthetic alias control")
        buffer = ctypes.create_unicode_buffer(32768)
        get_short = ctypes.windll.kernel32.GetShortPathNameW
        get_short.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
        get_short.restype = ctypes.c_uint32
        length = get_short(str(path), buffer, len(buffer))
        if not length or length >= len(buffer):self.skipTest("No fixture short name available")
        alias = Path(buffer.value).name
        if alias.casefold() == path.name.casefold():self.skipTest("Fixture volume has no distinct short-name alias")
        self.manifest()
        manifest = self.root / "MANIFEST.sha256"
        with manifest.open("a", encoding="utf8", newline="\n") as output:
            output.write(hashlib.sha256(path.read_bytes()).hexdigest() + "  " + alias + "\n")
        with self.assertRaises(P.ValidationError):P.Snapshot(self.root).read(alias)

    def test_one_git_commit_ignores_later_working_tree_changes(self) -> None:
        self.git("init", "--initial-branch=main")
        commit = self.commit();reference = self.ref("method/examples/receipts/publication.json")
        self.write("method/examples/data/measurement.json", b"changed later");self.manifest()
        anchored = P.Snapshot(self.root, commit)
        self.assertEqual(anchored.state, "commit_snapshot")
        self.assertEqual(len(P.verify_receipt(anchored, reference)["nodes"]), 4)
        with self.assertRaises(P.ValidationError):self.verify()

    def test_mixed_commit_manifest_and_source_are_rejected(self) -> None:
        self.git("init", "--initial-branch=main")
        old = self.commit();old_ref = self.ref("method/examples/receipts/research.json")
        self.write("method/examples/data/measurement.json", b"new committed bytes");self.manifest()
        new = self.commit()
        self.assertEqual(P.verify_receipt(P.Snapshot(self.root, old), old_ref)["receipt"]["profile"], "research")
        with self.assertRaises(P.ValidationError):P.verify_receipt(P.Snapshot(self.root, new), old_ref)
        for ref in ["HEAD", "main", new[:7], new.upper(), "-invalid"]:
            with self.assertRaises(P.ValidationError):P.Snapshot(self.root, ref)

    def test_cli_reports_candidate_and_failing_mutation(self) -> None:
        command = [sys.executable, "-B", str(REPO / "method/v1/portable.py"), "--root", str(self.root)]
        for name, code in [("method/examples/receipts/publication.json", 0), ("method/examples/negative/source-hash.json", 1)]:
            reference = self.ref(name)
            result = subprocess.run(command + ["--receipt", name, "--sha256", reference["sha256"]], capture_output=True, timeout=30)
            self.assertEqual(result.returncode, code, result.stdout)
            value = json.loads(result.stdout)
            if code == 0:self.assertEqual(value["state"], "candidate")

    def test_malformed_field_types_raise_validation_errors(self) -> None:
        for mutate in [lambda c: c["checks"][0].update(id=[]),
                       lambda c: c["contract"]["plans"][0].update(kind={}),
                       lambda c: c.update(profile=[]),
                       lambda c: c.update(checks=None)]:
            card = self.card();mutate(card)
            with self.assertRaises(P.ValidationError):P.validate_card(card)

    def test_empty_inputs_and_strict_declared_schema(self) -> None:
        card = self.card();card["contract"]["inputs"] = [];P.validate_card(card)
        card["private_validation_report"] = "hidden"
        with self.assertRaises(P.ValidationError):P.validate_card(card)


if __name__ == "__main__":
    unittest.main()
