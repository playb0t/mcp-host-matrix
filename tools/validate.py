#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check repository data, prose, links and file integrity without network access."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from typing import Any, Iterator
from urllib.parse import unquote, urlsplit

class ValidationError(Exception):
    """The repository violates its declared data or packaging contract."""

STATUSES = frozenset({
    "measured_with_limits", "measured_negative_with_limits",
    "measured_positive_with_limits", "not_measured", "unknown",
    "measured",
})
TEXT_SUFFIXES = frozenset({".md", ".json", ".cff", ".yml", ".yaml", ".svg", ".txt", ".py", ".sha256", ".excalidraw"})
IGNORED_PARTS = frozenset({".git", "__pycache__", ".venv"})
HASH = re.compile(r"[0-9a-f]{64}")
IDENTIFIER = re.compile(r"[A-Za-z0-9_.:/\\@+,-]+")
BT = chr(96)

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)

def object_value(value: Any, label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label}: expected an object")
    return value

def array_value(value: Any, label: str) -> list[Any]:
    require(isinstance(value, list), f"{label}: expected an array")
    return value

def nonempty_strings(value: Any, label: str) -> list[str]:
    result = array_value(value, label)
    require(bool(result) and all(isinstance(x, str) and x.strip() for x in result), f"{label}: expected nonempty strings")
    return result

def natural(value: Any, label: str) -> int:
    require(type(value) is int and value >= 0, f"{label}: expected a nonnegative integer")
    return value

def unique(values: list[Any], label: str) -> None:
    require(len(values) == len(set(values)), f"{label}: duplicate value")

def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result

def _json_constant(value: str) -> Any:
    raise ValidationError(f"Nonfinite JSON constant: {value}")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_json_object, parse_constant=_json_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path.name}: invalid UTF-8 JSON: {exc}") from exc

