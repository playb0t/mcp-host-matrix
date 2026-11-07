#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Verify public work records in one manifest-bound repository snapshot.

These checks establish declared-record consistency and byte identity. They do
not execute observations, authenticate humans, publish files or contact hosts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from typing import Any

VERSION = "1.0.0"
PROFILES = {
    "engineering": {"change": "change", "validation": "command", "regression": "command"},
    "research": {"question": "assessment", "method": "assessment", "controls": "command",
                 "observations": "artifact", "conclusion": "assessment"},
    "document": {"sources": "assessment", "format": "document", "content": "assessment"},
    "publication": {"payload": "payload", "recipient": "assessment", "delivery": "publication"},
}
KINDS = frozenset({kind for values in PROFILES.values() for kind in values.values()})
RELATIONS = frozenset({"input", "research_basis", "publication_input"})
MAX_FILE = 64 * 1024 * 1024
MAX_JSON = 2 * 1024 * 1024
MAX_FILES = 10000
MAX_NODES = 512
MAX_DEPTH = 64
HASH = re.compile(r"[0-9a-f]{64}")


class ValidationError(ValueError):
    """A record or its selected snapshot violates the public method."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    require(isinstance(value, dict) and set(value) == keys, label + ": unexpected fields")
    return value


def _text(value: Any, label: str, limit: int = 10000) -> str:
    require(isinstance(value, str) and bool(value.strip()) and len(value) <= limit,
            label + ": nonempty bounded text required")
    return value


def _hash(value: Any) -> str:
    require(isinstance(value, str) and HASH.fullmatch(value) is not None, "Invalid SHA-256")
    return value


def logical_path(value: Any) -> str:
    value = _text(value, "Logical path", 1000)
    require("\\" not in value and not value.startswith("/"), "Absolute or nonportable path")
    for part in value.split("/"):
        require(part not in ("", ".", "..") and part.casefold() != ".git" and not part.endswith((" ", ".")) and
                re.search(r'[<>:"|?*\x00-\x1f]', part) is None and
                re.match(r"^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)", part, re.I) is None,
                "Noncanonical logical path or Windows alias")
    return value


def _ref(value: Any) -> dict[str, str]:
    value = _object(value, {"logical_path", "sha256"}, "Reference")
    logical_path(value["logical_path"]);_hash(value["sha256"])
    return value


def _method_ref(value: Any) -> dict[str, str]:
    value = _object(value, {"id", "version", "logical_path", "sha256"}, "Method reference")
    require(value["id"] == "work-evidence" and value["version"] == VERSION,
            "Unsupported method identity or version")
    logical_path(value["logical_path"]);_hash(value["sha256"])
    require(Path(value["logical_path"]).name == "MANIFEST.json", "Method manifest name differs")
    return value


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        require(key not in result, "Duplicate JSON key")
        result[key] = value
    return result


def load_json(raw: bytes) -> dict[str, Any]:
    require(len(raw) <= MAX_JSON, "JSON size limit exceeded")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=lambda _: require(False, "Nonfinite JSON"))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValidationError("Invalid bounded UTF-8 JSON") from exc
    require(isinstance(value, dict), "JSON object required")
    return value


def _unlinked(path: Path) -> None:
    for parent in (path, *path.parents):
        info = parent.lstat()
        require(not stat.S_ISLNK(info.st_mode) and
                not getattr(info, "st_file_attributes", 0) & 0x400, "Linked or reparse path")
        if stat.S_ISREG(info.st_mode):
            require(info.st_nlink == 1, "Hardlinked file")


class Snapshot:
    """Read only manifest-listed bytes from a candidate or one explicit Git tree.

    A commit snapshot does not establish that the commit was published to a
    particular remote. Obtain the expected repository and commit independently.
    """
    def __init__(self, root: Path, commit: str | None = None) -> None:
        raw_root = str(root)
        require(not raw_root.startswith(("\\\\", "//")), "Network roots are not accepted")
        self.root = Path(root).absolute()
        _unlinked(self.root)
        require(self.root.is_dir() and self.root.resolve() == self.root, "Canonical directory required")
        self.commit = commit
        self.state = "candidate" if commit is None else "commit_snapshot"
        if commit is not None:
            require(isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit) is not None,
                    "Commit must be a full lowercase Git object ID")
            require(self._git(["cat-file", "-t", commit]).strip() == b"commit", "Commit object required")
        manifest = self._raw("MANIFEST.sha256", MAX_JSON)
        self.manifest_sha256 = digest(manifest)
        self.manifest: dict[str, str] = {}
        aliases: set[str] = set()
        try:
            lines = manifest.decode("utf-8").splitlines()
        except UnicodeError as exc:
            raise ValidationError("Manifest is not UTF-8") from exc
        require(b"\r" not in manifest and manifest.endswith(b"\n"), "Manifest must use LF with a final newline")
        require(0 < len(lines) <= MAX_FILES, "Manifest entry limit")
        for line in lines:
            require(len(line) >= 67 and line[64:66] == "  ", "Invalid manifest line")
            sha, name = _hash(line[:64]), logical_path(line[66:])
            require(name != "MANIFEST.sha256" and name.casefold() not in aliases,
                    "Recursive or duplicate manifest entry")
            aliases.add(name.casefold());self.manifest[name] = sha

    def _git(self, args: list[str]) -> bytes:
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        try:
            result = subprocess.run(["git", "--no-replace-objects", "-C", str(self.root), *args],
                                    capture_output=True, timeout=20, env=env)
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValidationError("Git snapshot read failed") from exc
        require(result.returncode == 0, "Git snapshot object unavailable")
        return result.stdout

    def _raw(self, name: str, limit: int = MAX_FILE) -> bytes:
        logical_path(name)
        if self.commit is not None:
            entry = self._git(["ls-tree", "-z", self.commit, "--", name])
            require(entry.endswith(b"\x00") and entry.count(b"\x00") == 1, "Snapshot file unavailable")
            metadata, stored_name = entry[:-1].split(b"\t", 1)
            fields = metadata.split(b" ")
            require(len(fields) == 3 and fields[0] in (b"100644", b"100755") and
                    fields[1] == b"blob" and stored_name.decode("utf-8") == name,
                    "Snapshot entry is not a regular file")
            obj = fields[2].decode("ascii")
            size = int(self._git(["cat-file", "-s", obj]).strip())
            require(0 <= size <= limit, "Snapshot file exceeds size limit")
            raw = self._git(["cat-file", "blob", obj])
            require(len(raw) == size, "Git object size changed")
            return raw
        path = self.root.joinpath(*name.split("/"))
        try:
            resolved = path.resolve()
            require(resolved.is_relative_to(self.root) and resolved.relative_to(self.root).as_posix() == name,
                    "Candidate path spelling is an alias")
            _unlinked(path);before = path.stat()
            require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, "Bounded regular file required")
            with path.open("rb") as stream:
                opened = os.fstat(stream.fileno())
                require((opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino), "File replaced")
                raw = stream.read(limit + 1)
            _unlinked(path);after = path.stat()
        except OSError as exc:
            raise ValidationError("Candidate file unavailable") from exc
        require(len(raw) <= limit and
                (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), "File changed during read")
        return raw

    def assert_anchor(self) -> None:
        require(digest(self._raw("MANIFEST.sha256", MAX_JSON)) == self.manifest_sha256,
                "Repository manifest changed during verification")

    def read(self, name: str) -> bytes:
        name = logical_path(name)
        require(name in self.manifest, "File is not covered by the selected repository manifest")
        self.assert_anchor()
        raw = self._raw(name)
        require(digest(raw) == self.manifest[name], "Repository file fingerprint differs")
        self.assert_anchor()
        return raw


def read_ref(snapshot: Snapshot, value: Any) -> bytes:
    value = _ref(value)
    raw = snapshot.read(value["logical_path"])
    require(digest(raw) == value["sha256"], "Reference fingerprint differs")
    return raw


def verify_method(snapshot: Snapshot, method_ref: Any) -> dict[str, Any]:
    ref = _method_ref(method_ref)
    value = load_json(read_ref(snapshot, {key: ref[key] for key in ("logical_path", "sha256")}))
    _object(value, {"schema", "id", "version", "files"}, "Method manifest")
    require(value["schema"] == "work-method-manifest/1" and value["id"] == ref["id"] and
            value["version"] == ref["version"], "Method manifest identity differs")
    entries = value["files"]
    require(isinstance(entries, list) and len(entries) == 3, "Method bundle must contain its three declared files")
    prefix = ref["logical_path"].rsplit("/", 1)[0]
    expected = {prefix + "/" + name for name in ("portable.py", "SPEC.json", "README.md")}
    actual: set[str] = set()
    for entry in entries:
        _object(entry, {"logical_path", "sha256", "size"}, "Method file")
        name = logical_path(entry["logical_path"])
        require(name not in actual and type(entry["size"]) is int and 0 <= entry["size"] <= MAX_FILE,
                "Duplicate or invalid method file")
        raw = read_ref(snapshot, {key: entry[key] for key in ("logical_path", "sha256")})
        require(len(raw) == entry["size"], "Method file size differs")
        actual.add(name)
    require(actual == expected, "Method file set differs")
    definition = load_json(snapshot.read(prefix + "/SPEC.json"))
    require(definition.get("schema") == "work-method-spec/1" and definition.get("profiles") == PROFILES,
            "Method specification profiles differ")
    return value


def _validate_card(card: Any) -> None:
    card = _object(card, {"schema", "case_id", "profile", "variant", "method_ref", "contract",
                          "checks", "outcome", "limits"}, "Card")
    require(card["schema"] == "work-method-card/1", "Unknown card schema")
    require(isinstance(card["case_id"], str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", card["case_id"]) is not None,
            "Invalid case identifier")
    profile = card["profile"]
    require(isinstance(profile, str) and profile in PROFILES, "Unknown work profile")
    require(card["variant"] is None or card["variant"] == "mcp" and profile == "research",
            "MCP is a research variant")
    _method_ref(card["method_ref"])
    contract = _object(card["contract"], {"scope", "completion", "options", "inputs", "plans", "exclusions"}, "Contract")
    _text(contract["scope"], "Scope")
    require(contract["completion"] in ("verified", "bounded"), "Invalid completion mode")
    options = contract["options"]
    require(isinstance(options, dict), "Options object required")
    inputs = contract["inputs"]
    require(isinstance(inputs, list) and len(inputs) <= 1000, "Invalid input list")
    seen_inputs: set[str] = set()
    for item in inputs:
        name = _ref(item)["logical_path"]
        require(name.casefold() not in seen_inputs, "Duplicate input")
        seen_inputs.add(name.casefold())
    if profile == "engineering":
        require(options.get("change_mode") in ("changed", "no_change"), "Engineering change mode required")
        require("research_derived" not in options or type(options["research_derived"]) is bool,
                "Research-derived flag must be boolean")
    elif profile == "research":
        require(options.get("mode") in ("source", "experimental"), "Research mode required")
    elif profile == "document":
        require(options.get("format") in ("md", "text", "json", "html", "docx", "pdf", "pptx", "xlsx"),
                "Document format required")
        require("original_content" not in options or type(options["original_content"]) is bool,
                "Original-content flag must be boolean")
    else:
        require(options.get("stage") in ("prepared", "published"), "Publication stage required")
        destination = options.get("destination")
        require(isinstance(destination, dict) and set(destination) == {"channel", "target"}, "Publication destination required")
        _text(destination["channel"], "Destination channel");_text(destination["target"], "Destination target")
    exclusions = contract["exclusions"]
    require(isinstance(exclusions, dict), "Exclusions object required")
    allowed = ({"regression"} if profile == "engineering" else
               {"controls"} if profile == "research" and options["mode"] == "source" else
               {"sources"} if profile == "document" and options.get("original_content") is True else
               {"delivery"} if profile == "publication" and options["stage"] == "prepared" else set())
    require(set(exclusions) <= allowed, "Profile requirement cannot be excluded")
    for reason in exclusions.values():_text(reason, "Exclusion reason")
    plans = contract["plans"]
    require(isinstance(plans, list) and 1 <= len(plans) <= 1000, "Invalid check plan")
    plan_by_id: dict[str, dict[str, str]] = {}
    purposes: set[str] = set()
    for plan in plans:
        _object(plan, {"id", "purpose", "kind"}, "Check plan")
        ident = _text(plan["id"], "Check identifier", 128)
        purpose = _text(plan["purpose"], "Check purpose", 128)
        require(ident not in plan_by_id and purpose not in purposes and plan["kind"] in KINDS,
                "Duplicate or invalid check plan")
        if purpose in PROFILES[profile]:
            require(plan["kind"] == PROFILES[profile][purpose], "Required check kind differs")
        plan_by_id[ident] = plan;purposes.add(purpose)
    require(purposes.isdisjoint(exclusions) and set(PROFILES[profile]) <= purposes | set(exclusions),
            "Required check omitted")
    checks = card["checks"]
    require(isinstance(checks, list) and len(checks) == len(plans), "Result set differs from plan")
    result_ids: set[str] = set()
    states: list[str] = []
    for check in checks:
        require(isinstance(check, dict) and check.get("id") in plan_by_id, "Unplanned result")
        plan = plan_by_id[check["id"]]
        conclusion = profile == "research" and plan["purpose"] == "conclusion"
        keys = {"id", "kind", "state", "reason", "evidence_refs"} | ({"verdict"} if conclusion else set())
        _object(check, keys, "Check result")
        require(check["id"] not in result_ids and check["kind"] == plan["kind"] and
                check["state"] in ("passed", "failed", "incomplete"), "Invalid result binding or state")
        _text(check["reason"], "Result reason")
        evidence = check["evidence_refs"]
        require(isinstance(evidence, list) and 1 <= len(evidence) <= 1000, "Public check evidence required")
        for item in evidence:_ref(item)
        if conclusion:
            require(check["verdict"] in ("supported", "refuted", "inconclusive"), "Research verdict required")
        result_ids.add(check["id"]);states.append(check["state"])
    limits = card["limits"]
    require(isinstance(limits, list) and len(limits) <= 1000, "Limits list required")
    for item in limits:_text(item, "Limit")
    failed = any(state != "passed" for state in states)
    if failed:
        require(contract["completion"] == "bounded" and bool(limits), "Mandatory checks did not pass")
    if profile == "publication":
        require(not failed, "Publication cannot hide missing delivery as bounded completion")
        expected = options["stage"]
    else:
        expected = "bounded" if failed else "assessed" if profile == "research" else "verified"
    require(card["outcome"] == expected, "Outcome differs from recorded checks")



def validate_card(card: Any) -> None:
    """Reject malformed declared records with a consistent validation error."""
    try:
        _validate_card(card)
    except (KeyError, TypeError, RecursionError) as exc:
        raise ValidationError("Invalid card field type or structure") from exc


def verify_receipt(snapshot: Snapshot, ref: Any) -> dict[str, Any]:
    """Verify a public receipt DAG without reading data outside its snapshot."""
    seen: dict[tuple[str, str], tuple[dict, dict]] = {}
    active: set[str] = set()
    nodes: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []

    def visit(link: Any, depth: int) -> tuple[dict, dict]:
        link = _ref(link);name = link["logical_path"];pin = link["sha256"];key = (name, pin)
        require(depth <= MAX_DEPTH and name not in active, "Receipt depth or cycle limit")
        if key in seen:return seen[key]
        require(len(seen) + len(active) < MAX_NODES, "Receipt node limit")
        value = load_json(read_ref(snapshot, link))
        _object(value, {"schema", "case_id", "profile", "variant", "method_ref", "contract_ref",
                        "artifacts", "parents", "outcome", "withheld"}, "Receipt")
        require(value["schema"] == "work-method-receipt/1", "Unknown receipt schema")
        verify_method(snapshot, value["method_ref"])
        card = load_json(read_ref(snapshot, value["contract_ref"]))
        validate_card(card)
        require(all(value[field] == card[field] for field in ("case_id", "profile", "variant", "method_ref", "outcome")),
                "Receipt differs from its card")
        for item in card["contract"]["inputs"]:read_ref(snapshot, item)
        for check in card["checks"]:
            for item in check["evidence_refs"]:read_ref(snapshot, item)
        withheld = _object(value["withheld"], {"internal_artifacts", "private_artifacts"}, "Withheld counts")
        require(all(type(count) is int and 0 <= count <= 1000000 for count in withheld.values()),
                "Withheld metadata must contain counts only")
        outputs = value["artifacts"]
        require(isinstance(outputs, list) and 1 <= len(outputs) <= 1000, "Public outputs required")
        output_names: set[str] = set()
        for output in outputs:
            _object(output, {"logical_path", "sha256", "size", "visibility"}, "Public artifact")
            name_out = logical_path(output["logical_path"])
            require(name_out.casefold() not in output_names and output["visibility"] == "public" and
                    type(output["size"]) is int and 0 <= output["size"] <= MAX_FILE,
                    "Duplicate, private or invalid public artifact")
            raw = read_ref(snapshot, {key: output[key] for key in ("logical_path", "sha256")})
            require(len(raw) == output["size"], "Artifact size differs")
            output_names.add(name_out.casefold())
            artifacts.append(dict(output, receipt_sha256=pin))
        parents = value["parents"]
        require(isinstance(parents, list) and len(parents) <= 100, "Invalid parent list")
        active.add(name);parent_links: set[tuple[str, str]] = set();parent_artifacts: set[str] = set()
        for parent in parents:
            _object(parent, {"ref", "relation"}, "Parent")
            require(parent["relation"] in RELATIONS, "Unknown parent relation")
            parent_ref = _ref(parent["ref"])
            parent_key = (parent_ref["logical_path"], parent["relation"])
            require(parent_key not in parent_links, "Duplicate parent relation")
            parent_links.add(parent_key)
            previous, _ = visit(parent_ref, depth + 1)
            require(parent["relation"] != "research_basis" or previous["profile"] == "research",
                    "Research basis parent must be research")
            if parent["relation"] == "publication_input":
                parent_artifacts.update(item["sha256"] for item in previous["artifacts"])
        if value["profile"] == "engineering" and card["contract"]["options"].get("research_derived") is True:
            require(any(parent["relation"] == "research_basis" for parent in parents), "Research-derived patch lacks research basis")
        if value["profile"] == "publication":
            require(any(parent["relation"] == "publication_input" for parent in parents), "Publication needs receipt input")
            require({item["sha256"] for item in outputs} <= parent_artifacts,
                    "Publication output lacks direct accepted public input")
        active.remove(name);seen[key] = (value, card)
        nodes.append({"ref": dict(link), "case_id": value["case_id"], "profile": value["profile"]})
        return value, card

    try:
        value, card = visit(ref, 0)
        snapshot.assert_anchor()
        return {"receipt": value, "card": card, "nodes": nodes, "artifacts": artifacts}
    except (OSError, KeyError, TypeError, UnicodeError, RecursionError) as exc:
        raise ValidationError("Invalid or unavailable receipt graph") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--commit")
    args = parser.parse_args()
    try:
        snapshot = Snapshot(args.root, args.commit)
        result = verify_receipt(snapshot, {"logical_path": args.receipt, "sha256": args.sha256})
        print(json.dumps({"status": "PASS", "state": snapshot.state, "commit": snapshot.commit,
                          "receipt_nodes": len(result["nodes"]), "public_artifacts": len(result["artifacts"])}))
        return 0
    except (ValidationError, OSError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
