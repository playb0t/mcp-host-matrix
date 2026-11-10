# Evidence policy

[Project](../README.md) · [Matrix](../matrix/MATRIX.en.md) · [Structured results](../matrix/RESULTS.json)

## Scope and units

Each observation is bound to a component version, operation, authentication profile, runtime, policy and fixture. Documentation describes inspected pages; runtime receipts describe identified processes and requests. These evidence layers are reported separately.

R01 contains 23 selected run IDs: 12 base windows, 8 operation variants and 3 additional healthy timing windows. R06 contains four paths across two profiles: eight cells, one completed trial per cell. R05 contains one native trigger and three automatic refresh attempts. These units are not interchangeable.

## Future observation records

The following fields are required for new observations; they do not change the existing snapshot.

- Identify the full scenario: client and exact version/build, server and version/build or fixture configuration, endpoint, and authentication profile. Retain the runtime, policy and fixture context. Unknown identity fields remain explicit.
- Record the connection step: configuration generation, discovery, client registration, login, or MCP invocation. Keep evidence, failures and unmeasured steps separate; success at one step does not establish a later step.
- Keep connection outcomes and tool-boundary assessments in separate linked records. For a claimed tool boundary, identify the declared scope, effective backend principal and grants, enforcement point, and applicable positive and negative controls. Link the records to relevant existing R01-R06 observations without adding directions or transferring their outcomes.
- For DCR observations, record the selected registration method, authorization-server metadata and support flags, and the assessed specification revision. A successful DCR flow alone does not establish CIMD support or compliance with registration-selection rules.

### Diagnostic-copy observations

For future observations involving diagnostic data, identify the source data class, producer, destination, expected audience, actual reader context and namespace. Distinguish literal credentials from references and public metadata. Keep captured arguments, tool-result reflections, application logs, standard error, telemetry exports and client history within an explicitly declared observation scope; a channel name alone does not establish confidentiality.

Assess content minimization, effective access and retention independently, against a stated policy. Record the execution branch, artifact and attempt identity, observer health/window, controls, evidence and unmeasured channels. Source inspection is separate from runtime observation. Do not combine separate runs into one claimed end-to-end disclosure. A return to the original authorized caller alone does not establish disclosure to another reader.

Disconnect, grant revocation and deletion of named retained data are distinct operations. State the authorized ownership/scope, requested action, result and verification for each retained object. Absence from one namespace does not establish an ACL denial; a fix for future records does not establish deletion of prior copies. A receipt signature alone does not prove destruction of all copies.

These requirements apply to future evidence records. They add no measured subjects, research directions, observations, scores or denominators, and do not alter the current snapshot or imply consumer/schema integration.

