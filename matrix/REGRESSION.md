# Regression selection map

[Matrix](MATRIX.en.md) · [Data](RESULTS.json) · [Evidence policy](../docs/EVIDENCE-POLICY.md)

This is a proposed selection map, not an executed campaign.

| Direction | Reachable change to inspect | Smallest useful follow-up | Required controls and boundaries |
|---|---|---|---|
| R01 | Remove/disable/logout, revoke, store cleanup, registration or accepted-work lifecycle | Affected native operation and profile with a fresh synthetic grant; provider observations and separate prior-refresh replay | Healthy window; before/after replay; working revoke; actual ACK meaning; drain/cancellation policy; file-edit versus UI |
| R02 | Cache serialization, normalization, namespace, writer/removal or Windows ACL | Select ordinary URL, alias, resource or post-remove reader matching the diff and access subject | Same-tuple positive; A-positive before B; own/private canaries; fresh/invalid/revoke; effective owner/DACL provenance; real-profile/syscall limits |
| R03 | List notifications, schema caches, argument validation or approval/trust | No-change and changed inputSchema on the same connection, then valid/stale calls | Server validator and call receipts; explicit API/trust settings; ordinary consent requires its own test |
| R04 | Metadata validation, sanitizer ordering, URL/opener or platform dependency | Qualify inert recorder, then selected HTTP/unsupported-URI pair | Exact argv/process identity; success/exit chronology; other-target rejection; prior effects; no inference about real interpreter/browser |
| R05 | Token fetch, redirects, form handling, bundled SDK or runtime | Selected PUBLIC 307 cross-origin refresh with direct and receiver controls | Trigger versus attempts; exact body/recipient; valid/invalid refresh; bootstrap versus new issuance; receiver denial; separate Location authority |
| R06 | Selectors, migration, registration or cross-build refresh reuse | Affected old/new pair and PUBLIC/DCR profile; separate native-first-connection and controller observations | Natural expiry; fresh baseline; late-store timing; wrong-client/management/revoke/fresh controls; official installer separate |

## Integration-state selectors

Seven selectors cover changes that sit beside the R01-R06 directions. Each one names what to keep separate after a change and the smallest useful controls. They are selection hints. They add no directions, subjects, rows, counts or outcomes, and no selector inherits a verdict from a direction.

| Selector | Change after which a check is useful | Keep separate | Smallest controls | Boundary |
|---|---|---|---|---|
| `IG01` | Authorization flow, migration, writer, storage backend or access policy | New, retained and mixed state; file metadata and effective access | Fresh and retained state; same-owner success and an independent reader; mode readback after the change | A readable synthetic token does not establish that a real credential is valid |
| `IG02` | Parser, encoder, resolver or reference form | The validated field and the resource finally addressed | An ordinary allowed resource; boundary, alias and normalization forms; the final request target | A different path at a recorder does not establish backend acceptance |
| `IG03` | Principal, object-key provenance or delegation | The logical owner of an object and the authority of the shared executor | The same trusted subject continues; another subject with the same known identifier; forged and expired proofs refused before downstream effects | An identifier or a synthetic label does not establish a trusted identity |
| `IG04` | Error, event, serialization or telemetry mapping | Transport, protocol, application and persisted outcomes | Ordinary success; partial and empty failure; the emitted events against the saved representation | A saved marker does not establish that every log is complete |
| `IG05` | Cancellation, asynchronous acquisition or resource lifecycle | Cancellation, completion, resource release and authority revocation | Ordinary completion; early and late cancellation with a late acquisition; completion before the fixture is retired | A closed local socket or session is not a provider revocation |
| `IG06` | Concurrent persistence, retry, versioning or a replacement contract | Request order, the storage contract and the final backend state | A controlled order and overlap; the authoritative version or append contract where one exists | Request order and a described contract do not establish the final state or atomicity |
| `IG07` | A session, client or connection shared by several calls; event routing, multiplexing or a lock | The session and the single call; the result of a call and what arrives beside it: progress, server requests and errors | Two overlapping calls on one session, each with its own handler, where every progress message and server request must reach the call that caused it; a nested call where the contract allows one; cancelling one call while the other finishes | Correct results do not establish that the events reached the right call |

`IG01` can select an R02 follow-up and `IG05` an R01 lifecycle follow-up. R06 migration and reuse need their own evidence that the authority is still valid; readable saved data is not enough.

For `IG07`, run the calls at the same time. Calls made one after another can pass while overlapping calls still mix. If a fix stops the mixing by making calls wait for each other, check that parallel and nested calls still work where the contract promises them. When an event carries nothing that ties it to a call, record its owner as unknown and do not assign it to the latest call.

### Worked examples

Each selector below was applied to one open-source change. The links lead to the filed pull requests, which carry the code and the regression tests. A filed pull request is not a vendor acceptance, a merge or a release.

| Selector | Change | Pull request |
|---|---|---|
| `IG01` | An OAuth-only setup stopped writing tokens and, in automatic mode, kept earlier token files with their public modes. On one filesystem a chmod that reported success left the mode unchanged. | [sanity-io/cli 2257](https://github.com/sanity-io/cli/pull/2257) |
| `IG02` | A path parameter that is exactly a dot segment passed encoding and was normalized into another request path. | [sanity-io/client 1417](https://github.com/sanity-io/client/pull/1417) |
| `IG03` | A shared organization writer took the conversation identifier chosen by the browser. The change scopes it to a signed anonymous session. | [sanity-io/context 304](https://github.com/sanity-io/context/pull/304) |
| `IG04`, `IG05` | An in-band stream error ended through the finish hooks without a failure marker. Request cancellation did not reach the model call or the pending connection. | [sanity-io/context 303](https://github.com/sanity-io/context/pull/303) |

`IG06` has no worked example. The order of outgoing snapshot requests was observed; the backend outcome was not measured.

`IG07` has no worked example.

## Recording a follow-up

Apply the [future observation fields](../docs/EVIDENCE-POLICY.md#future-observation-records) to each new follow-up. Freeze the full client/version, server, endpoint and authentication-profile identity, then name the affected connection step. Keep connection and tool-boundary checks in separate linked records under the applicable existing R01-R06 scope. For registration changes, retain the selected method, authorization-server metadata and specification revision. Unmeasured steps remain explicit.

For event presence or absence, see the [paired observation checks](../examples/claims/README.md). For a denominator or a log-order claim, compare the [worked R01 and R04 grounds](../grounds/README.md).

## After a patch

1. Freeze old/new selector, resolved version, archive/binary hash, actual public entry, bundled SDK/dependencies, runtime, OS and policy. A top-level version alone does not identify the loaded implementation.
2. Inspect the reachable diff and affected state transition. Unknown relevance remains unknown; it is neither a fix nor a new failure.
3. Select the smallest affected case with its controls. Broaden for shared dependencies, changed boundaries, failed controls or a broader claim.
4. Preserve the old result. Add a version-bound outcome with receipts, failures and limits, then compare the same criterion. Do not overwrite history or convert an unrun row to PASS.
5. Review source changes, update the projection/fingerprints, then check links, privacy and checksums.

A redirect fix need not trigger all six directions. A package update does not close unrelated host observations. One URI, profile or OS does not settle every combination.

Other hosts/profiles, ordinary UI consent, real-profile/native other-SID discovery and write, real interpreters, other redirect/issuer/resource/TLS contexts, official updates and broader conformance/integration remain separate scopes.
