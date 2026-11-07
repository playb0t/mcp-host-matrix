#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render only the matrix coverage table from structured outcomes."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
START="<!-- matrix-coverage:start -->"
END="<!-- matrix-coverage:end -->"

def escaped(value: str)->str:
    return value.replace("\n"," ").replace("|","\\|").replace("<","&lt;").replace(">","&gt;")

def section(data: dict)->str:
    subjects=data["subjects"]
    lines=["| Direction | "+" | ".join(escaped(s["name"])for s in subjects)+" |","|"+"---|"*(len(subjects)+1)]
    for case in data["cases"]:
        legacy=case["id"] in {"R01","R02","R03","R04","R05","R06"}
        known=set(case.get("native_hosts",[])+case.get("components",[])) if legacy else set()
        values=[]
        for subject in subjects:
            selected=subject["name"] in known if legacy else case.get("subject_id")==subject["id"]
            values.append("M" if selected and case["status"].startswith("measured") else
                          "Unknown" if selected and case["status"]=="unknown" else "Not measured")
        lines.append("| "+escaped(case["id"]+" "+case.get("title",case["topic"]))+" | "+" | ".join(values)+" |")
    return "\n".join([START,*lines,END])

def replace_section(text: str,data: dict)->str:
    if START in text or END in text:
        if text.count(START)!=1 or text.count(END)!=1 or text.index(START)>text.index(END):raise ValueError("Invalid coverage markers")
        a=text.index(START);b=text.index(END)+len(END)
    else:
        a=text.index("| Direction |");b=text.index("\n\n",a)
    return text[:a]+section(data)+text[b:]

def check(root: Path,data: dict)->None:
    text=(root/"matrix/MATRIX.en.md").read_text(encoding="utf8")
    if START not in text or replace_section(text,data)!=text:raise ValueError("Coverage table differs from RESULTS.json")

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument("--check",action="store_true");args=parser.parse_args()
    try:
        data=json.loads((args.root/"matrix/RESULTS.json").read_text(encoding="utf8"))
        if args.check:check(args.root,data)
        else:
            path=args.root/"matrix/MATRIX.en.md";path.write_text(replace_section(path.read_text(encoding="utf8"),data),encoding="utf8",newline="\n")
        return 0
    except (ValueError,KeyError,OSError)as exc:print(str(exc));return 1
if __name__=="__main__":raise SystemExit(main())
