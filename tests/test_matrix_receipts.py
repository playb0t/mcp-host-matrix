from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from uuid import uuid4
from unittest.mock import patch

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/"tools"))
import receipt_import as I
import render_matrix as R
import validate as V
STATE=REPO.parent/".matrix-tests"


class Fixture:
    def __init__(self)->None:
        STATE.mkdir(exist_ok=True);self.root=STATE/uuid4().hex
        self.source_root=self.root;self.outputs: list[Path]=[]
        shutil.copytree(REPO,self.root,ignore=shutil.ignore_patterns(".git","__pycache__"))
        self.case_id="SYN-R01";self.receipt_name="work/fixture/receipt.json"
        self.source_name="work/fixture/source.json";self.projection_name="work/fixture/matrix-projection.json"
        self.write(self.source_name,{"synthetic":True,"observed":True,"before":1,"after":1})
        cell={"case_id":self.case_id,"topic":"R01","status":"measured_with_limits"}
        case={"id":self.case_id,"topic":"R01","status":"measured_with_limits","subject_id":"fixture-service",
              "versions":{"fixture":"1.0.0"},"native_hosts":[],"components":[],
              "observations":["Synthetic fixture observation for integrity controls."],
              "controls":["Synthetic positive and negative receipt controls."],
              "limits":["Synthetic data only; no product measurement or external publication."],
              "evidence_ids":["fixture.source"]}
        receipt={"case_id":self.case_id,"kind":"Synthetic reviewed projection","versions":case["versions"],
                 "sources":[{"id":"fixture.source","sha256":self.ref(self.source_name)["sha256"],"format":"JSON"}],
                 "excerpts":[{"source_id":"fixture.source","source_pointer":"","fields":{"observed":True}}],
                 "derived_checks":[{"label":"Synthetic unchanged value","source_id":"fixture.source",
                     "operation":"all equal","source_pointers":["/before","/after"],"result":True}],
                 "limits":case["limits"]}
        self.write(self.projection_name,{"schema":"mcp-matrix-projection/1","matrix_cells":[cell],
            "subjects":[{"id":"fixture-service","name":"Synthetic service","kind":"service"}],
            "cases":[case],"receipts":[receipt]})
        card=self.read("method/examples/cards/research.json")
        card["case_id"]="synthetic-matrix-research";card["contract"]["options"]={"mode":"experimental","matrix_cells":[cell],"matrix_projection":self.projection_name}
        card["contract"]["inputs"]=[self.ref(self.source_name)];card["contract"]["exclusions"]={}
        card["contract"]["plans"].append({"id":"controls","purpose":"controls","kind":"command"})
        checks=[]
        for plan in card["contract"]["plans"]:
            check={"id":plan["id"],"kind":plan["kind"],"state":"passed","reason":"Synthetic recorded control result only.","evidence_refs":[self.ref(self.source_name)]}
            if plan["purpose"]=="conclusion":check["verdict"]="supported"
            checks.append(check)
        card["checks"]=checks;self.write("work/fixture/card.json",card)
        artifacts=[]
        for name in (self.source_name,self.projection_name):
            artifacts.append({**self.ref(name),"size":(self.root/name).stat().st_size,"visibility":"public"})
        self.write(self.receipt_name,{"schema":"work-method-receipt/1","case_id":card["case_id"],
            "profile":"research","variant":None,"method_ref":card["method_ref"],"contract_ref":self.ref("work/fixture/card.json"),
            "artifacts":artifacts,"parents":[],"outcome":"assessed","withheld":{"internal_artifacts":2,"private_artifacts":1}})
        self.index()

    def cleanup(self)->None:
        for root in [self.source_root, *self.outputs]:
            assert root.resolve().is_relative_to(STATE.resolve()) and root!=STATE
            if root.exists():
                def retry(function, name, info):
                    path=Path(name)
                    assert path.resolve().is_relative_to(root.resolve())
                    if not isinstance(info[1],PermissionError):raise info[1]
                    path.chmod(0o700);function(name)
                shutil.rmtree(root,onerror=retry)

    def read(self,name: str)->dict:return json.loads((self.root/name).read_text(encoding="utf8"))
    def write(self,name: str,value: object)->None:
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
        if isinstance(value,bytes):p.write_bytes(value)
        else:p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf8",newline="\n")
    def ref(self,name: str)->dict:return {"logical_path":name,"sha256":hashlib.sha256((self.root/name).read_bytes()).hexdigest()}
    def index(self)->None:V.write_manifest(self.root)
    def graph(self)->dict:return I.P.verify_receipt(I.P.Snapshot(self.root),self.ref(self.receipt_name))
    def output(self)->Path:
        target=STATE/(uuid4().hex+"-candidate");self.outputs.append(target);return target
    def apply(self)->dict:
        target=self.output()
        result=I.apply(self.root,self.ref(self.receipt_name),self.case_id,output=target)
        self.root=target;self.index();return result
    def validate(self)->dict:return V.validate(self.root)
    def cli(self,*args: str)->dict:
        argv=[sys.executable,"-B",str(self.root/"tools/validate.py"),"--root",str(self.root),*args]
        q=subprocess.run(argv,capture_output=True,timeout=60)
        return {"argv":argv,"exit_code":q.returncode,"stdout":q.stdout.decode("utf8"),"stderr":q.stderr.decode("utf8")}
    def rebind_card(self,change)->None:
        card=self.read("work/fixture/card.json");change(card);self.write("work/fixture/card.json",card)
        receipt=self.read(self.receipt_name);receipt["contract_ref"]=self.ref("work/fixture/card.json");self.write(self.receipt_name,receipt);self.index()


