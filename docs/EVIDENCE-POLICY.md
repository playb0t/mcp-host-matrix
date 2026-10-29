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
