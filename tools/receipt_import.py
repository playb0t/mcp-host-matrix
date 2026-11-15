#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Import reviewed public research projections without inventing observations."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
import sys
from reader_statements import FORMS, render_statement
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("matrix_portable_method",ROOT/"method/v1/portable.py")
assert spec and spec.loader
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
STATUSES=frozenset({"measured_with_limits","measured_negative_with_limits","measured_positive_with_limits","measured","not_measured","unknown"})
TOPICS=frozenset({"R01","R02","R03","R04","R05","R06"})
LEGACY={'cases': {'R01': 'cb0dee576c789d63727ec0db3323f162e09bb20278c3046ce4439f99e93b8797', 'R02': '19d3ba28a959c2aff8506c739da7c803058414799dd9872c3a83b2be269a65b1', 'R03': '5c514e2ec64ffc6072857785f3fabc9bee928f49aab71c0ad9239dbbcaf93086', 'R04': 'f3028c07d8a1dba027cb2de221318d41325eb5eeca9340bf77842e49b249d24a', 'R05': 'a774f30a1d628b880dc21c900a5983d18d9d04fdb28e82537dcd039845b8db2f', 'R06': '37432a386d042271ed2d49faaa747eec1fa93b8c83e324fbe9b0452a557c1515'}, 'receipts': {'disconnect/bench/receipts/R01.json': 'bd101439af7cbe3edbc808a00360f59fce6a04f40cbdf40a002c0e3a02af04af', 'matrix/receipts/R02.json': '88097f36938a85a451dc5def1843d5b6a6fe6a0044f85fb0291851603d2cfa4b', 'matrix/receipts/R03.json': 'a76dbe9acb825eb8366254368250188f2a761b6d8375f6f53fcfdb0716e119ae', 'matrix/receipts/R04.json': 'ded3df5fc6fd0e3ff98ed492d942d23f0fbc653c79b9e9037f965a55c9ae4615', 'matrix/receipts/R05.json': '3427537c25414641707d1e198af592e7be6aad91660662a10d573b4c4f907393', 'disconnect/bench/receipts/R06.json': 'cad71baae650c78d77d3043e7111e22089a5d1de1f33f89075e94128d6c73733'}}

LEGACY_SUBJECTS=[{'id': 'vscode', 'name': 'VS Code', 'kind': 'host'}, {'id': 'claude-code', 'name': 'Claude Code', 'kind': 'host'}, {'id': 'cursor', 'name': 'Cursor', 'kind': 'host'}, {'id': 'zed', 'name': 'Zed', 'kind': 'host'}, {'id': 'cascade', 'name': 'Cascade', 'kind': 'host'}, {'id': 'mcp-remote', 'name': 'mcp-remote', 'kind': 'bridge'}]

def require(ok: bool,message: str)->None:
    if not ok:raise ValueError("Matrix receipt: "+message)


def encode(value: Any)->bytes:
    return (json.dumps(value,indent=2,ensure_ascii=False)+"\n").encode("utf8")


def digest(value: Any)->str:return hashlib.sha256(P.canonical(value)).hexdigest()