Background: [CWE-532](https://cwe.mitre.org/data/definitions/532.html) describes sensitive information in log files. [MCP Logging security](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/logging) addresses the protocol logging channel. [OpenTelemetry OBI trace selection](https://opentelemetry.io/docs/zero-code/obi/configure/metrics-traces-attributes/) separately documents sensitive MCP argument/result capture. Each source retains its own scope and revision; these references do not establish a new weakness class.

## Reading the evidence

| Material | Establishes | Scope |
|---|---|---|
| Vendor documentation | What a selected page said at the recorded read date | Does not establish runtime behavior |
| Versioned implementation | Inspected paths and checks | Does not establish that an unobserved execution took a path |
| Controlled runtime receipt | What the fixture and identified processes observed | Bound to its version, profile, policy and observation window |
| Curated projection | Selected results, counts, controls and limits | Raw author-held receipts are identified separately |
| SHA-256 | Identity of particular bytes | Does not establish truth, completeness or independent reproduction |

A missing request supports an absence within the stated healthy observation window. A recorder event, timeout or HTTP response must be read with its qualified controls. Working controls include logout/revocation, A-positive refresh before B-resource refusal, readable/private-denied file canaries, no-change schema notification, exact-target opener matching and valid/invalid refresh comparisons.

Controller replay and native new-build reuse are separate observations. An intended response is not a delivered response. Configuration removal, grant retirement, registration deletion, local storage, transport and accepted work are distinct states.

## Material limits

- R02 uses synthetic bridge caches and known-path readers. Real default-profile runtime access and native other-SID discovery/write were not measured. The denied projection retained EPERM without an exact syscall.
- R03 uses programmatic VS Code invocation and automatic trust settings in a fixture workspace. Ordinary UI consent and poisoning resistance were not measured.
- R04 uses an inert executable in an instrumented child environment. Real PowerShell, browsers and URI handlers were excluded. Metadata response bodies were not separately captured.
- R05 redirects between two owned loopback origins. The receiving origin denies exchange. Attacker control of trusted-server Location and successful exchange at a real provider were not established.
- Native R06 rows use same-path/profile build replacement after natural access expiry; bridge rows use explicit-pin or local-latest launch selection without waiting for access expiry. Official installers/auto-updaters were not measured; VS Code ciphertext was not decrypted. Store snapshots follow the observation window and controller replay.

These limits define what the reported results establish. They do not negate the observed credential delivery, retained authority or other measured transitions.

## Data and receipt availability

The repository bundles curated documents and projections. [EVIDENCE.json](../matrix/EVIDENCE.json) identifies source artifacts by ID, role, SHA-256 and availability.

[Selected deidentified R01-R06 receipts](../matrix/receipts/README.md) include saved field-level observations, controls, source fingerprints and JSON locators. Raw credentials, personal profiles/paths, complete personal SIDs and the fixture implementation are excluded. Full originals remain author-held; suitable additional material may be requested through the [repository tracker](https://github.com/playb0t/mcp-host-matrix/issues). The current package is not a self-contained rerun. Package-specific disclosure records retain their own scope and attribution.

Snapshot dates and documentation read dates bound the results' currency. A package version identifies the measured artifact; it does not date an unversioned vendor page. Protocol revision dates and event timestamps retain their technical meaning.

## Glossary

| Term | Meaning in this matrix |
|---|---|
| A / B | Case-local labels. R02 URL/resource tests use original and second server configurations sharing a bridge cache; file tests identify readers separately. R05: A is the original token endpoint, B the redirect target. |
| STATIC | Manually configured, pre-registered client identity without DCR or CIMD; a fixture label |
| MCP | Model Context Protocol |
| Host / bridge | A native client environment / a separately launched intermediary such as mcp-remote |
| Fixture | The controlled synthetic provider, resource server or test environment |
| PUBLIC | OAuth client kind without client-secret authentication; separate from how the client is registered |
| DCR | Dynamic client registration at the authorization server |
| CIMD | Client ID Metadata Documents, using a metadata URL as client identity |
| PUBLIC-NODCR | Tested profile with a public client and dynamic registration disabled |
| CONFIDENTIAL-NODCR | Tested profile with client-secret authentication and dynamic registration disabled |
| CIMD-NODCR | Tested metadata-document client-identity profile without dynamic registration |
| DCR-ON | Tested profile with dynamic client registration enabled; token method remains case-specific |
| AS / RT / TTL | Authorization server / refresh token / time to live |
| Revocation request | A request to the provider's token-revocation endpoint; distinct from deleting configuration |
| Controller replay | A separate refresh request made with the required profile credentials before/after an operation |
| 200 / 200 | Before / after HTTP responses for that replay, not a general safety grade |
| Token issued | A new access token was returned; a semantic outcome, distinct from an HTTP-code-only claim |
| ACK | Observer-recorded action evidence; not necessarily exact click time or host-native acknowledgement |
| SID / ACL / DACL | Windows security identifier / access control list / discretionary access control list |
| PID / TCP | Process identifier / Transmission Control Protocol |
| STDIO / RPC | Standard input/output transport / remote procedure call |
| URI / PKCE | Uniform Resource Identifier / Proof Key for Code Exchange |
| n/a / Not measured | Not applicable to that profile / no measurement claim in this snapshot |

## Repository verification

`python -B tools/validate.py` checks JSON structure and references, declared file fingerprints and editable scenes, relational counts, local links/anchors and image references, LF text, common private-data patterns, any SVG content, and the complete file manifest. It does not launch subjects or contact providers. Integrity checks do not independently reproduce the measurements.

After an intentional edit, `python -B tools/validate.py --write-manifest` regenerates checksums. Source fingerprint changes require inspecting the source and its projection.

Use the [regression selection map](../matrix/REGRESSION.md) to identify a version-bound follow-up relevant to an implementation change.

## Receipt-bound observations

New cells use the [portable work method](../method/v1/README.md). A research
card declares options.matrix_cells and its public matrix-projection.json.
The projection contains the subjects, cases, source excerpts and derived
checks reviewed inside the research. The importer copies those declarations;
it does not compose new observations at import time.

New matrix receipts use mcp-host-matrix-receipt/2. Their provenance contains
work_receipt_ref (logical_path and `sha256`), work_receipt_sha256, profile,
variant and contract_sha256. The work receipt is the portable public
work-method-receipt/1; contract_sha256 identifies its public card contract.
It is not the hash of a private validation report or internal graph.

The adjacent public-artifacts index must equal that receipt's public artifact
metadata. It is not independent proof. Every matrix source hash must occur
among the receipt's direct public artifacts, whose bytes must exist in the
same repository snapshot. Excerpts and declared equality/distinctness checks
are compared with their public JSON sources. Internal and private artifacts
contribute only the receipt's withheld counts; their names and hashes are not
copied into the matrix receipt or index.

A selected repository accepts receipts covered by its MANIFEST.sha256 with
their cards, method bundle and data in that same selected Git tree. A working
tree is candidate-only. A local Git commit does not prove remote publication;
obtain the intended repository and commit independently. The verifier never
contacts subjects or publishes. Hash consistency does not establish semantic
truth or authenticate a producer.

The exact R01-R06 case content and six saved receipts remain legacy at the
25 October 2026 snapshot. Their bytes and case fingerprints are pinned; a
changed file cannot gain a legacy exemption merely by using an old ID.
Legacy observations are not retroactively represented as new work receipts.

subjects is a catalog of hosts, bridges, components or services. A new cell
names subject_id and requires its own receipt. Only that designated subject
gets coverage in a new row; contextual native_hosts or components do not
establish additional measured subjects. Adding a catalog entry does
not measure that subject. Materialize and Neon receive cells only when
suitable research receipts are available. Source-only research cannot claim
a measured cell. The marked subject-coverage table is rendered from RESULTS;
the surrounding narrative remains editorial text. Unknown is retained for an
unresolved selected cell; M remains a coverage mark rather than a safety grade.
Import also rebinds the one
figures/SOURCES.json fingerprint for the intentionally changed RESULTS file.
Existing figure bytes and labels remain the legacy projections; no new figure
coverage is claimed by that metadata update.

Prepare an import in a separate, absolute, previously absent output directory.
Its parent must exist, and the output must be outside the source root, with no
linked or aliased path components. --apply requires --output; --output is
rejected for a verification-only call. The source repository is read-only to
the importer. For example, set SOURCE and NEW_CANDIDATE to absolute paths:

```console
python -B tools/receipt_import.py --root SOURCE --receipt RECEIPT --sha256 HASH --case CASE --apply --output NEW_CANDIDATE
python -B tools/render_matrix.py --root NEW_CANDIDATE --check
python -B tools/validate.py --root NEW_CANDIDATE --write-manifest
python -B tools/validate.py --root NEW_CANDIDATE
```

The importer verifies and stages every file listed in the selected source
manifest, plus the calculated cell, receipts, rendered table and figure-source
fingerprint. Unmanifested files and .git are excluded. Snapshot content is
bounded to 256 mebibytes. With --commit, every copied source file comes from that
explicit commit, even if the worktree has later edits. Without --commit, every
selected file must match the captured manifest; a changed selected file fails
verification if observed before copying. Source edits after those reads remain
in the source and are not claimed as part of the candidate.

The output directory and its files are created exclusively. Final readback
checks the expected bytes and exact file/directory inventory, rejecting
unplanned entries and links. Existing outputs and conflicting files are never
reused, replaced or rolled back. A failure
after output creation retains an explicitly reported incomplete directory,
including any later foreign edits; inspect it and choose a fresh output for a
retry. No cooperative lock protects noncooperating editors. Path and content
checks detect observed changes; they are not a filesystem transaction against
a hostile process that swaps directories or edits after the checks. Use a
parent directory controlled by the operator and review the candidate before
any later publication.

Success reports prepared_requires_repository_validation, not a completed
import or publication. The copied source manifest intentionally predates the
calculated updates. Review those changes, then explicitly regenerate and
validate the candidate manifest as above. CI also executes the portable-method
and importer unittest suites; all these checks remain offline and do not
reproduce product measurements.
