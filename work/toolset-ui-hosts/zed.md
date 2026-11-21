# Zed: tool-set picker lifecycle

Open selector retained keep/removed after the client received keep/added in two passes.

Reopen showed the new list; immediate selection and full restart retained keep=false, inherited added=true.

The native surface is agent: manage profiles > Write > Configure MCP Tools. Selections persist immediately; Go Back completes the view. The open list was stale while wire responses contained the new tools. Reopen refreshed it. The explicit keep=false entry and inherited added state survived restart.

## Evidence

[Curated observations](zed.json) · [Original fixture](../vscode-toolset-ui/catalog-change.mjs) · [Projection](matrix-projection.json)

## Limits

- Selected deidentified excerpts of retained native observations, not a self-contained replay. Raw journals, private images and local receipt ancestry remain author-held.
- The wire catalog and visible interface are separate observations. The private in-memory client registry was not inspected.
- No model turn or paid request was initiated. No fixture tool was invoked; model dispatch and authorization expansion were not tested.
- Normal confirmation and full application restart do not establish crash durability, atomic writes or concurrent-writer behavior.
- These cases add no subjects or directions and do not change the legacy snapshot, its historical 12/12 and 8/8 counts, or the existing VS Code case.
- Internal independent review is not external peer review or independent reproduction. PASS/FAIL of a local UI criterion is not a product safety grade.
- The selector saves changes immediately. Go Back is the native completion action; there is no OK button.
- The explicit stored entry is matching_keep=false. matching_added is enabled through inherited enable_all_context_servers=true, not a separately stored added=true entry.
- The first native click materialized the inherited enabled state; a second click produced the observed disabled state. No root cause is inferred.
- A custom user-data directory isolated configuration and data. Windows KnownFolder IPC is a separate limitation; no claim covers all system files.
- All six retained distribution files remained unchanged.