def identifier(value: Any)->str:
    require(isinstance(value,str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,127}",value)is not None,"invalid identifier")
    return value


def subjects(value: Any)->dict[str,dict]:
    require(isinstance(value,list) and 1<=len(value)<=1000,"subjects catalog required")
    result={};names=set()
    for item in value:
        require(isinstance(item,dict) and set(item)=={"id","name","kind"},"subject schema differs")
        ident=identifier(item["id"])
        require(ident not in result and isinstance(item["name"],str) and item["name"].strip() and
                item["name"] not in names and item["kind"] in {"host","bridge","service","component"},"duplicate or invalid subject")
        result[ident]=item;names.add(item["name"])
    return result


def cells(value: Any)->dict[str,dict]:
    require(isinstance(value,list) and 1<=len(value)<=1000,"matrix_cells required")
    result={}
    for item in value:
        require(isinstance(item,dict) and set(item)=={"case_id","topic","status"},"matrix cell schema differs")
        ident=identifier(item["case_id"])
        require(ident not in result and ident not in LEGACY["cases"] and item["topic"] in TOPICS and item["status"] in STATUSES,"duplicate, legacy or invalid cell")
        result[ident]=item
    return result


def pointer(value: Any,name: str)->Any:
    require(isinstance(name,str) and (not name or name.startswith("/")),"invalid source pointer")
    if not name:return value
    for token in name[1:].split("/"):
        require(re.search(r"~(?![01])",token)is None,"invalid pointer escape")
        key=token.replace("~1","/").replace("~0","~")
        if isinstance(value,list):
            require(re.fullmatch(r"0|[1-9][0-9]*",key)is not None,"invalid array pointer")
            value=value[int(key)]
        else: value=value[key]
    return value


def check_sources(snapshot: Any,receipt: dict,artifacts: list[dict])->dict[str, Any]:
    public={a["sha256"]:a for a in artifacts};source_ids={};decoded={}
    sources=receipt.get("sources")
    require(isinstance(sources,list) and sources,"public sources required")
    for item in sources:
        require(isinstance(item,dict) and set(item)=={"id","sha256","format"},"source schema differs")
        ident=identifier(item["id"])
        require(ident not in source_ids and item["sha256"] in public,"source hash is not a direct public artifact")
        require(isinstance(item["format"],str) and item["format"].strip(),"source format missing")
        source_ids[ident]=item
        raw=snapshot.read(public[item["sha256"]]["logical_path"])
        require(hashlib.sha256(raw).hexdigest()==item["sha256"],"public source bytes differ")
        if item["format"].upper()=="JSON":decoded[ident]=P.load_json(raw)
    excerpts=receipt.get("excerpts");derived=receipt.get("derived_checks")
    require(isinstance(excerpts,list) and isinstance(derived,list),"declared excerpts and derived checks required")
    for item in excerpts:
        require(isinstance(item,dict) and set(item)<= {"source_id","source_pointer","fields","label"} and
                {"source_id","source_pointer","fields"}<=set(item),"excerpt schema differs")
        require(item["source_id"] in decoded and isinstance(item["fields"],dict),"excerpt needs a public JSON source")
        selected=pointer(decoded[item["source_id"]],item["source_pointer"])
        require(isinstance(selected,dict) and all(k in selected and P.canonical(selected[k])==P.canonical(v) for k,v in item["fields"].items()),"excerpt differs from public source")
    for item in derived:
        require(isinstance(item,dict) and set(item)=={"label","source_id","operation","source_pointers","result"},"derived check schema differs")
        require(item["source_id"] in decoded and item["operation"] in {"all equal","all distinct"} and
                isinstance(item["source_pointers"],list) and len(item["source_pointers"])>=2 and type(item["result"])is bool,"invalid derived check")
        values=[P.canonical(pointer(decoded[item["source_id"]],p))for p in item["source_pointers"]]
        actual=len(set(values))== (1 if item["operation"]=="all equal" else len(values))
        require(actual==item["result"],"derived check differs from public source")

    return decoded

def observation_index(record: Any, case: dict) -> dict[str, tuple[str, str, set[tuple[str, str]]]]:
    """Index complete event pairs once per source; never join different attempts."""
    require(isinstance(record, dict) and set(record) == {
        "schema", "case_id", "subject_id", "versions", "operation", "boundary",
        "observer", "channels", "attempts"
    } and record["schema"] == "matrix-observation/1", "observation schema differs")
    require(record["case_id"] == case["id"] and record["subject_id"] == case["subject_id"]
            and P.canonical(record["versions"]) == P.canonical(case["versions"]),
            "observation case, subject or versions differ")
    identifier(record["observer"])
    identifier(record["operation"])
    require(record["boundary"] in {"component", "backend", "native", "deployed"},
            "invalid observation boundary")
    channels = record["channels"]
    require(isinstance(channels, list) and 0 < len(channels) <= 1000, "observer channels required")
    monitored = {identifier(channel) for channel in channels}
    require(len(monitored) == len(channels), "duplicate observer channel")
    attempts = record["attempts"]
    require(isinstance(attempts, dict) and 0 < len(attempts) <= 1000, "observation attempts required")
    result = {}
    for name, attempt in attempts.items():
        identifier(name)
        require(isinstance(attempt, dict) and set(attempt) == {"role", "window", "events"},
                "attempt schema differs")
        role, window = attempt["role"], attempt["window"]
        require(role in {"observation", "control"} and window in {"complete", "interrupted"},
                "invalid attempt role or window")
        events = attempt["events"]
        require(isinstance(events, list), "attempt events required")
        pairs = set()
        for event in events:
            require(isinstance(event, list) and len(event) == 2 and event[0] in monitored,
                    "event outside recorder channels")
            pairs.add((event[0], identifier(event[1])))
        result[name] = (role, window, pairs)
    return result


def supported_claims(case: dict, claims: list, decoded: dict) -> list[str]:
    """Return checked event statements within their own observation attempts."""
    require(isinstance(claims, list) and 0 < len(claims) <= 1000, "observation claims required")
    indexes = {}
    rendered = []
    for claim in claims:
        require(isinstance(claim, dict) and set(claim) == {
            "source_id", "attempt", "control", "channel", "object", "predicate"
        }, "observation claim schema differs")
        source = identifier(claim["source_id"])
        require(source in decoded and isinstance(decoded[source], dict), "claim needs a public JSON source")
        record = decoded[source].get("observation")
        if source not in indexes:
            indexes[source] = observation_index(record, case)
        attempts = indexes[source]
        run_id, control_id = identifier(claim["attempt"]), identifier(claim["control"])
        require(run_id in attempts and attempts[run_id][0] == "observation", "claim target attempt missing")
        require(control_id in attempts and attempts[control_id][:2] == ("control", "complete"),
                "claim needs a separate completed control")
        channel, obj = identifier(claim["channel"]), identifier(claim["object"])
        require(any(c == channel for c, _ in attempts[control_id][2]), "control did not observe channel")
        _, window, events = attempts[run_id]
        predicate = claim["predicate"]
        if predicate == "absent":
            require(window == "complete", "absence claim has an incomplete window")
            require((channel, obj) not in events, "event observed in claimed absence window")
        else:
            require(predicate == "present", "invalid claim predicate")
            require((channel, obj) in events, "claimed event not observed")
        rendered.append(f"{record['operation']} [{source}, {record['boundary']}, {record['observer']}, "
                        f"{run_id}, control {control_id}]: {channel}({obj}) {predicate}.")
    return rendered


def check_claims(case: dict, receipt: dict, decoded: dict) -> None:
    if "claims" in receipt:
        rendered = supported_claims(case, receipt["claims"], decoded)
        require(rendered == case.get("observations"), "observation text differs from supported claims")



HISTORICAL_GROUNDS = {
    "R01": ("window_cohort", {
        "disconnect/bench/receipts/R01.json": LEGACY["receipts"]["disconnect/bench/receipts/R01.json"],
        "disconnect/bench/RESULTS.json": "2920343f43543e374d990faf9c4159aff73ce0d0a0a879b2a1466ccdf739f701",
    }),
    "R04": ("event_order", {
        "matrix/receipts/R04.json": LEGACY["receipts"]["matrix/receipts/R04.json"],
        # Bind the reviewed run-to-stream mapping as well as the embedded original bytes.
        "grounds/r04-timing.json": "399a1107f675b2dc9c49bed695dc760c0a6451d5f63c3085550d7cc75e823d55",
    }),
}


def evaluate_ground(snapshot: Any, ground: dict, case: dict,
                    allowed: dict[str, str]) -> dict:
    form = FORMS.get(case["id"])
    statement_field = "statement_form" if form else "statement"
    require(isinstance(ground, dict) and set(ground) == {
        "schema", "case_id", "kind", statement_field, "parameters", "sources", "expected"
    } and ground["schema"] == "matrix-ground/1", "invalid ground statement or schema")
    require(ground["case_id"] == case["id"], "ground case differs")
    if ground["kind"] in {"window_cohort", "event_order"}:
        require(form is not None, "no registered statement form for this ground and case")
    if form:
        require((ground["kind"], ground["statement_form"]) == form, "invalid historical statement form")
    else:
        require(isinstance(ground["statement"], str) and bool(ground["statement"].strip()), "statement required")
    refs = ground["sources"]
    require(isinstance(refs, list) and 0 < len(refs) <= 32, "ground sources required")
    decoded = {}
    paths = set()
    for ref in refs:
        require(isinstance(ref, dict) and set(ref) == {"id", "path", "sha256"}, "invalid ground source")
        name = P.logical_path(ref["path"])
        key = identifier(ref["id"])
        require(name in allowed and name not in paths and key not in decoded, "unknown or duplicate ground source")
        raw = snapshot.read(name)
        actual = hashlib.sha256(raw).hexdigest()
        require(actual == ref["sha256"] and allowed[name] == actual, "ground source fingerprint differs")
        paths.add(name)
        decoded[key] = P.load_json(raw)
    params = ground["parameters"]
    require(isinstance(params, dict), "invalid ground parameters")
    kind = ground["kind"]
    if kind in {"window_cohort", "event_order"}:
        source_receipt = decoded.get(identifier(params.get("receipt")))
        require(isinstance(source_receipt, dict) and source_receipt.get("case_id") == case["id"],
                "ground evidence belongs to another case")
        if "subject_id" in case:
            require(source_receipt.get("subject_id") == case["subject_id"] and
                    P.canonical(source_receipt.get("versions")) == P.canonical(case["versions"]),
                    "ground evidence subject or versions differ")
    if kind == "atomic_events":
        require(set(params) == {"claims"}, "invalid atomic ground parameters")
        computed = {"events": supported_claims(case, params["claims"], decoded)}
    elif kind == "window_cohort":
        from cohort_ground import evaluate
        computed = evaluate(params, decoded)
    elif kind == "event_order":
        if form:
            require(params.get("sequence_form") == form[1], "named event sequence required by statement form")
        from order_ground import evaluate
        computed = evaluate(params, decoded)
    else:
        raise ValueError("Unknown ground kind")
    require(P.canonical(computed) == P.canonical(ground["expected"]), "computed ground differs from expected")
    return {"case_id": case["id"], "kind": kind, "statement": render_statement(case["id"], computed) if form else ground["statement"], "computed": computed}


def historical_ground(snapshot: Any, case_id: str) -> dict:
    kind, allowed = HISTORICAL_GROUNDS[case_id]
    ground = P.load_json(snapshot.read(f"grounds/{case_id}.json"))
    require(ground.get("kind") == kind, "historical ground kind differs")
    result = evaluate_ground(snapshot, ground, {"id": case_id}, allowed)
    require({ref["path"] for ref in ground["sources"]} == set(allowed), "historical ground inputs differ")
    return result


def check_linked_grounds(snapshot: Any, case: dict, receipt: dict, artifacts: list[dict]) -> None:
    if "grounds" not in receipt:
        return
    links = receipt["grounds"]
    require(isinstance(links, list) and 0 < len(links) <= 100, "invalid observation ground links")
    allowed = {a["logical_path"]: a["sha256"] for a in artifacts}
    seen = set()
    statements = case.get("observations")
    require(isinstance(statements, list), "observations required")
    for link in links:
        require(isinstance(link, dict) and set(link) == {"logical_path", "sha256", "observation_index"},
                "invalid observation ground link")
        index = link["observation_index"]
        require(type(index) is int and 0 <= index < len(statements), "invalid observation index")
        path = P.logical_path(link["logical_path"])
        require(path not in seen and path in allowed and allowed[path] == link["sha256"],
                "ground must be a distinct direct public artifact")
        seen.add(path)
        raw = snapshot.read(path)
        require(hashlib.sha256(raw).hexdigest() == link["sha256"], "ground artifact fingerprint differs")
        ground = P.load_json(raw)
        checked = evaluate_ground(snapshot, ground, case, allowed)
        require(checked["statement"] == statements[index], "ground statement differs from linked observation")


def projection(snapshot: Any,ref: dict)->dict:
    graph=P.verify_receipt(snapshot,ref);work=graph["receipt"];card=graph["card"]
    require(work["profile"]=="research" and work["variant"] in (None,"mcp"),"matrix needs a research receipt")
    options=card["contract"]["options"];declared=cells(options.get("matrix_cells"))
    require(not any(c["status"].startswith("measured")for c in declared.values()) or options["mode"]=="experimental","source-only work cannot claim a measured cell")
    name=options.get("matrix_projection","matrix-projection.json");P.logical_path(name)
    candidates=[a for a in work["artifacts"] if a["logical_path"]==name]
    require(len(candidates)==1,"projection must be one direct public research artifact")
    value=P.load_json(snapshot.read(name))
    require(set(value)=={"schema","matrix_cells","subjects","cases","receipts"} and value["schema"]=="mcp-matrix-projection/1","projection schema differs")
    require(P.canonical(value["matrix_cells"])==P.canonical(options["matrix_cells"]),"projection cells differ from admitted contract")
    catalog=subjects(value["subjects"])
    require(isinstance(value["cases"],list) and isinstance(value["receipts"],list),"projection lists required")
    by_case={};by_receipt={}
    for case in value["cases"]:
        require(isinstance(case,dict),"case object required");ident=identifier(case.get("id"))
        require(ident not in by_case and ident in declared,"unplanned or duplicate case")
        require(case.get("topic")==declared[ident]["topic"] and case.get("status")==declared[ident]["status"] and case.get("subject_id") in catalog,"case topic/status/subject differs")
        require("receipt"not in case and "public_artifacts"not in case,"projection must not supply generated receipt links")
        by_case[ident]=case
    for receipt in value["receipts"]:
        require(isinstance(receipt,dict) and set(receipt)-{"claims", "grounds"}=={"case_id","kind","versions","sources","excerpts","derived_checks","limits"},"projection receipt schema differs")
        ident=receipt["case_id"];require(ident not in by_receipt and ident in declared,"unplanned or duplicate projection receipt")
        require(P.canonical(receipt["versions"])==P.canonical(by_case[ident].get("versions")),"receipt and case versions differ")
        decoded = check_sources(snapshot,receipt,work["artifacts"])
        check_claims(by_case[ident], receipt, decoded)
        check_linked_grounds(snapshot, by_case[ident], receipt, work["artifacts"])
        require(isinstance(by_case[ident].get("evidence_ids"),list) and
                set(by_case[ident]["evidence_ids"])=={item["id"]for item in receipt["sources"]},
                "case evidence IDs differ from its public source IDs")
        by_receipt[ident]=receipt
    require(set(by_case)==set(by_receipt)==set(declared),"projection does not cover admitted cells exactly")
    return {"graph":graph,"projection":value,"subjects":catalog,"cases":by_case,"receipts":by_receipt}


def material(snapshot: Any,ref: dict,case_id: str)->dict:
    result=projection(snapshot,ref);require(case_id in result["cases"],"requested case not declared")
    work=result["graph"]["receipt"];card=result["graph"]["card"]
    body=copy.deepcopy(result["receipts"][case_id])
    body={"schema":"mcp-host-matrix-receipt/2",**body,"provenance":{
        "work_receipt_ref":dict(ref),"work_receipt_sha256":ref["sha256"],"profile":work["profile"],
        "variant":work["variant"],"contract_sha256":digest(card["contract"])}}
    index={"schema":"mcp-matrix-public-artifacts/1","work_receipt_ref":dict(ref),
           "artifacts":copy.deepcopy(work["artifacts"]),"withheld":copy.deepcopy(work["withheld"])}
    case=copy.deepcopy(result["cases"][case_id]);case["receipt"]="matrix/receipts/"+case_id+".json"
    case["public_artifacts"]="matrix/receipts/"+case_id+".public-artifacts.json"
    return {"case":case,"receipt":body,"index":index,"subjects":result["subjects"],"graph":result["graph"]}


def validate_matrix(root: Path,data: dict,*,manifested: bool=True)->dict[str,int]:
    catalog=subjects(data.get("subjects"));legacy=0;bound=0
    require(data["subjects"][:len(LEGACY_SUBJECTS)]==LEGACY_SUBJECTS,"legacy subject catalog changed")
    require(data.get("snapshot_date")=="2026-10-25","legacy snapshot date changed")
    for name,pin in LEGACY["receipts"].items():
        path=root/name;P._unlinked(path)
        require(hashlib.sha256(path.read_bytes()).hexdigest()==pin,"legacy receipt bytes changed")
    existing={c["id"]:c for c in data["cases"]}
    require(len(existing)==len(data["cases"]),"duplicate matrix case")
    require(set(LEGACY["cases"])<=set(existing),"legacy case removed")
    snapshot=P.Snapshot(root) if manifested else None
    for ident,case in existing.items():
        if ident in LEGACY["cases"]:
            require(digest(case)==LEGACY["cases"][ident],"legacy case content changed")
            legacy+=1;continue
        identifier(ident);require(case.get("subject_id") in catalog,"unknown subject_id")
        require(case.get("topic") in TOPICS and case.get("status") in STATUSES,"invalid direction or status")
        require(case.get("receipt")=="matrix/receipts/"+ident+".json" and
                case.get("public_artifacts")=="matrix/receipts/"+ident+".public-artifacts.json","new cell needs canonical receipt links")
        if not manifested:continue
        assert snapshot is not None
        receipt=P.load_json(snapshot.read(case["receipt"]));index=P.load_json(snapshot.read(case["public_artifacts"]))
        provenance=receipt.get("provenance");require(isinstance(provenance,dict),"new cell provenance required")
        ref=provenance.get("work_receipt_ref");expected=material(snapshot,ref,ident)
        check_sources(snapshot,receipt,expected["graph"]["receipt"]["artifacts"])
        require(P.canonical(receipt)==P.canonical(expected["receipt"]),"matrix receipt differs from reviewed projection")
        require(P.canonical(index)==P.canonical(expected["index"]),"public artifact index differs from bound work receipt")
        require(P.canonical(case)==P.canonical(expected["case"]),"matrix cell differs from reviewed projection")
        for sid,subject in expected["subjects"].items():require(P.canonical(catalog.get(sid))==P.canonical(subject),"subject metadata differs from research")
        bound+=1
    return {"legacy_cases":legacy,"receipt_bound_cases":bound,"subjects":len(catalog)}


def _output_path(source: Path, output: Path) -> Path:
    """Require a fresh canonical destination; never reuse a directory."""
    require(output.is_absolute(), "output must be an absolute new directory")
    require(not str(output).startswith(("\\\\", "//")), "network output is not accepted")
    P.logical_path(output.name)
    P._unlinked(output.parent)
    require(str(output.resolve()) == str(output), "output path must be canonical, without aliases")
    require(not output.is_relative_to(source) and not source.is_relative_to(output),
            "output must be outside the source root")
    require(not output.exists() and not output.is_symlink(), "output already exists; preserved")
    return output


def _create_file(root: Path, name: str, content: bytes) -> None:
    """Create one file exclusively inside the newly owned candidate directory."""
    target = root.joinpath(*P.logical_path(name).split("/"))
    parent = root
    P._unlinked(parent)
    for part in target.relative_to(root).parts[:-1]:
        parent = parent / part
        try:
            parent.mkdir()
        except FileExistsError:
            pass
        P._unlinked(parent)
        require(parent.is_dir(), "candidate parent is not a directory")
    with target.open("xb") as stream:
        stream.write(content)


def _check_inventory(output: Path, files: dict[str, bytes]) -> None:
    """Reject unplanned files, directories and links observed in the candidate."""
    expected_files = set(files)
    expected_dirs: set[str] = set()
    for name in files:
        for parent in Path(name).parents:
            if parent != Path("."):
                expected_dirs.add(parent.as_posix())
    actual_files: set[str] = set()
    actual_dirs: set[str] = set()
    P._unlinked(output)
    for path in output.rglob("*"):
        P._unlinked(path)
        name = path.relative_to(output).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISREG(mode):
            actual_files.add(name)
        elif stat.S_ISDIR(mode):
            actual_dirs.add(name)
        else:
            require(False, "unexpected candidate entry type")
    require(actual_files == expected_files and actual_dirs == expected_dirs,
            "candidate inventory differs from selected files and required directories")


def _stage_new(output: Path, files: dict[str, bytes]) -> None:
    # mkdir and every file create are exclusive. No existing path is replaced,
    # restored or deleted, including when a noncooperating editor writes here.
    output.mkdir()
    try:
        for name, content in files.items():
            _create_file(output, name, content)
        for name, content in files.items():
            target = output.joinpath(*name.split("/"))
            P._unlinked(target)
            require(target.read_bytes() == content, "candidate changed while staging")
        _check_inventory(output, files)
    except BaseException as exc:
        # Retain the entire incomplete directory: cleanup could erase a late
        # foreign edit. Reuse is forbidden; inspect it and choose a fresh output.
        raise OSError(f"incomplete output retained at {output}: {exc}") from exc


def apply(root: Path,ref: dict,case_id: str,*,output: Path,commit: str|None=None)->dict:
    snapshot=P.Snapshot(root,commit);root=snapshot.root
    output=_output_path(root,Path(output));result=material(snapshot,ref,case_id)
    data=P.load_json(snapshot.read("matrix/RESULTS.json"));catalog=subjects(data["subjects"])
    for ident,subject in result["subjects"].items():
        require(ident not in catalog or P.canonical(catalog[ident])==P.canonical(subject),"subject ID collision")
        if ident not in catalog:data["subjects"].append(subject)
    found=next((c for c in data["cases"]if c["id"]==case_id),None)
    require(found is None or P.canonical(found)==P.canonical(result["case"]),"existing different matrix case preserved")
    if found is None:data["cases"].append(result["case"])
    from render_matrix import replace_section
    page=snapshot.read("matrix/MATRIX.en.md").decode("utf8")
    updates={result["case"]["receipt"]:encode(result["receipt"]),result["case"]["public_artifacts"]:encode(result["index"]),
        "matrix/RESULTS.json":encode(data),"matrix/MATRIX.en.md":replace_section(page,data).encode("utf8")}
    source_file="figures/SOURCES.json"
    source_bytes=snapshot.read(source_file);fingerprints=P.load_json(source_bytes)
    rows=[row for row in fingerprints["inputs"] if row.get("repository_file")=="matrix/RESULTS.json"]
    require(len(rows)==1,"expected one structured-results figure source fingerprint")
    rows[0]["sha256"]=hashlib.sha256(updates["matrix/RESULTS.json"]).hexdigest()
    updates[source_file]=encode(fingerprints)
    # Materialize only the selected manifest, never arbitrary worktree files.
    # All source reads finish before creating the output. Later source edits
    # remain untouched; the candidate represents these verified selected bytes.
    files: dict[str, bytes] = {}
    total = 0
    for name in snapshot.manifest:
        raw = snapshot.read(name)
        total += len(raw)
        require(total <= 256 * 1024 * 1024, "selected snapshot exceeds staging size limit")
        files[name] = raw
    for name, raw in updates.items():
        if name not in ("matrix/RESULTS.json", "matrix/MATRIX.en.md", source_file):
            require(name not in files or files[name] == raw, "existing different receipt preserved")
        files[name] = raw
    manifest = snapshot._raw("MANIFEST.sha256", P.MAX_JSON)
    require(hashlib.sha256(manifest).hexdigest() == snapshot.manifest_sha256,
            "selected manifest changed before staging")
    files["MANIFEST.sha256"] = manifest
    snapshot.assert_anchor()
    _stage_new(output, files)
    return {"status":"prepared_requires_repository_validation","state":snapshot.state,
            "case_id":case_id,"source_root":str(root),"output":str(output),
            "commit":commit,"files":list(updates)}


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--ground", choices=sorted(HISTORICAL_GROUNDS), help="verify a historical evidence ground")
    parser.add_argument("--receipt");parser.add_argument("--sha256")
    parser.add_argument("--case");parser.add_argument("--commit");parser.add_argument("--apply",action="store_true")
    parser.add_argument("--output",type=Path,help="absolute, absent candidate directory outside --root")
    args=parser.parse_args()
    if args.ground:
        if any((args.receipt, args.sha256, args.case, args.apply, args.output)):
            parser.error("--ground is read-only and cannot be combined with receipt import")
    elif not all((args.receipt, args.sha256, args.case)):
        parser.error("--receipt, --sha256 and --case are required for import")
    if args.apply and args.output is None:parser.error("--apply requires --output")
    if args.output is not None and not args.apply:parser.error("--output requires --apply")
    try:
        ref={"logical_path":args.receipt,"sha256":args.sha256};snapshot=P.Snapshot(args.root,args.commit)
        if args.ground:
            result = historical_ground(snapshot, args.ground)
            snapshot.assert_anchor()
            print(json.dumps(result, ensure_ascii=True))
            return 0
        result=apply(args.root,ref,args.case,output=args.output,commit=args.commit)if args.apply else material(snapshot,ref,args.case)
        print(json.dumps(result if args.apply else {"status":"PASS","state":snapshot.state,"case_id":result["case"]["id"]}))
        return 0
    except (ValueError,OSError,KeyError,TypeError,IndexError)as exc:
        print(json.dumps({"status":"FAIL","reason":str(exc)}));return 1

if __name__=="__main__":raise SystemExit(main())