class MatrixReceiptTests(unittest.TestCase):
    def setUp(self)->None:self.f=Fixture();self.addCleanup(self.f.cleanup)
    def test_new_service_import_passes_full_validator(self)->None:
        f=self.f;f.apply();result=f.validate()
        self.assertEqual(result["legacy_cases"],6);self.assertEqual(result["receipt_bound_cases"],1)
        self.assertEqual(result["subjects"],7)
        imported=f.read("matrix/receipts/"+f.case_id+".json")
        self.assertEqual(imported["provenance"]["work_receipt_sha256"],f.ref(f.receipt_name)["sha256"])
        self.assertEqual(imported["excerpts"],f.read(f.projection_name)["receipts"][0]["excerpts"])
    def test_source_hash_substitution_fails_after_new_manifest(self)->None:
        f=self.f;f.apply();name="matrix/receipts/"+f.case_id+".json";v=f.read(name);v["sources"][0]["sha256"]="0"*64;f.write(name,v);f.index()
        with self.assertRaisesRegex(ValueError,"source hash"):f.validate()
    def test_source_bytes_mutation_fails_after_new_manifest(self)->None:
        f=self.f;f.apply();f.write(f.source_name,{"synthetic":True,"observed":False});f.index()
        with self.assertRaises(ValueError):f.validate()
    def test_index_cannot_be_substituted_as_authority(self)->None:
        f=self.f;f.apply();n="matrix/receipts/"+f.case_id+".public-artifacts.json";v=f.read(n);v["artifacts"][0]["sha256"]="0"*64;f.write(n,v);f.index()
        with self.assertRaisesRegex(ValueError,"artifact index"):f.validate()
    def test_case_identity_or_subject_cannot_change(self)->None:
        f=self.f;f.apply();data=f.read("matrix/RESULTS.json");data["cases"][-1]["subject_id"]="unknown";f.write("matrix/RESULTS.json",data);f.index()
        with self.assertRaisesRegex(ValueError,"subject_id"):I.validate_matrix(f.root,data)
    def test_legacy_subjects_cannot_be_relabelled(self)->None:
        f=self.f;data=f.read("matrix/RESULTS.json");data["subjects"][0]["name"]="Another service"
        with self.assertRaisesRegex(ValueError,"legacy subject"):I.validate_matrix(f.root,data,manifested=False)

    def test_unknown_cell_retains_unknown_coverage_mark(self)->None:
        f=self.f;f.rebind_card(lambda c:c["contract"]["options"]["matrix_cells"][0].update(status="unknown"))
        projection=f.read(f.projection_name);projection["matrix_cells"][0]["status"]="unknown";projection["cases"][0]["status"]="unknown";f.write(f.projection_name,projection)
        work=f.read(f.receipt_name);next(a for a in work["artifacts"]if a["logical_path"]==f.projection_name).update(sha256=f.ref(f.projection_name)["sha256"],size=(f.root/f.projection_name).stat().st_size);f.write(f.receipt_name,work);f.index()
        f.apply();self.assertEqual(f.validate()["receipt_bound_cases"],1)
        row=next(line for line in (f.root/"matrix/MATRIX.en.md").read_text().splitlines()if line.startswith("| SYN-R01"))
        self.assertTrue(row.endswith("| Unknown |"))

    def test_context_client_does_not_promote_extra_measured_subject(self)->None:
        f=self.f;projection=f.read(f.projection_name)
        projection["cases"][0]["native_hosts"]=["VS Code"]
        projection["cases"][0]["components"]=["mcp-remote"]
        f.write(f.projection_name,projection);work=f.read(f.receipt_name)
        next(a for a in work["artifacts"]if a["logical_path"]==f.projection_name).update(sha256=f.ref(f.projection_name)["sha256"],size=(f.root/f.projection_name).stat().st_size)
        f.write(f.receipt_name,work);f.index();f.apply();f.validate()
        row=next(line for line in (f.root/"matrix/MATRIX.en.md").read_text().splitlines()if line.startswith("| SYN-R01"))
        self.assertEqual(row.count("| M "),1)
        self.assertTrue(row.endswith("| M |"))
        self.assertEqual(row.split("|")[2].strip(),"Not measured")

    def test_missing_matrix_cells_prevents_import(self)->None:
        f=self.f;f.rebind_card(lambda c:c["contract"]["options"].pop("matrix_cells"))
        with self.assertRaisesRegex(ValueError,"matrix_cells"):I.material(I.P.Snapshot(f.root),f.ref(f.receipt_name),f.case_id)
    def test_source_only_cannot_claim_measured(self)->None:
        f=self.f;f.rebind_card(lambda c:c["contract"]["options"].update(mode="source"))
        with self.assertRaisesRegex(ValueError,"source-only"):I.material(I.P.Snapshot(f.root),f.ref(f.receipt_name),f.case_id)
    def test_projection_options_mismatch_is_rejected(self)->None:
        f=self.f;f.rebind_card(lambda c:c["contract"]["options"]["matrix_cells"][0].update(status="measured"))
        with self.assertRaisesRegex(ValueError,"projection cells"):I.material(I.P.Snapshot(f.root),f.ref(f.receipt_name),f.case_id)
    def test_projection_is_not_invented_from_work_receipt(self)->None:
        f=self.f;n=f.receipt_name;v=f.read(n);v["artifacts"]=[a for a in v["artifacts"]if a["logical_path"]!=f.projection_name];f.write(n,v);f.index()
        with self.assertRaisesRegex(ValueError,"projection must"):I.material(I.P.Snapshot(f.root),f.ref(n),f.case_id)
    def test_legacy_case_and_receipt_mutation_rejected(self)->None:
        f=self.f;data=f.read("matrix/RESULTS.json");data["cases"][0]["observations"].append("Changed legacy claim.")
        with self.assertRaisesRegex(ValueError,"legacy case"):I.validate_matrix(f.root,data,manifested=False)
        name=next(iter(I.LEGACY["receipts"]));f.write(name,b'{}\n')
        with self.assertRaisesRegex(ValueError,"legacy receipt"):I.validate_matrix(f.root,f.read("matrix/RESULTS.json"),manifested=False)
    def test_measured_case_without_receipt_link_rejected(self)->None:
        f=self.f;f.apply();data=f.read("matrix/RESULTS.json");data["cases"][-1].pop("receipt")
        with self.assertRaisesRegex(ValueError,"receipt links"):I.validate_matrix(f.root,data)
    def test_unmanifested_receipt_is_not_accepted(self)->None:
        f=self.f;f.apply();p=f.root/"MANIFEST.sha256";p.write_text("\n".join(s for s in p.read_text().splitlines()if not s.endswith("matrix/receipts/"+f.case_id+".json"))+"\n",encoding="utf8",newline="\n")
        with self.assertRaisesRegex(ValueError,"manifest"):f.validate()
    def test_wrong_method_pin_is_rejected(self)->None:
        f=self.f;f.rebind_card(lambda c:c["method_ref"].update(sha256="0"*64))
        with self.assertRaises(ValueError):I.material(I.P.Snapshot(f.root),f.ref(f.receipt_name),f.case_id)
    def test_changed_excerpt_is_not_a_new_observation(self)->None:
        f=self.f;v=f.read(f.projection_name);v["receipts"][0]["excerpts"][0]["fields"]["observed"]=False;f.write(f.projection_name,v)
        work=f.read(f.receipt_name);next(a for a in work["artifacts"]if a["logical_path"]==f.projection_name).update(sha256=f.ref(f.projection_name)["sha256"],size=(f.root/f.projection_name).stat().st_size);f.write(f.receipt_name,work);f.index()
        with self.assertRaisesRegex(ValueError,"excerpt"):I.material(I.P.Snapshot(f.root),f.ref(f.receipt_name),f.case_id)
    def test_existing_different_receipt_prevents_all_mutation(self)->None:
        f=self.f;name="matrix/receipts/"+f.case_id+".json";f.write(name,b'{}\n');f.index();before=(f.root/"matrix/RESULTS.json").read_bytes()
        output=f.output()
        with self.assertRaisesRegex(ValueError,"different receipt"):
            I.apply(f.root,f.ref(f.receipt_name),f.case_id,output=output)
        self.assertEqual((f.root/"matrix/RESULTS.json").read_bytes(),before)
        self.assertFalse(output.exists())

    def test_output_required_and_source_aliases_rejected(self)->None:
        f=self.f;reference=f.ref(f.receipt_name)
        with self.assertRaises(TypeError):I.apply(f.root,reference,f.case_id)
        outputs=[f.root,f.root/"candidate",Path("relative-candidate"),f.root/".."/"alias-candidate"]
        if os.name=="nt":
            outputs.append(f.root.parent.with_name(f.root.parent.name.swapcase())/"case-alias-candidate")
        for output in outputs:
            with self.subTest(output=str(output)):
                with self.assertRaises(ValueError):I.apply(f.root,reference,f.case_id,output=output)
        self.assertFalse((f.root/"candidate").exists())

    def test_existing_output_foreign_data_is_preserved(self)->None:
        f=self.f;output=f.output();output.mkdir();foreign=output/"foreign.txt";foreign.write_bytes(b"foreign")
        with self.assertRaisesRegex(ValueError,"already exists"):
            I.apply(f.root,f.ref(f.receipt_name),f.case_id,output=output)
        self.assertEqual(foreign.read_bytes(),b"foreign");self.assertEqual(list(output.iterdir()),[foreign])

    def test_linked_output_parent_is_rejected(self)->None:
        f=self.f;alias=f.output()
        try:alias.symlink_to(f.root,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest("directory symlinks unavailable")
        # Remove the alias separately; fixture cleanup must never traverse it.
        f.outputs.remove(alias);self.addCleanup(alias.unlink)
        with self.assertRaisesRegex(ValueError,"Linked|reparse"):
            I.apply(f.root,f.ref(f.receipt_name),f.case_id,output=alias/"candidate")
        self.assertFalse((f.root/"candidate").exists())

    def test_complete_selected_snapshot_excludes_unmanifested_files(self)->None:
        f=self.f;before={name:(f.root/name).read_bytes()for name in I.P.Snapshot(f.root).manifest}
        f.write("unmanifested-private.txt",b"not selected")
        original_manifest=(f.root/"MANIFEST.sha256").read_bytes();result=f.apply()
        self.assertEqual(result["status"],"prepared_requires_repository_validation")
        self.assertFalse((f.root/"unmanifested-private.txt").exists())
        self.assertEqual((f.source_root/"MANIFEST.sha256").read_bytes(),original_manifest)
        for name,raw in before.items():
            self.assertEqual((f.source_root/name).read_bytes(),raw)
            if name not in result["files"]:self.assertEqual((f.root/name).read_bytes(),raw)
        self.assertEqual(f.validate()["receipt_bound_cases"],1)

    def test_competing_source_edit_before_final_write_is_preserved(self)->None:
        f=self.f;source=f.root/"matrix/RESULTS.json";foreign=b"operator competing source edit\n"
        real=I._create_file;output=f.output();reference=f.ref(f.receipt_name)
        def compete(root: Path,name: str,content: bytes)->None:
            if name=="matrix/RESULTS.json":source.write_bytes(foreign)
            real(root,name,content)
        with patch.object(I,"_create_file",side_effect=compete):
            result=I.apply(f.root,reference,f.case_id,output=output)
        self.assertEqual(source.read_bytes(),foreign)
        self.assertFalse((f.root/("matrix/receipts/"+f.case_id+".json")).exists())
        self.assertEqual(result["state"],"candidate")
        self.assertEqual(result["status"],"prepared_requires_repository_validation")
        self.assertEqual(json.loads((output/"matrix/RESULTS.json").read_bytes())["cases"][-1]["id"],f.case_id)
        V.write_manifest(output);self.assertEqual(V.validate(output)["receipt_bound_cases"],1)

    def test_source_mutation_before_read_fails_without_output(self)->None:
        f=self.f;output=f.output();reference=f.ref(f.receipt_name);f.write("README.md",b"new operator edit\n")
        with self.assertRaisesRegex(ValueError,"fingerprint"):
            I.apply(f.root,reference,f.case_id,output=output)
        self.assertEqual((f.root/"README.md").read_bytes(),b"new operator edit\n")
        self.assertFalse(output.exists())

    def test_output_created_after_check_is_not_reused(self)->None:
        f=self.f;output=f.output();real=I._stage_new
        def compete(target: Path,files: dict[str,bytes])->None:
            target.mkdir();(target/"foreign.txt").write_bytes(b"foreign")
            real(target,files)
        with patch.object(I,"_stage_new",side_effect=compete):
            with self.assertRaises(FileExistsError):I.apply(f.root,f.ref(f.receipt_name),f.case_id,output=output)
        self.assertEqual((output/"foreign.txt").read_bytes(),b"foreign")
        self.assertEqual(len(list(output.iterdir())),1)

    def test_partial_failure_and_late_foreign_edit_are_retained(self)->None:
        f=self.f;output=f.output();before=(f.root/"matrix/RESULTS.json").read_bytes();real=I._create_file
        def fail(root: Path,name: str,content: bytes)->None:
            if name=="matrix/RESULTS.json":
                (root/"README.md").write_bytes(b"foreign later edit\n")
                raise OSError("Synthetic partial staging failure")
            real(root,name,content)
        with patch.object(I,"_create_file",side_effect=fail):
            with self.assertRaisesRegex(OSError,"incomplete output retained"):
                I.apply(f.root,f.ref(f.receipt_name),f.case_id,output=output)
        self.assertEqual((output/"README.md").read_bytes(),b"foreign later edit\n")
        self.assertEqual((f.root/"matrix/RESULTS.json").read_bytes(),before)

    def test_foreign_file_created_before_exclusive_open_is_preserved(self)->None:
        f=self.f;output=f.output();real=I._create_file
        def compete(root: Path,name: str,content: bytes)->None:
            if name=="matrix/RESULTS.json":(root/name).write_bytes(b"foreign target\n")
            real(root,name,content)
        with patch.object(I,"_create_file",side_effect=compete):
            with self.assertRaisesRegex(OSError,"incomplete output retained"):
                I.apply(f.root,f.ref(f.receipt_name),f.case_id,output=output)
        self.assertEqual((output/"matrix/RESULTS.json").read_bytes(),b"foreign target\n")

    def test_changed_candidate_is_not_reported_as_prepared(self)->None:
        f=self.f;output=f.output();real=I._create_file
        def compete(root: Path,name: str,content: bytes)->None:
            real(root,name,content)
            if name=="matrix/RESULTS.json":(root/".gitattributes").write_bytes(b"foreign candidate edit\n")
        with patch.object(I,"_create_file",side_effect=compete):
            with self.assertRaisesRegex(OSError,"candidate changed while staging"):
                I.apply(f.root,f.ref(f.receipt_name),f.case_id,output=output)
        self.assertEqual((output/".gitattributes").read_bytes(),b"foreign candidate edit\n")

    def test_unplanned_file_or_empty_directory_rejects_candidate(self)->None:
        f=self.f;real=I._create_file
        for kind in ("file","directory"):
            with self.subTest(kind=kind):
                output=f.output()
                def compete(root: Path,name: str,content: bytes)->None:
                    real(root,name,content)
                    if name=="MANIFEST.sha256":
                        foreign=root/"foreign-unplanned"
                        if kind=="file":foreign.write_bytes(b"foreign material\n")
                        else:foreign.mkdir()
                with patch.object(I,"_create_file",side_effect=compete):
                    with self.assertRaisesRegex(OSError,"candidate inventory differs"):
                        I.apply(f.root,f.ref(f.receipt_name),f.case_id,output=output)
                if kind=="file":self.assertEqual((output/"foreign-unplanned").read_bytes(),b"foreign material\n")
                else:self.assertTrue((output/"foreign-unplanned").is_dir())

    def test_unplanned_symlink_rejects_candidate_and_is_preserved(self)->None:
        f=self.f;real=I._create_file;output=f.output();link=output/"foreign-link"
        probe=f.root/"symlink-probe"
        try:probe.symlink_to(f.root/"README.md")
        except (OSError,NotImplementedError):self.skipTest("file symlinks unavailable")
        finally:
            if probe.is_symlink():probe.unlink()
        def compete(root: Path,name: str,content: bytes)->None:
            real(root,name,content)
            if name=="MANIFEST.sha256":
                link.symlink_to(f.root/"README.md")
        try:
            with patch.object(I,"_create_file",side_effect=compete):
                with self.assertRaisesRegex(OSError,"Linked|reparse"):
                    I.apply(f.root,f.ref(f.receipt_name),f.case_id,output=output)
            self.assertTrue(link.is_symlink())
        finally:
            if link.is_symlink():link.unlink()

    def test_commit_snapshot_preserves_later_source_worktree_edit(self)->None:
        f=self.f;reference=f.ref(f.receipt_name);output=f.output()
        env={key:value for key,value in os.environ.items()if not key.startswith("GIT_")}
        def git(*args: str)->str:
            result=subprocess.run(["git","-c","core.autocrlf=false","-c","commit.gpgsign=false",
                "-c","core.hooksPath="+str(f.root/".empty-hooks"),"-c","user.name=Fixture",
                "-c","user.email=fixture@example.invalid","-C",str(f.root),*args],
                capture_output=True,timeout=30,env=env)
            self.assertEqual(result.returncode,0,result.stderr.decode(errors="replace"))
            return result.stdout.decode().strip()
        git("init");git("add",".");git("commit","-m","Synthetic matrix snapshot")
        commit=git("rev-parse","HEAD");f.write("matrix/RESULTS.json",b"later worktree edit\n")
        result=I.apply(f.root,reference,f.case_id,output=output,commit=commit)
        self.assertEqual(result["state"],"commit_snapshot");self.assertEqual(result["commit"],commit)
        self.assertEqual((f.root/"matrix/RESULTS.json").read_bytes(),b"later worktree edit\n")
        self.assertFalse((output/".git").exists());V.write_manifest(output)
        self.assertEqual(V.validate(output)["receipt_bound_cases"],1)

    def test_cli_apply_requires_output_and_output_requires_apply(self)->None:
        f=self.f;base=[sys.executable,"-B",str(f.root/"tools/receipt_import.py"),"--root",str(f.root),
            "--receipt",f.receipt_name,"--sha256",f.ref(f.receipt_name)["sha256"],"--case",f.case_id]
        for extra,message in [(["--apply"],"--apply requires --output"),
                              (["--output",str(f.output())],"--output requires --apply")]:
            result=subprocess.run([*base,*extra],capture_output=True,timeout=30)
            self.assertEqual(result.returncode,2);self.assertIn(message,result.stderr.decode())

    def test_boolean_integer_excerpt_aliases_are_rejected(self)->None:
        f=self.f
        for observed,projected,accepted in [(1,True,False),(0,False,False),(1,1,True),(True,True,True)]:
            with self.subTest(observed_type=type(observed).__name__,projected_type=type(projected).__name__):
                source=f.read(f.source_name);source["observed"]=observed;f.write(f.source_name,source)
                source_ref=f.ref(f.source_name)
                card=f.read("work/fixture/card.json");card["contract"]["inputs"]=[source_ref]
                for row in card["checks"]:row["evidence_refs"]=[source_ref]
                f.write("work/fixture/card.json",card)
                projection=f.read(f.projection_name);projection["receipts"][0]["sources"][0]["sha256"]=source_ref["sha256"]
                projection["receipts"][0]["excerpts"][0]["fields"]["observed"]=projected;f.write(f.projection_name,projection)
                work=f.read(f.receipt_name);work["contract_ref"]=f.ref("work/fixture/card.json")
                for row in work["artifacts"]:
                    row.update(sha256=f.ref(row["logical_path"])["sha256"],size=(f.root/row["logical_path"]).stat().st_size)
                f.write(f.receipt_name,work);f.index()
                if accepted:I.material(I.P.Snapshot(f.root),f.ref(f.receipt_name),f.case_id)
                else:
                    with self.assertRaisesRegex(ValueError,"excerpt"):I.material(I.P.Snapshot(f.root),f.ref(f.receipt_name),f.case_id)

    def test_index_boolean_integer_alias_is_not_equal_metadata(self)->None:
        f=self.f;f.apply();name="matrix/receipts/"+f.case_id+".public-artifacts.json"
        index=f.read(name);self.assertEqual(index["withheld"]["private_artifacts"],1)
        index["withheld"]["private_artifacts"]=True;f.write(name,index);f.index()
        with self.assertRaisesRegex(ValueError,"artifact index"):f.validate()

    def test_generated_table_cannot_drift_from_data(self)->None:
        f=self.f;f.apply();p=f.root/"matrix/MATRIX.en.md";p.write_text(p.read_text().replace("| SYN-R01","| Changed"),encoding="utf8",newline="\n");f.index()
        with self.assertRaisesRegex(ValueError,"Coverage table"):f.validate()

if __name__=="__main__":unittest.main()