def files(root: Path) -> list[Path]:
    result: list[Path] = []
    for path in root.rglob("*"):
        if any(part in IGNORED_PARTS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            require(path.resolve().is_relative_to(root.resolve()), "File resolves outside repository")
            result.append(path)
    return sorted(result)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def checked_path(root: Path, name: str) -> Path:
    require(bool(name) and "\\" not in name and not PurePosixPath(name).is_absolute(), "Invalid repository path")
    require(".." not in PurePosixPath(name).parts, "Repository path contains traversal")
    path = (root / name).resolve()
    require(path.is_relative_to(root.resolve()) and path.is_file(), f"Missing repository file: {name}")
    require(path.relative_to(root.resolve()).as_posix() == name, "Repository path is not canonical")
    return path

def count_relations(value: Any, label: str = "data") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "counts":
                counts = object_value(item, f"{label}.counts")
                for name, count in counts.items():
                    require(type(count) in (int, float) and math.isfinite(count) and count >= 0, f"{label}.counts.{name}: expected a nonnegative number")
                for components, total in (
                    (("base_windows", "operation_variants", "additional_healthy_windows"), "selected_run_ids"),
                    (("primary_windows", "operation_variants", "additional_timing_windows"), "selected_distinct_run_ids"),
                ):
                    if all(name in counts for name in (*components, total)):
                        require(sum(counts[name] for name in components) == counts[total], f"{label}: count components do not sum to {total}")
                if all(name in counts for name in ("conceptual_rows", "profiles_per_row", "measured_cells")):
                    require(counts["conceptual_rows"] * counts["profiles_per_row"] == counts["measured_cells"], f"{label}: row/profile product does not match cells")
            count_relations(item, f"{label}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            count_relations(item, f"{label}[{index}]")

def validate_data(data: Any, updates: Any, evidence: Any, root: Path | None = None) -> dict[str, int]:
    matrix = object_value(data, "matrix")
    update = object_value(updates, "update")
    catalog = object_value(evidence, "evidence")
    require(matrix.get("schema") == "mcp-host-matrix/1", "Unknown matrix schema")
    require(update.get("schema") == "mcp-update-bench-public/1", "Unknown update schema")
    require(catalog.get("schema") == "mcp-host-matrix-evidence/1", "Unknown evidence schema")
    scope = object_value(matrix.get("scope"), "matrix.scope")
    for field in ("full_protocol_audit", "exhaustive_host_coverage"):
        if field in scope:
            require(type(scope[field]) is bool, f"{field}: expected a boolean")
    cases = array_value(matrix.get("cases"), "matrix.cases")
    require(bool(cases), "Matrix has no cases")
    case_ids: list[str] = []
    for case in cases:
        case = object_value(case, "case")
        identifier = case.get("id")
        require(isinstance(identifier, str) and re.fullmatch(r"R\d{2}", identifier) is not None, "Invalid case ID")
        case_ids.append(identifier)
        require(isinstance(case.get("status"), str) and case.get("status") in STATUSES, f"{identifier}: invalid status")
        versions = object_value(case.get("versions"), f"{identifier}.versions")
        require(bool(versions) and all(isinstance(v, str) and v.strip() for v in versions.values()), f"{identifier}: missing version")
        for key in ("observations", "controls", "limits", "evidence_ids"):
            nonempty_strings(case.get(key), f"{identifier}.{key}")
        for key in ("native_hosts", "components"):
            items = array_value(case.get(key), f"{identifier}.{key}")
            require(all(isinstance(x, str) and x for x in items), f"{identifier}: invalid subject")
            unique(items, f"{identifier}.{key}")
        subcases = array_value(case.get("subcases", []), f"{identifier}.subcases")
        subids = []
        for item in subcases:
            item = object_value(item, f"{identifier}.subcase")
            require(isinstance(item.get("id"), str) and bool(item["id"]), "Missing subcase ID")
            require(isinstance(item.get("status"), str) and item.get("status") in STATUSES, f"{item['id']}: invalid status")
            subids.append(item["id"])
        unique(subids, f"{identifier}.subcases")
    unique(case_ids, "matrix.cases")
    artifacts = array_value(catalog.get("artifacts"), "evidence.artifacts")
    ids: list[str] = []
    for artifact in artifacts:
        artifact = object_value(artifact, "artifact")
        require(isinstance(artifact.get("id"), str) and bool(artifact["id"]), "Missing artifact ID")
        ids.append(artifact["id"])
        require(isinstance(artifact.get("sha256"), str) and HASH.fullmatch(artifact["sha256"]) is not None, f"{artifact['id']}: invalid SHA-256")
        if artifact.get("repository_file") is not None:
            require(isinstance(artifact["repository_file"], str), "Invalid artifact repository path")
            if root is not None:
                require(sha(checked_path(root, artifact["repository_file"])) == artifact["sha256"], f"{artifact['id']}: projection fingerprint mismatch")
    unique(ids, "evidence.artifacts")
    for case in cases:
        require(set(case["evidence_ids"]) <= set(ids), f"{case['id']}: unresolved evidence ID")
    cells = array_value(update.get("cells"), "update.cells")
    pairs: list[tuple[str, str]] = []
    for cell in cells:
        cell = object_value(cell, "update cell")
        require(all(isinstance(cell.get(k), str) and cell[k] for k in ("row", "profile")), "Missing row/profile")
        require(isinstance(cell.get("status"), str) and cell.get("status") in STATUSES, "Update cell has invalid status")
        pairs.append((cell["row"], cell["profile"]))
        codes = array_value(cell.get("controller_http_before_after"), "controller HTTP pair")
        require(len(codes) == 2 and all(type(x) is int and 100 <= x <= 599 for x in codes), "Invalid controller HTTP pair")
        require(type(cell.get("native_old_refresh_reused")) is bool, "Invalid native refresh reuse flag")
    unique(pairs, "update row/profile pairs")
    rows = {row for row, _ in pairs}
    for field, actual in (("selected_cells", len(cells)), ("conceptual_rows", len(rows))):
        if field in update:
            require(natural(update[field], field) == actual, f"{field}: count does not match records")
    survivors = {row for row in rows if all(c["controller_http_before_after"][-1] == 200 for c in cells if c["row"] == row)}
    native = {row for row in survivors if all(c["native_old_refresh_reused"] for c in cells if c["row"] == row)}
    for field, actual in (("authority_survival_rows", len(survivors)), ("compound_native_reuse_rows", len(native))):
        if field in update:
            require(natural(update[field], field) == actual, f"{field}: count does not match observations")
    count_relations(matrix)
    count_relations(update)
    return {"cases": len(cases), "update_cells": len(cells), "evidence_artifacts": len(artifacts)}

def privacy_check(name: str, text: str) -> None:
    patterns = (
        r"(?i)\b[A-Z]:[\\/]",
        r"/(?:home|Users)/[^/\s]+/",
        r"S-1-5-21-(?:\d+-){3}\d+",
        r"(?i)\bgh[pousr]_[A-Za-z0-9]{20,}",
        r"\bgithub_pat_[A-Za-z0-9_]{20,}",
    )
    require(not any(re.search(pattern, text) for pattern in patterns), f"{name}: personal path or credential pattern")

def mask_code(text: str, inline: bool = True) -> str:
    result: list[str] = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(" + BT + r"{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1]:
                fence = None
            result.append("\n" if line.endswith("\n") else "")
        elif fence:
            result.append("\n" if line.endswith("\n") else "")
        else:
            result.append(re.sub("(" + BT + r"+).*?\1", " ", line) if inline else line)
    return "".join(result)

def prose_issues(text: str, markdown: bool = False) -> list[str]:
    """Report high-confidence spacing defects, leaving technical literals alone."""
    text = mask_code(text) if markdown else text
    if not markdown and "_" in text and IDENTIFIER.fullmatch(text):
        return []
    text = re.sub(r"\[[A-Za-z0-9_./-]+\]\([^)]*\)", " ", text)
    text = re.sub(r"<[^>]*>", " ", text)
    text = re.sub(r"\]\([^)\n]*\)", "]", text)
    text = re.sub(r"\b(?:https?|mailto):\S+", " ", text)
    text = re.sub(r"\b(?:localhost|(?:\d{1,3}\.){3}\d{1,3}):\d{1,5}(?:/[^\s|]*)?", " ", text)
    text = re.sub(r"\b(?:[A-Za-z0-9_.-]+[\\/])+[A-Za-z0-9_.-]+\.[A-Za-z0-9]+", " ", text)
    text = re.sub(r"\b[A-Za-z0-9_-]+\.(?:md|jsonl?|svg|png|js|py|cff|toml|ya?ml)\b", " ", text)
    text = re.sub(r"\b(?:[A-Z][A-Za-z0-9_]*\.)+[A-Za-z][A-Za-z0-9_]*\b", " ", text)
    text = re.sub(r"\b[0-9a-f]{16,}\b", " ", text, flags=re.I)
    text = re.sub(r"\b(?:R\d{2}(?:-[A-Z]\d{2})?|r\d{2}\.[A-Za-z_0-9]+|N\d{2}|F\d{2}|Base64|UTF-?\d+(?:LE|BE)?|SHA-?\d+|MD5|WSL2|OAuth2|S256)\b", " ", text)
    text = re.sub(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b", " ", text)
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\b", " ", text)
    # Detect missing spaces at the edges before masking valid dates/versions/times.
    issues: list[str] = []
    for pattern in (r"[A-Za-z]((?:\d{4}-\d{2}-\d{2})|(?:\d+\.\d+\.\d+)|(?:\d{2}:\d{2}:\d{2}))", r"\d{4}-\d{2}-\d{2}[A-Za-z]"):
        issues.extend(text[max(0, m.start() - 16):m.end() + 16].replace("\n", " ").strip() for m in re.finditer(pattern, text))
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)?\b", " ", text)
    text = re.sub(r"\b\d{2}:\d{2}:\d{2}(?:\.\d+)?\b", " ", text)
    text = re.sub(r"\bv?\d+(?:\.\d+){2,}\b", " ", text)
    text = re.sub(r"\b[A-Za-z]\d{2,}\b", " ", text)
    patterns = (
        r"[:;,](?=[A-Za-z0-9])", r"(?<=[A-Za-z])\.(?=\d)",
        r"\b[A-Za-z]{2,}\d+", r"\d[A-Za-z]+",
        r"\b[a-z]+(?:HTTP|RPC|RT|PID|TTL|ACK)\b",
        r"\b(?:[a-z]+|[A-Z][a-z]+)[A-Z]\b",
        r"\b\d+\s+/(?=\d)", r"\b\d+/\s+(?=\d)",
    )
    for pattern in patterns:
        issues.extend(text[max(0, m.start() - 16):m.end() + 16].replace("\n", " ").strip() for m in re.finditer(pattern, text))
    return sorted(set(issues))

def string_values(value: Any, label: str = "$") -> Iterator[tuple[str, str]]:
    if isinstance(value, str):
        yield label, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from string_values(child, f"{label}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from string_values(child, f"{label}[{index}]")

def style_check(name: str, text: str, markdown: bool = False) -> None:
    issues = prose_issues(text, markdown)
    require(not issues, f"{name}: prose spacing near {issues[:4]}")

def heading_ids(text: str) -> set[str]:
    ids = set(re.findall(r'\bid=["' + "'" + r']([^"' + "'" + r']+)["' + "'" + "]", text))
    counts: dict[str, int] = {}
    for heading in re.findall(r"^#{1,6}\s+(.+)$", mask_code(text, inline=False), re.M):
        heading = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading)
        heading = re.sub(r"<[^>]+>", "", heading).replace(BT, "").replace("*", "").lower()
        identifier = "".join(c for c in heading if c.isalnum() or c in " _-").replace(" ", "-")
        n = counts.get(identifier, 0)
        counts[identifier] = n + 1
        ids.add(identifier + (f"-{n}" if n else ""))
    return ids

def link_destinations(text: str) -> Iterator[str]:
    """Read inline links with balanced parentheses and reference definitions."""
    text = mask_code(text)
    for match in re.finditer(r"!?\[[^\]\n]*\]\(", text):
        start = match.end()
        if text[start:start + 1] == "<":
            end = text.find(">", start + 1)
            require(end >= 0, "Unclosed angle-bracket Markdown link")
            yield text[start + 1:end]
            continue
        depth, index = 1, start
        while index < len(text) and depth:
            if text[index] == "\\":
                index += 2
                continue
            if text[index] == "(":
                depth += 1
            elif text[index] == ")":
                depth -= 1
            index += 1
        require(depth == 0, "Unclosed Markdown link")
        yield text[start:index - 1].strip().split(maxsplit=1)[0]
    definitions: dict[str, str] = {}
    for match in re.finditer(r"(?m)^ {0,3}\[([^\]\n]+)\]:[ \t]*(\S+)", text):
        if not match[1].startswith("^"):
            require(match[1] not in definitions, "Duplicate Markdown reference")
            definitions[match[1]] = match[2].strip("<>")
            yield definitions[match[1]]
    for match in re.finditer(r"\[([^\]\n]+)\]\[([^\]\n]*)\]", text):
        require((match[2] or match[1]) in definitions, "Unresolved Markdown reference")
    footnotes = re.findall(r"(?m)^ {0,3}\[\^([^\]\n]+)\]:", text)
    unique(footnotes, "Markdown footnotes")
    refs = re.findall(r"\[\^([^\]\n]+)\](?!:)", text)
    require(set(refs) <= set(footnotes), "Unresolved Markdown footnote")

def local_links(root: Path, path: Path, text: str) -> int:
    count = 0
    for destination in link_destinations(text):
        parsed = urlsplit(destination)
        if parsed.scheme or parsed.netloc:
            continue
        name, fragment = unquote(parsed.path), unquote(parsed.fragment)
        target = (path.parent / name).resolve() if name else path.resolve()
        require(target.is_relative_to(root.resolve()) and target.is_file(), f"{path.name}: missing or escaping link {destination}")
        if fragment and target.suffix == ".md":
            require(fragment in heading_ids(target.read_text(encoding="utf-8")), f"{path.name}: missing anchor {destination}")
        count += 1
    return count

def safe_svg_reference(value: str) -> bool:
    return value.startswith("#") or re.fullmatch(r"data:(?:image/(?:png|jpeg|webp)|font/woff2?|application/font-woff);base64,[A-Za-z0-9+/=\s]+", value) is not None


def validate_svg(path: Path) -> None:
    root = ET.parse(path).getroot()
    require(root.tag.rsplit("}", 1)[-1] == "svg", f"{path.name}: not an SVG")
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1].lower()
        require(tag not in {"script", "foreignobject", "iframe", "object", "embed", "audio", "video", "animate", "animatemotion", "animatetransform", "set"}, f"{path.name}: active SVG element")
        for key, value in element.attrib.items():
            name = key.rsplit("}", 1)[-1].lower()
            require(not name.startswith("on"), f"{path.name}: SVG event handler")
            if name in {"href", "src"}:
                require(safe_svg_reference(value), f"{path.name}: external SVG resource")
            for reference in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", value, re.I):
                require(safe_svg_reference(reference), f"{path.name}: external SVG resource")
        if tag == "style":
            css = element.text or ""
            require("@import" not in css.lower(), f"{path.name}: SVG CSS import")
            for reference in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", css, re.I):
                require(safe_svg_reference(reference), f"{path.name}: external SVG font/resource")

def verify_file_fingerprints(root: Path, value: Any) -> None:
    """Check declared repository-file/SHA-256 pairs in structured documents."""
    if isinstance(value, dict):
        if "repository_file" in value:
            name, digest = value["repository_file"], value.get("sha256")
            require(isinstance(name, str), "Invalid fingerprint repository path")
            require(isinstance(digest, str) and HASH.fullmatch(digest) is not None, "Invalid declared SHA-256")
            require(sha(checked_path(root, name)) == digest, f"Repository fingerprint mismatch: {name}")
        for child in value.values():
            verify_file_fingerprints(root, child)
    elif isinstance(value, list):
        for child in value:
            verify_file_fingerprints(root, child)


def validate(root: Path, manifest: bool = True) -> dict[str, int]:
    root = root.resolve()
    data = read_json(root / "matrix/RESULTS.json")
    updates = read_json(root / "disconnect/bench/UPDATE-RESULTS.json")
    evidence = read_json(root / "matrix/EVIDENCE.json")
    result = validate_data(data, updates, evidence, root)
    link_count = 0
    for path in files(root):
        name = path.relative_to(root).as_posix()
        if path.suffix in TEXT_SUFFIXES or path.name in {"LICENSE", ".gitignore", ".gitattributes"}:
            text = path.read_text(encoding="utf-8")
            require(b"\r" not in path.read_bytes(), f"{name}: use LF")
            privacy_check(name, text)
            if path.suffix in {".json", ".excalidraw"}:
                document = read_json(path)
                verify_file_fingerprints(root, document)
                if path.suffix == ".excalidraw":
                    scene = object_value(document, name)
                    require(scene.get("type") == "excalidraw", f"{name}: invalid scene type")
                    array_value(scene.get("elements"), f"{name}.elements")
                else:
                    count_relations(document, name)
                    for label, value in string_values(document):
                        style_check(f"{name}:{label}", value)
            elif path.suffix == ".md":
                style_check(name, text, markdown=True)
                link_count += local_links(root, path, text)
            elif path.suffix == ".svg":
                validate_svg(path)
    checked = 0
    if manifest:
        known: set[str] = set()
        for line in (root / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
            require("  " in line, "Invalid manifest line")
            digest, name = line.split("  ", 1)
            require(HASH.fullmatch(digest) is not None, "Invalid manifest digest")
            require(name not in known and name != "MANIFEST.sha256", "Duplicate or recursive manifest entry")
            require(sha(checked_path(root, name)) == digest, f"Checksum mismatch: {name}")
            known.add(name)
            checked += 1
        expected = {p.relative_to(root).as_posix() for p in files(root) if p != root / "MANIFEST.sha256"}
        require(known == expected, "Manifest must cover every distributable file")
    result.update(local_links=link_count, manifest_files=checked)
    return result

def write_manifest(root: Path) -> None:
    entries = [f"{sha(path)}  {path.relative_to(root).as_posix()}" for path in files(root) if path != root / "MANIFEST.sha256"]
    (root / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8", newline="\n")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    try:
        if args.write_manifest:
            validate(args.root, manifest=False)
            write_manifest(args.root.resolve())
        print(json.dumps({"status": "PASS", **validate(args.root)}, sort_keys=True))
        return 0
    except (ValidationError, OSError, UnicodeError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
