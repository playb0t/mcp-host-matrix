"""Execute isolated positive/negative full-validator controls, retaining raw outputs."""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path
from test_matrix_receipts import Fixture

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    f=Fixture()
    try:
        argv=[sys.executable,"-B",str(f.root/"tools/receipt_import.py"),"--root",str(f.root),
              "--receipt",f.receipt_name,"--sha256",f.ref(f.receipt_name)["sha256"],"--case",f.case_id,"--apply"]
        imported=subprocess.run(argv,capture_output=True,timeout=60)
        import_result={"argv":argv,"exit_code":imported.returncode,"stdout":imported.stdout.decode("utf8"),"stderr":imported.stderr.decode("utf8")}
        if imported.returncode:raise ValueError("Synthetic CLI import failed: "+import_result["stdout"]+import_result["stderr"])
        f.index();positive=f.cli()
        name="matrix/receipts/"+f.case_id+".json";receipt=f.read(name);receipt["sources"][0]["sha256"]="0"*64;f.write(name,receipt);f.index()
        negative=f.cli()
        result={"schema":"matrix-receipt-controls/1","synthetic":True,"import":import_result,"positive":positive,"negative":negative,
                "negative_manifest_regenerated":True,"legacy_cases":6,"fixture_case":f.case_id,
                "accepted":positive["exit_code"]==0 and negative["exit_code"]!=0 and "source hash"in negative["stdout"]+negative["stderr"]}
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8",newline="\n")
        print(json.dumps({"positive_exit":positive["exit_code"],"negative_exit":negative["exit_code"],"accepted":result["accepted"]}))
        return 0 if result["accepted"]else 1
    finally:f.cleanup()
if __name__=="__main__":raise SystemExit(main())
