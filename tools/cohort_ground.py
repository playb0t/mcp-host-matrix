"""Verify a declared set of provider observation windows from the revoke-bench projection."""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("Window cohort: " + reason)


def fingerprint(value: Any, label: str) -> str:
    require(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None,
            "invalid " + label + " fingerprint")
    return value


def unique_ids(values: list[str], name: str) -> set[str]:
    require(isinstance(values, list) and bool(values)
            and all(isinstance(item, str) and item for item in values), name + " IDs required")
    ids = set(values)
    require(len(ids) == len(values), "duplicate " + name + " ID")
    return ids


def revocation(value: Any) -> tuple[str, list[int]]:
    """A negative recording permits neither a captured request nor a response."""
    if value == "none":
        return "none", []
    require(isinstance(value, dict) and set(value) == {"request", "request_ids", "responses"},
            "invalid revocation representation")
    state, ids, responses = value["request"], value["request_ids"], value["responses"]
    require(isinstance(ids, list) and isinstance(responses, list), "invalid revocation lists")
    if state == "none":
        require(not ids and not responses, "contradictory revocation absence")
        return state, []
    require(state == "sent", "unknown revocation state")
    received = unique_ids(ids, "revoke request")
    statuses = []
    answered = set()
    for response in responses:
        ident = response["request_id"]
        require(ident in received and ident not in answered, "unbound revoke response")
        require(type(response["http_status"]) is int, "invalid response status")
        answered.add(ident)
        statuses.append(response["http_status"])
    return state, statuses


def verify_selection(selection: dict, sources: dict, rows: list[dict]) -> str:
    timing = selection["timing"]
    if timing == "retrospective":
        require(set(selection) == {"timing", "run_ids"}, "unexpected retrospective fields")
        return timing
    require(timing == "before_measurement" and set(selection) == {"timing", "run_ids", "plan", "journal"},
            "before_measurement requires a plan and capture journal")
    plan = sources[selection["plan"]]
    journal = sources[selection["journal"]]
    require(isinstance(plan, dict) and plan.get("schema") == "window-plan/1"
            and plan.get("run_ids") == selection["run_ids"], "committed plan differs")
    digest = hashlib.sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True,
                            separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    require(isinstance(journal, dict) and journal.get("schema") == "window-plan-history/1",
            "capture journal required")
    history = journal["events"]
    require(isinstance(history, list) and history and history[0] == {
            "kind": "plan_sealed", "plan_sha256": digest}, "plan must precede run starts")
    expected = {row["run_id"]: row["source_verdict_sha256"] for row in rows}
    started: set[str] = set()
    finished: set[str] = set()
    for event in history[1:]:
        run = event["run_id"]
        require(run in expected, "journal run outside cohort")
        if event == {"kind": "started", "run_id": run, "plan_sha256": digest}:
            require(run not in started, "duplicate start")
            started.add(run)
        else:
            require(event == {"kind": "finished", "run_id": run, "verdict_sha256": expected[run]}
                    and run in started and run not in finished, "unbound journal event")
            finished.add(run)
    require(finished == set(expected), "incomplete capture journal")
    return timing


def evaluate(spec: dict, sources: dict[str, Any]) -> dict:
    try:
        return _evaluate(spec, sources)
    except (KeyError, TypeError, AttributeError, IndexError) as exc:
        raise ValueError("Window cohort: missing or malformed evidence") from exc


