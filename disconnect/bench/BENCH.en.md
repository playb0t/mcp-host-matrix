# Measured outcomes

[Project](../../README.md) · [Disconnection page](../MATRIX.en.md) · [Glossary](../../docs/EVIDENCE-POLICY.md#glossary)

Selected outcomes from pinned client builds and the local synthetic OAuth/MCP fixture. This summary is separate from the documentation matrix; the fixture served both authorization-server and MCP resource-server roles.

The fixture used synthetic tokens, an access lifetime of 120 s, refresh tokens always issued, and a 30 s slow tool call. Client builds were pinned. No real provider or model calls and no new vendor login were used; some isolated profiles reused existing dedicated account state, and Cascade used an offline UserStatus response from the earlier connectivity bench described in *Remote MCP client options without a local bridge*. The six paths are the five hosts that connected natively on that bench plus the bridge under Claude Code. The other seven documented hosts were not included in this revocation bench; Continue CLI was tested on the earlier connectivity bench. Each path had the primary profile without DCR shown below and a DCR-ON profile.

The design called for the action about 5 s after the slow call started, before its effect committed. That timing was not met in every window, so in-flight observations remain specific to each window and do not support one uniform in-flight conclusion for the whole set. "The effect" means the slow call's commit at the MCP resource server. UI actions were performed by the author or by scripted pointer input under the author's authorization; CLI and file-edit operations are named separately. Exact click times are not always known. ACK denotes the observer's recorded action evidence, such as persisted configuration, command completion or a revocation request; it is not necessarily a host-native acknowledgement. Each primary window remained open at least 60 s after that ACK.

The controller replayed the same prior refresh token before and after the action with the profile's required client credentials. This controller probe does not describe all client-initiated refresh traffic. "Prior refresh token after" is the outcome of that replay after the action: "token issued" means a new access token was returned; "refused" means the provider answered `invalid_grant`. "Revocation request" means a POST to the authorization server's revocation endpoint, the RFC 7009 operation. The saved fixture implementation declares `revocation_endpoint` in its metadata. The journals record successful authorization-server metadata requests, but do not retain those response bodies; this declaration is established from the implementation, rather than a saved body capture. Endpoint availability alone does not establish an obligation to invoke it on every disconnect action. Here, "none" means no matching request observed within the named healthy window, not over an unlimited period.

| Client | Version | Primary profile | Disconnect action | Revocation request | Prior refresh token after | DCR registration DELETE |
|---|---|---|---|---|---|---|
| VS Code | 1.142.0 | PUBLIC-NODCR | Uninstall | none | token issued | none |
| Zed | 1.24.4 | CONFIDENTIAL-NODCR | Uninstall | none | token issued | none |
| Cascade | 3.10.67 | PUBLIC-NODCR | server Toggle | none | token issued | none |
| Cursor | 3.24.18 | CONFIDENTIAL-NODCR | server Toggle | none | token issued | none |
| Claude Code | 2.1.306 | PUBLIC-NODCR | mcp remove | none | token issued | none |
| Claude Code → mcp-remote | 2.1.306 / 0.15.2 | PUBLIC-NODCR | config removal and session exit | none | token issued | none |

In both tables the DCR registration DELETE column comes from a DCR-ON window; the other columns of the main table use the non-DCR profile in Primary profile. Each main row therefore combines two windows of one client path.

| Action | Client | Revocation request | Prior refresh token after | DCR registration DELETE |
|---|---|---|---|---|
| Disable | VS Code 1.142.0 | none | token issued | none |
| `claude mcp logout` | Claude Code 2.1.306 | sent (access and refresh) | refused | none |
| Clear authentication | Claude Code 2.1.306 | sent (access and refresh) | refused | none |
| server entry removed from mcp.json by file edit | Cursor 3.24.18 | none | token issued | n/a |
| server entry removed from the source config by file edit | VS Code 1.142.0 | none | token issued | n/a |

Disable, logout and Clear authentication each have one selected window per profile; each file-edit variant has one non-DCR window, so its registration DELETE is n/a. Clear authentication used a separate native session on the same profile and grant, so it is not a same-session cancellation test. The VS Code file-edit variant reused a trusted profile; it is not native Uninstall or an independent fresh-profile repetition.

Across five native hosts and one bridge path, none of the 12 base windows produced a revocation request, and the prior refresh remained usable in a separate controller replay. No registration DELETE was observed in the six DCR-ON base windows. Logout and Clear authentication produced revocation requests and subsequent refusal of the prior refresh. The selected set contains 12 base windows, 8 operation variants and 3 additional healthy timing windows: 23 run IDs. Replays used the original profile's required credentials; use by another party was not tested.

Native Cursor Remove was not measured in the pinned build's MCP panel. In the retained VS Code DCR window the effect committed before observer ACK. The test provider let accepted work finish, so completion after transport close alone does not establish a cancellation defect. Store observations were limited: a bridge point control found the refresh token still in its cache; Cascade's exact SQLite entry retained its opaque hash; Claude authentication controls had bounded before/after receipts, while the remove rows had only a later after-read. Zed's credential entry was not located. An unchanged opaque entry does not establish a usable token or access from another profile. Process snapshots around 10 s are bounded observations, not a lifetime or deletion audit. These observations do not assess compliance with a product's stated contract.

The [public results](RESULTS.json) list all 23 selected run IDs, the 3 timing windows, outcomes and raw verdict SHA-256 values, without tokens or private local paths. The [deidentified R01 receipt](receipts/R01.json) exposes selected saved observations and controls. Full originals and the fixture implementation remain author-held and may be requested through the [repository issue tracker](https://github.com/playb0t/mcp-host-matrix/issues); this is not a self-contained rerun.
