# VS Code: catalog refresh and persisted picker selection (R03)

A fresh MCP tool registry can coexist with stale rows in an already-open **Configure Tools** picker. Confirming a modified selection in that stale view can leave a newly added tool disabled, including after a full application restart.

This is a version-bound companion to [the original R03 schema-drift case](../../matrix/MATRIX.en.md#r03-inputschema-changed-inside-one-native-session), using the existing `vscode` subject. The original measurements and receipt are retained unchanged.

| Experiment | Boundary and recorded result | Public observations |
|---|---|---|
| VS Code 1.145.2, official MCP SDK 1.32.2, stdio | One initialize, two list-change notices and three tools/list requests; registry reflects add/remove while the open UI retains old rows. Reopening reflects the new list. No tool calls in this experiment. | [catalog excerpts](catalog-observations.json) |
| Installed VS Code 1.146.0 | Minimal server switches keep/removed to keep/added. An actual server Stop/Start resets the second pass. Unchecking keep in the stale picker, OK and full close/restart preserve a false group; added has no explicit entry and is effectively disabled. | [installed excerpts](installed-observations.json) |
| VS Code 1.148.0 self-host, paired baseline/patched | Same pinned baseline and diagnostic support: baseline retains removed and hides added; patched shows added and removes removed. OK retains keep=true/off=false, with added=false before the fix and added=true after it. Maps survive full restart in both arms. Patched added-tool callbacks occur before and after restart. | [paired excerpts](paired-observations.json) |
| Component regressions and fresh-main port | Three MCP group cases fail on baseline. An initial patch passes one and fails two; refined patch passes six picker cases. Fresh-main port repeats red 3/3 failing, green 6/0 failing, build/types/lint exit 0. These are coverage counts, not separate findings. | [component results](paired-observations.json) |

The three group cases cover pending group-off, pending group-on and mixed selection as tools are added/removed. Other picker checks cover live refresh, pending individual choices and filter preservation. Component checks use real QuickTree/DOM with controlled services; native observations above provide a separate boundary.

Phase labels in the public excerpts are formatted for display; the Node version prefix and number are stored separately. UTC timestamps, tool names and selection values are retained.

The paired excerpts focus on picker rows, selected maps and server callbacks; registry refresh is documented in the separate 1.145.2 experiment.

The useful research chain is **notice and list response -> registry -> open rows -> OK -> persisted selection -> restart**. A successful tools/list refresh alone does not establish that the user-facing selection reflects the current catalog.

## Reproduce

Save [catalog-change.mjs](catalog-change.mjs) and configure a local MCP stdio server with command `node` and that script as its argument. The script has no external dependencies and starts its 45-second catalog-change timer once per process, after initialized.

1. Start the server and open Chat -> Configure Tools; expand its group. Initial tools: matching_keep and matching_removed.
2. Keep the picker open past 45 seconds. The server replaces matching_removed with matching_added; affected open rows remain old.
3. Close and reopen Configure Tools. The current catalog appears.
4. Stop and restart the MCP server before a second pass. Open the initial picker again and let the new 45-second timer expire.
5. In the stale view uncheck matching_keep, press OK, fully close and restart VS Code with the same profile, then inspect the picker. This left matching_added effectively disabled on installed 1.146.0.

Use an isolated profile and a workspace you have chosen to trust. The paired self-host comparison and component checks are additional experiments; this script does not perform them automatically.

## Limits and controls

- These are selected projections of retained experiments, curated on 2026-11-21; this producer performed offline evidence checks, with no new VS Code target run. Full private bench logs and local receipt ancestry are not public.

- The 1.145.2 SDK trace, installed 1.146.0 persistence run and paired 1.148.0 self-host runs are separate experiments, not one cross-version transaction.

- Ordinary user consent for a changed inputSchema remains unmeasured; the previous R03 schema case retains its original scope.

- The measured stale-OK outcome leaves the added tool disabled. An expansion of authority was not established by these experiments.

- A diagnostic call to disabled fixture_off succeeded in both self-host arms. It used the stock tool service with actual userSelectedTools and undefined context. This is a selection-versus-dispatch control, with no default-agent or LLM turn and no authorization finding. The removed-tool control stopped at diagnostic lookup before stock invocation.

- The self-host runs used the same generated observation/invocation support in both arms; multiple server processes occurred. Matching official native binaries were reused where dependency versions matched. These are instrumented self-host runs.

- The installed 1.146.0 binary was unchanged; a public-API observer/command-opener extension and an isolated profile were used. Its restart outcome has a false group and no explicit added entry: effective disabled is not a literal stored added=false.

- VS Code remains the existing subject: this case adds no host and does not revise the 2026-10-25 snapshot or historical 12/12 and 8/8 counts.

- Issue 349603 and PR 349608 were submitted on 2026-11-21. Acceptance, merge and release are separate events; this case does not claim them.

## Submitted upstream

- [Issue 349603](https://github.com/microsoft/vscode/issues/349603)
- [PR 349608](https://github.com/microsoft/vscode/pull/349608), submitted commit `26e69320b01705c4342afa7d54de7408ba6f4cff`

The reproducer and selected observations are supplied by Alex Gercog. The [portable research card](card.json) and receipt bind this public projection; byte integrity is distinct from independent reproduction.