def _evaluate(spec: dict, sources: dict[str, Any]) -> dict:
    require(isinstance(spec, dict) and set(spec) == {"bench", "receipt", "selection", "minimum_seconds",
            "logout_control"}, "unexpected parameters")
    bench = sources[spec["bench"]]
    receipt = sources[spec["receipt"]]
    require(bench["schema"] == "revoke-bench-public/1" and receipt["schema"] == "mcp-host-matrix-receipt/1",
            "unexpected source schemas")
    raw_hash = fingerprint(bench["source"]["results_sha256"], "source")
    source_ids = [row["id"] for row in receipt["sources"] if row["sha256"] == raw_hash]
    require(len(source_ids) == 1, "unbound source projection")
    excerpts: dict[str, dict] = {}
    for entry in receipt["excerpts"]:
        if entry["source_id"] == source_ids[0]:
            ptr = entry["source_pointer"]
            require(ptr not in excerpts, "duplicate excerpt")
            excerpts[ptr] = entry["fields"]

    threshold = spec["minimum_seconds"]
    require(type(threshold) in (int, float) and math.isfinite(threshold) and threshold > 0,
            "invalid observation threshold")
    plan = unique_ids(spec["selection"]["run_ids"], "planned")
    base = bench["base_cells"]
    variants = bench["operation_variants"]
    extra = bench["additional_timing_windows"]
    require(all(isinstance(group, list) for group in (base, variants, extra)), "invalid run series")
    unique_ids([row["run_id"] for group in (base, variants, extra) for row in group], "recorded")
    require(plan == {row["run_id"] for row in base}, "declared cohort differs from base run IDs")
    for row in base:
        fingerprint(row["source_verdict_sha256"], "verdict")
    timing = verify_selection(spec["selection"], sources, base)
    confirmed = contradicted = unknown = 0
    routes: dict[str, set[str]] = {}
    for row in base:
        ptr = row["source_pointer"]
        require(isinstance(ptr, str) and ptr.startswith("/base_cells/") and ptr.endswith("/observation"),
                "expected base observation pointer")
        identity = excerpts[ptr.rsplit("/", 1)[0]]
        require(all(identity[k] == row[k] for k in ("run_id", "profile", "version")),
                "window identity differs")
        # The public projection appends the bridge version to its display label.
        client = identity["client"]
        bridge_version = identity["version"].split(" / ")[-1]
        require(row["client"] == client or (" -> " in client and " / " in identity["version"]
                and row["client"] == f"{client} {bridge_version}"), "window route differs")
        recorded = excerpts[ptr]
        state, statuses = revocation(recorded["revocation_request"])
        require(state == row["revocation_request"] and statuses == row.get("revocation_response_http_statuses", []),
                "revocation observations differ")
        require(all(recorded[k] == row[k] for k in ("operation", "source_verdict_sha256")),
                "window source or operation differs")
        for key in ("observation_completed", "native_tool_begin_observed"):
            require(type(recorded[key]) is bool and recorded[key] is row[key], "window health differs")
        seconds = row["after_ack_seconds"]
        require(type(seconds) in (int, float) and math.isfinite(seconds) and seconds >= 0
                and type(recorded["after_ack_seconds"]) in (int, float)
                and recorded["after_ack_seconds"] == seconds, "window duration differs")
        routes.setdefault(row["client"], set()).add(row["profile"])
        if state == "sent":
            contradicted += 1
        elif row["observation_completed"] and row["native_tool_begin_observed"] and seconds >= threshold:
            confirmed += 1
        else:
            unknown += 1

    control = next((row for row in variants if row["run_id"] == spec["logout_control"]), None)
    require(control is not None and control["operation"] == "logout"
            and control["observation_completed"] is True and control["native_tool_begin_observed"] is True,
            "qualified logout control required")
    ptr = control["source_pointer"]
    require(ptr.startswith("/operation_variants/"), "logout must be outside the base cohort")
    obs = excerpts[ptr]
    require(all(obs[k] == control[k] for k in ("run_id", "profile", "operation")), "logout identity differs")
    state, statuses = revocation(obs["revocation_request"])
    require(state == control["revocation_request"] == "sent" and statuses
            and len(statuses) == len(obs["revocation_request"]["request_ids"])
            and all(status == 200 for status in statuses) and statuses == control["revocation_response_http_statuses"],
            "logout receipt not acknowledged")
    require(control["same_prior_refresh_token"] is True, "logout replay token differs")
    for key, code, error in [("controller_refresh_before", 200, None), ("controller_refresh_after", 400, "invalid_grant")]:
        checkpoint = excerpts[ptr + "/" + key]
        require(all(checkpoint[k] == control[key][k] == value for k, value in
                    (("initiator", "controller"), ("http_status", code), ("error", error))),
                "logout replay control differs")
    return {"selection": timing, "minimum_seconds": threshold, "declared": len(plan),
            "confirmed": confirmed, "contradicted": contradicted, "unknown": unknown,
            "profiles_by_route": {route: sorted(profiles) for route, profiles in sorted(routes.items())},
            "control": {"run_id": control["run_id"], "revoke_responses": statuses,
                        "prior_refresh_before": 200, "prior_refresh_after": 400, "error": "invalid_grant"}}
