"""Check the order of log entries inside one reviewed, fingerprinted run capture."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta
from typing import Any

UTC_MS = r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z"
LOG_ENTRY = re.compile(rf"\[({UTC_MS})\]\[([1-9][0-9]*)\] (.+)")
MILLISECOND = timedelta(milliseconds=1)
SHA256 = re.compile(r"[0-9a-f]{64}")


def _require(test: bool, message: str) -> None:
    if not test:
        raise ValueError("Event order: " + message)


def _unique_object(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(items)
    _require(len(result) == len(items), "ambiguous duplicate key in extract")
    return result


def _lookup(values: dict, key: Any) -> dict:
    _require(isinstance(key, str) and isinstance(values.get(key), dict), "source or event unavailable")
    return values[key]


def evaluate(spec: dict, sources: dict[str, Any]) -> dict:
    """Measure line and UTC order. The run-to-stream provenance is reviewed evidence."""
    required = {"receipt", "capture", "events", "run_fields"}
    _require(isinstance(spec, dict) and set(spec) in (required, required | {"sequence_form"}), "invalid parameters")
    opener = "sequence_form" in spec
    if opener:
        _require(spec["sequence_form"] == "bridge-opener-log-v1", "unknown named event sequence")
    receipt = _lookup(sources, spec["receipt"])
    capture = _lookup(sources, spec["capture"])
    _require(set(capture) == {"schema", "case_id", "run_source", "run_sha256", "clock",
                              "log_sha256", "extract_source", "extract_text"} and
             capture["schema"] == "matrix-log-extract/1" and capture["case_id"] == receipt.get("case_id"),
             "capture and receipt differ")
    _require(isinstance(capture["log_sha256"], str) and SHA256.fullmatch(capture["log_sha256"]) is not None
             and capture["clock"] == "bridge-log-utc-ms", "invalid log fingerprint or clock")
    entries = receipt.get("sources")
    _require(isinstance(entries, list), "receipt sources unavailable")
    pins: dict[str, str] = {}
    for entry in entries:
        _require(isinstance(entry, dict) and isinstance(entry.get("id"), str) and
                 entry["id"] not in pins and isinstance(entry.get("sha256"), str)
                 and SHA256.fullmatch(entry["sha256"]) is not None, "invalid receipt source")
        pins[entry["id"]] = entry["sha256"]
    run = capture["run_source"]
    _require(isinstance(run, str) and run in pins and pins[run] == capture["run_sha256"], "run pin differs")
    # The capture and every locator could consistently name the wrong run. Match
    # independently declared selection fields against the receipt's run excerpts.
    fields = spec["run_fields"]
    excerpts = receipt.get("excerpts")
    _require(isinstance(fields, dict) and fields and isinstance(excerpts, list), "invalid receipt run selector")
    matching_runs = {
        row["source_id"] for row in excerpts
        if isinstance(row, dict) and isinstance(row.get("source_id"), str) and
        row.get("source_pointer") == "" and isinstance(row.get("fields"), dict) and
        all(key in row["fields"] and json.dumps(row["fields"][key], sort_keys=True) == json.dumps(value, sort_keys=True)
            for key, value in fields.items())
    }
    _require(matching_runs == {run}, "receipt run selector does not identify the capture")
    text = capture["extract_text"]
    extract = capture["extract_source"]
    _require(isinstance(text, str) and isinstance(extract, str) and extract != run and
             hashlib.sha256(text.encode("utf-8")).hexdigest() == pins.get(extract), "extract digest differs")
    records = json.loads(text, object_pairs_hook=_unique_object)
    _require(isinstance(records, dict), "expected a timing extract")
    events = spec["events"]
    _require(isinstance(events, list) and 2 <= len(events) <= 64, "need 2 to 64 event references")
    scope = (run, capture["clock"], capture["log_sha256"])
    lines: list[int] = []
    timestamps: list[datetime] = []
    process: str | None = None
    for event in events:
        _require(isinstance(event, dict) and set(event) == {"run_source", "clock", "log_sha256", "key", "message"},
                 "invalid event locator")
        _require((event["run_source"], event["clock"], event["log_sha256"]) == scope,
                 "events must be from the same run or log and use the same clock")
        record = _lookup(records, event["key"])
        _require(type(record.get("line")) is int and record["line"] > 0 and
                 isinstance(record.get("text"), str), "invalid numbered log entry")
        parsed = LOG_ENTRY.fullmatch(record["text"])
        _require(parsed is not None and parsed[1] == record.get("utc"), "embedded log time differs")
        assert parsed is not None
        _require(parsed[3] == event["message"], "selected log message differs")
        _require(process is None or process == parsed[2], "different emitting process")
        process = parsed[2]
        stamp = datetime.strptime(parsed[1], "%Y-%m-%dT%H:%M:%S.%fZ")
        _require(not lines or (record["line"] > lines[-1] and stamp > timestamps[-1]),
                 "line numbers and timestamps must be strictly increasing")
        timestamps.append(stamp)
        lines.append(record["line"])
    intervals = [(b - a) // MILLISECOND for a, b in zip(timestamps, timestamps[1:])]
    result = {"run_source": run, "clock": capture["clock"], "log_sha256": capture["log_sha256"],
              "emitter_pid": int(process), "lines": lines, "intervals_ms": intervals}
    if opener:
        # Each locator's message was matched against its original numbered log record above.
        _require([e["key"] for e in events] == ["helper_still_running", "opener_success", "helper_exit0"],
                 "opener sequence needs running, success and exit records")
        _require(events[0]["message"] == "Browser helper open is still running, treating it as the browser"
                 and events[1]["message"] == "Browser opened automatically.", "unexpected opener messages")
        exit_match = re.fullmatch(r"Browser helper open exited \{ code: (-?[0-9]+) \}", events[2]["message"])
        _require(exit_match is not None, "missing helper exit code")
        result["opener_timing"] = {"running_to_success_ms": intervals[0],
                                   "success_to_exit_ms": intervals[1], "exit_code": int(exit_match[1])}
    return result
