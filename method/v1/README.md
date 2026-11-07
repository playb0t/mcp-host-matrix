# Portable work method

The work-evidence method, version 1.0.0, records four work profiles and public
receipt links. It is independent of a particular agent runtime or matrix.

## Acceptance boundary

A Snapshot reads a single repository `MANIFEST.sha256`. Every referenced card,
receipt, method file and artifact must be listed there with its current hash.
With an explicit full Git commit ID, all reads use that commit tree, including
the manifest. A working tree is reported as candidate. A commit snapshot alone
does not prove publication to a particular remote: obtain the repository and
expected commit through the channel whose records you intend to accept.

The manifest does not list itself. The method MANIFEST.json lists exactly its
portable.py, SPEC.json and README.md. Examples are outside that method bundle,
so example references to the bundle do not create a content-hash cycle.
No network requests or subject execution take place.

## Card

A work-method-card/1 has exactly schema, case_id, profile, variant, method_ref,
contract, checks, outcome and limits. The profile is engineering, research,
document or publication. Only research may use variant mcp; other variants
are not defined. method_ref has id, version, logical_path and `sha256`.

The contract has exactly scope, completion, options, inputs, plans and
exclusions. Completion is verified or bounded. Inputs and evidence references
have logical_path and `sha256`. Paths are canonical repository-relative names,
with forward slashes; traversal, aliases and filesystem links are rejected.
Plans contain id, purpose and kind. Every plan has one result with the same
id and kind. Results contain state, reason and nonempty evidence_refs.
State is passed, failed or incomplete. A research conclusion also records
verdict supported, refuted or inconclusive. Its state describes completion of
the assessment; refuted does not mean that the assessment failed to complete.

Required purposes and kinds are in SPEC.json. Source-only research may exclude
controls with a reason; experimental research may not. Engineering may exclude
regression with a reason; original-content documents may exclude sources;
preparation-only publication may exclude delivery. Other required checks
cannot be waived. Exclusions and plans are part of the hashed contract.

Engineering options require change_mode changed or no_change; a
research_derived boolean adds a research_basis parent requirement. Research
requires mode source or experimental. Document options require format md,
text, json, html, docx, pdf, pptx or xlsx. Publication requires stage prepared
or published and a destination object with channel and target. Consumer
extensions such as options.matrix_cells are interpreted by their consumer.

Failed or incomplete checks require bounded completion and explicit limits.
The resulting outcome is bounded. Otherwise research has outcome assessed,
engineering and document have outcome verified. Publication has outcome
prepared or published matching its stage; failed delivery cannot be hidden
under bounded completion.

Public checks are projections of declared results. This module verifies their
structure, linkage, selected snapshot and bytes. It does not re-execute a
command, inspect a private validation report, evaluate semantic truth or
replace the producer's independent review and actual observations.

## Receipt

A work-method-receipt/1 has exactly schema, case_id, profile, variant,
method_ref, contract_ref, artifacts, parents, outcome and withheld.
contract_ref points to the public card. Its profile, method, identity and
outcome must agree. Each public artifact has logical_path, `sha256`, size and
visibility public. All artifact bytes are available in the same snapshot.

Parents contain ref and relation input, research_basis or publication_input.
A research_basis parent has research profile. A research-derived engineering
receipt requires that relation. A publication requires publication_input and
its output bytes must occur among direct publication_input parent artifacts. A
transformation first receives its own producer receipt.

Withheld contains only nonnegative internal_artifacts and private_artifacts
counts. Private validation reports, machine paths, producer labels, private
artifact names and private hashes are not fields of this envelope. This is a
new public projection; it is not a byte copy of an internal receipt graph.
Review the public payload itself before release: schema checks cannot decide
whether an arbitrary human-written source discloses private information.

## Use

From the repository root, verify a declared receipt:

```console
python -B method/v1/portable.py --root . --receipt method/examples/receipts/publication.json --sha256 HASH
```

Add --commit FULL_COMMIT_ID to select one exact Git tree. The command reports
PASS or FAIL and candidate or commit_snapshot; it never claims publication.
The Python API provides Snapshot, validate_card, verify_method and
verify_receipt. verify_receipt returns the root receipt and card, deduplicated
nodes, and public artifacts with their receipt_sha256. Hashes identify bytes;
they do not authenticate a person or grant authority.

The examples contain synthetic records and an expected failing mutation.
They are not MCP observations or a substitute for experimental controls.
