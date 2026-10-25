# Selected deidentified receipts

[Project](../../README.md) · [Matrix](../MATRIX.en.md) · [Evidence policy](../../docs/EVIDENCE-POLICY.md)

These six receipts expose selected observations and controls from existing saved evidence. They are field-level excerpts, not complete journals or a self-contained rerun. Full originals remain author-held. The connectivity track has separate structured results and is not covered by these receipts.

| Case | Receipt | What it exposes |
|---|---|---|
| R01 | [Disconnection](../../disconnect/bench/receipts/R01.json) | Twelve base windows, separate controller refresh before/after, logout and Clear authentication controls; scoped VS Code traffic attribution |
| R02 | [Retained file and ACL boundary](R02.json) | A-only same-SID file retention and refresh after claude mcp remove; inherited access versus a denied synthetic DACL projection, with fresh/invalid/revoked controls |
| R03 | [Schema drift](R03.json) | Same-session schema A/B, change notices, five server-side call validations and native metadata snapshots |
| R04 | [Executable boundary](R04.json) | Inert recorder event, HTTP/unsupported-URI pair, zero code/token issuance and opener/helper timing |
| R05 | [Refresh redirect](R05.json) | Three automatic attempts from one trigger, body digest/length at the second origin, POST and 400 responses, direct-refresh control |
| R06 | [Build replacement](../../disconnect/bench/receipts/R06.json) | Eight source verdicts, observation windows, controller replay, four native prior-refresh joins, retained bridge file hashes and revocation controls |

## Reading a receipt

Each source has an ID, a SHA-256 of its unchanged original bytes and a format. Each excerpt names a source and a JSON Pointer. Its `fields` map selects paths relative to that pointer; values are copied without rewriting. For JSONL, the pointer addresses a zero-based array of parsed lines. Thus `/0` is the first recorded line, not an event sequence number.

`derived_checks` are author-computed comparisons or counts over the specified source locations. Where account, token or process identifiers are omitted, the public excerpt preserves the comparison result and locators, but cannot independently demonstrate equality of those hidden values. Source fingerprints support later byte verification; they do not independently prove an observation true.

Credentials, complete personal SIDs, account/machine names and local paths are omitted. Known synthetic tool arguments, error codes, event sequence numbers, content hashes and required timing values remain. The repository [manifest](../../MANIFEST.sha256) fingerprints the published excerpts, separately from the fingerprints of their author-held sources.

F01 exposes the demonstrated retained-file subcase, together with the source run's overall status; it does not claim the entire source run passed. F02 does not establish access to a real default profile. R03 does not measure ordinary UI consent. R04 does not execute real PowerShell or a browser. R05 does not demonstrate a successful real-provider token exchange. R06 measures owned build replacement, not official updater behavior.

Further suitable source material may be requested through the [repository tracker](https://github.com/playb0t/mcp-host-matrix/issues).
