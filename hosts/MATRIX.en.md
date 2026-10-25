# Remote MCP client options without a local bridge

[MCP Host Matrix · R01-R06](../matrix/MATRIX.en.md) · [Project](../README.md) · [Glossary](../docs/EVIDENCE-POLICY.md#glossary)

<details>
<summary>Snapshot and source metadata</summary>

Documentation read: 21 October 2026. Measured builds and profiles are listed with each result.

The read date applies to the inspected documentation; runtime results are listed separately.

</details>

Author: Alex Gercog · Repository: [playb0t/mcp-host-matrix](https://github.com/playb0t/mcp-host-matrix) · Related page: [Remote MCP disconnection and stored authority](../disconnect/MATRIX.en.md).

A local bridge here means a process the client starts on the user's machine to reach a remote server, for example `mcp-remote`; this page lists what each client documents for connecting without one.

This page lists what each client documents and what connected on a bench; it does not recommend a configuration or estimate a vendor's cost.

DCR is dynamic client registration; CIMD is Client ID Metadata Documents (a URL as the client id); both as defined in the [MCP authorization specification, revision 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization).

This table covers the documented options of eleven clients. A direct route is conditional on the provider accepting the client registration, token method, callback, scopes and network path.

Public and secret-required OAuth clients are separate cases. Static request headers do not replace delegated OAuth when the provider requires it. "Not documented" refers to the inspected sources, not an assertion that a feature is absent.

| Client | Docs / version | Remote transport | DCR | CIMD | Static OAuth client | Request headers | OAuth callback | Bridge recipe | Automatic bridge | No-DCR gap | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [Cursor](https://cursor.com/docs/mcp) | Unversioned | HTTP/SSE; url | Mentioned; static alternative described | Not documented | auth.CLIENT_ID/CLIENT_SECRET; env | headers; env interpolation | Desktop 8787; separate cloud callback | Not documented in checked pages | Not documented | Match client callback and provider OAuth details | Conditional direct; public and secret clients both documented |
| [Claude Code](https://code.claude.com/docs/en/mcp) | Unversioned; callback version caveat | HTTP/SSE; `type`, `url` | Documented | Documented | --client-id/--client-secret; stored secret | headers/--header/headersHelper | Random; --callback-port | Not documented in checked pages | Not documented | Register correct localhost/127.0.0.1 callback | Conditional direct; public and secret clients both documented |
| [Claude Desktop](https://claude.com/docs/connectors/custom/add-unlisted) | Hosted connector; local JSON separate | Streamable HTTP/legacy SSE; URL UI | Documented | Documented with metadata conditions | Own ID/optional secret; connection UI | Request headers beta; org gate; up to four headers | Fixed hosted callback | Not documented in checked pages | Not documented | Cloud reachability; local process is separate | Conditional hosted direct; local JSON unresolved |
| [VS Code (GitHub Copilot)](https://code.visualstudio.com/docs/agents/reference/mcp-configuration) | VS Code format; other harnesses separate | HTTP/SSE; `servers.type`, `url` | Not documented in inspected reference | Not documented | oauth.clientId; secret field not documented | headers; input variables | Not documented in inspected reference | Not documented in checked pages | Not documented | Public ID exists; secret-required path unresolved | Public: conditional direct; secret: unresolved |
| [Windsurf (Cascade)](https://docs.devin.ai/desktop/cascade/mcp) | Cascade panel of the Windsurf app; Devin Local has a separate configuration | HTTP/SSE; serverUrl or url | Not documented separately from OAuth | Not documented | Static client ID/secret not documented | headers; env/file interpolation | Not documented | Not documented in checked pages | Not documented | Preregistration/CIMD unknown for Cascade | OAuth unresolved; headers are separate |
| [Zed](https://zed.dev/docs/ai/mcp) | Unversioned; native Agent scope | Remote url; transport detail not documented | Not documented; source inspected separately | Not documented; source inspected separately | Preregistered ID/secret not documented | headers; Authorization | Not documented; source detail separate | Not documented in checked pages | Not documented | Registration/callback detail not documented | OAuth unresolved; header path conditional |
| [Cline](https://docs.cline.bot/mcp/mcp-overview.md) | Changelog 4.1.7; CLI/Desktop differ; [Changelog](https://raw.githubusercontent.com/cline/cline/e9dafbb764d0cb9acb4ef93a956ae72c350b3952/CHANGELOG.md) | streamableHttp/sse; `url`, `type` | Contrasted with preregistration | Not documented | Preregistration documented; exact keys source-only | headers; CLI --header | Not documented for selected surface | Not documented in checked pages | Not documented | Support exists; setup/callback details incomplete | Preregistration documented; exact profiles unresolved |
| [Goose](https://goose-docs.ai/docs/getting-started/using-extensions/) | Unversioned; current extensions docs | `streamable_http`, `uri`; SSE unsupported | Documented | Documented | client_id/client_secret_key; secret store | headers | Ephemeral 127.0.0.1; GOOSE_OAUTH_CALLBACK_PORT | Not documented in checked pages | Not documented | Check provider token method and redirect details | Conditional direct; public and secret clients both documented |
| [Codex CLI](https://developers.openai.com/codex/mcp.md) | Unversioned; CLI docs snapshot | Streamable HTTP; `url`; SSE not documented | Documented | Documented | oauth.client_id/client_secret; config.toml | http_headers/env_http_headers/helper | Ephemeral/configurable; issuer-dependent path | Not documented in checked pages | Not documented | Register displayed callback; token method must match | Conditional direct; public and secret clients both documented |
| [ChatGPT (apps / connectors)](https://developers.openai.com/api/docs/guides/custom-mcp-server.md) | Hosted plugins/custom MCP portal | Streaming HTTP/SSE; Server URL | Documented | Documented | Provided client ID; secret through portal | Schema has headers; portal does not accept fixed credentials as a connection route | Fixed/ID-specific hosted callback | Not documented in checked pages | Not documented | Manifest and portal paths differ | Conditional OAuth direct; static-header path unresolved |
| [Continue CLI](https://docs.continue.dev/customize/deep-dives/mcp) | @continuedev/cli 1.5.47 | streamable-http/sse; `url`, `type` | Native CLI detail not documented | Native CLI detail not documented | Native CLI ID/secret not documented | requestOptions.headers | Native CLI callback not documented | No prose recipe found; source fallback exists | Source: interactive auth-error fallback | Auto bridge does not prove no-DCR compatibility | OAuth unresolved; header path conditional |

## Measured outcomes

The Verdict column above grades what each vendor documents; this section records what connected on the bench. A client can read "unresolved" above and "connected" here when the path exists but is not documented.

The bench used pinned client builds and a synthetic loopback OAuth/MCP provider. No real provider or model calls were made. Outcomes include failures and prevented bridge attempts. Account login for Cursor and Cascade was performed by the author in isolated profiles.

For Continue CLI a stub `npx` placed first on PATH recorded the launch arguments and exited without starting anything; "launch prevented" means the stub caught the call, not that the client declined to launch.

| Client / OS | PUBLIC-NODCR | CONFIDENTIAL-NODCR | CIMD-NODCR | DCR-ON |
|---|---|---|---|---|
| VS Code 1.142.0 / Windows | connected | clientId-only did not connect at token (401 invalid_client) | connected, metadata cache | connected |
| Continue CLI 1.5.47 / Windows | bridge launch attempted after 401; launch prevented | bridge launch attempted after 401; launch prevented | bridge launch attempted after 401; launch prevented | bridge launch attempted after 401; launch prevented |
| Zed 1.24.4 / Linux (WSL2) | did not connect: UI requires a client secret; no authorize request | connected | connected, metadata cache | connected |
| Cascade 3.10.67 / Linux (WSL2) | connected | clientId-only did not connect at token (401 invalid_client) | connected, configured metadata URL | connected |

An additional native client-secret UI configuration connected in VS Code CONFIDENTIAL-NODCR. Continue headless PUBLIC-NODCR stopped at the authorization challenge without attempting the bridge. No bridge was executed.

| Positive control | Profile | Outcome |
|---|---|---|
| Claude Code 2.1.306 | PUBLIC-NODCR | connected |
| Cursor 3.24.18 / Windows | CONFIDENTIAL-NODCR | connected; client_secret_basic; localhost:8787/callback |

Cursor completed one authorization grant and native initialize/tools/list from two existing editor hosts. This counts as one control run. Provider PKCE S256, resource binding, secret validation, event-time TCP ownership and target-process ancestry passed. The author performed account login and the synthetic MCP Authenticate click in isolated profiles.

The 16 core outcomes comprise 9 connections, 3 configuration-specific failures and 4 prevented bridge attempts. Both positive controls passed. With the VS Code client-secret UI variant and Continue headless control, there are 20 qualified runtime receipts, including failures and prevented attempts.

A qualified runtime receipt records HTTP `initialize` and `tools/list` from a client PID matched to the TCP connection owner, or the last request before a failure or intercepted launch, for each run. UI-based failure interpretations are retained with the request receipt; Zed PUBLIC-NODCR made discovery requests but no authorize request.

The bench summary (`bench/BENCH.en.md`, `bench/RESULTS.json`, `bench/CONTINUE-ARGV-CHECK.json`) sits next to this page; connectivity per-run originals remain author-held and available on request. [Selected deidentified receipts](../matrix/receipts/README.md) cover the separate R01-R06 directions.

Direct no-DCR paths were measured for VS Code, Zed and Cascade. Continue attempted the bridge in all four interactive profiles, including DCR-ON; a stub intercepted the launch. Its direct OAuth compatibility remains unresolved. A failed clientId-only configuration does not establish that every confidential configuration is unsupported.

CIMD limits: VS Code/Zed used a captured metadata document at the local authorization server. Cascade used a manually configured synthetic HTTPS metadata URL with verified live loopback fetch. Automatic discovery of a built-in client identity was not established. Linux results do not establish native Windows behavior.

### Cursor

Cursor documents static credentials in auth, including "CLIENT_SECRET". Desktop and cloud use different callbacks; register the one for the surface you use. [Documentation](https://cursor.com/docs/mcp).

On the bench the client presented callback `http://localhost:8787/callback` and token method `client_secret_basic` for CONFIDENTIAL-NODCR.

### Claude Code

Claude Code documents "--client-id" and an optional secret. Set the callback port when your provider needs a pre-registered redirect, and check the version-specific hostname note. [Documentation](https://code.claude.com/docs/en/mcp).

On the bench the client presented callback `http://localhost:51530/callback` and token method `none` for PUBLIC-NODCR; this run explicitly configured callback port 51530.

### Claude Desktop

Hosted custom connectors accept an "OAuth client" supplied by the user. Connections originate from Anthropic; static request headers have a separate beta gate. Local JSON is a different connection path. [Documentation](https://claude.com/docs/connectors/custom/add-unlisted).

### VS Code (GitHub Copilot)

The reference lists "clientId". It does not list a client-secret field in the inspected OAuth object, so the secret-required case remains open without proving a missing feature. [Documentation](https://code.visualstudio.com/docs/agents/reference/mcp-configuration).

On the bench (1.142.0, Windows) the public client connected without DCR; the clientId-only secret configuration did not connect at token (401 invalid_client); a client secret entered through the editor's own command, "Set OAuth Client Secret" (MCP category), connected. The pinned source marks this action `f1: false`; it is not a standalone global Command Palette entry. The command is not in the inspected reference.

On the bench the client presented callback `http://127.0.0.1:33418/` and token method `none` for PUBLIC-NODCR and CIMD-NODCR, or `client_secret_post` for the CONFIDENTIAL-NODCR secret UI variant.

### Windsurf (Cascade)

Cascade supports "serverUrl or url" and headers. Its OAuth registration details remain undocumented in the inspected pages. Devin Local uses a separate configuration. [Documentation](https://docs.devin.ai/desktop/cascade/mcp).

On the bench (3.10.67, Linux/WSL2) the public client connected with `oauth.clientId` without DCR; the clientId-only secret configuration did not connect at token; a manually configured metadata URL connected. The installed schema has no secret field.

On the bench the client presented callback `http://127.0.0.1:8765/auth/callback` and token method `none` for both PUBLIC-NODCR and CIMD-NODCR.

### Zed

Zed's remote example includes "headers" and general OAuth. DCR, CIMD and callback details found in source are kept separate from the documentation verdict. [Documentation](https://zed.dev/docs/ai/mcp).

[Source](https://github.com/zed-industries/zed/blob/70277c0193302af44978c8c784d1d78028cfe8f2/crates/context_server/src/oauth.rs), [Source](https://github.com/zed-industries/zed/blob/70277c0193302af44978c8c784d1d78028cfe8f2/crates/context_server/src/transport/http.rs).

On the bench (1.24.4, Linux/WSL2) the secret and metadata-URL clients connected without DCR; the public preregistered client did not connect: the UI requires a client secret and sends no authorize request.

On the bench the client presented callback `http://127.0.0.1:43997/callback` and token method `client_secret_post` for CONFIDENTIAL-NODCR; for CIMD-NODCR it presented `http://127.0.0.1:36555/callback` and `none` (loopback, random port for each flow).

### Cline

The changelog says "pre-registered OAuth clients". Exact keys and callback behavior were traced in source; those details are not presented as documented configuration. [Changelog](https://raw.githubusercontent.com/cline/cline/e9dafbb764d0cb9acb4ef93a956ae72c350b3952/CHANGELOG.md).

[Source](https://github.com/cline/cline/blob/e9dafbb764d0cb9acb4ef93a956ae72c350b3952/apps/vscode/src/services/mcp/McpOAuthManager.ts), [Source](https://github.com/cline/cline/blob/e9dafbb764d0cb9acb4ef93a956ae72c350b3952/apps/cli/src/wizards/mcp/oauth.ts).

### Goose

Goose provides "client_secret_key" and resolves it through environment entries or its credential store. Public clients may omit the secret. A fixed callback port has its own environment variable. [Documentation](https://goose-docs.ai/docs/getting-started/using-extensions/).

### Codex CLI

Pre-registered credentials are saved in config.toml. The reference exposes "oauth.client_secret"; register the callback shown by the CLI because its path depends on issuer support. [Reference](https://developers.openai.com/codex/config-reference.md). The MCP page linked in the table describes transport and OAuth flows; this configuration reference defines the credential keys.

### ChatGPT (apps / connectors)

The provided-client flow keeps the secret in the portal; the plugin package manifest lists "client_secret_basic" and other token methods. Manifest support for headers does not establish a portal connection route. [Reference](https://developers.openai.com/plugins/build/plugins.md). The custom-MCP guide linked in the table describes the server connection flow; this plugin-package reference defines manifest auth methods and header fields.

### Continue CLI

The 1.5.47 source contains "mcp-remote" in an interactive fallback after errors classified as authentication failures. The predicate includes 401, 405 and Unauthorized text; headless excludes the branch. On the bench (1.5.47, Windows) the launch was measured: after the first 401 the CLI attempted to start `mcp-remote` unpinned in all four interactive profiles, DCR enabled included; the call was caught by the bench's stub `npx`; headless stopped at the authorization challenge without attempting it. [Source](https://github.com/continuedev/continue/blob/d3f60ba9dd3fb5bfd3c91d6fbb41ce1aa768db45/extensions/cli/src/services/MCPService.ts) · [Authentication-error predicate](https://github.com/continuedev/continue/blob/d3f60ba9dd3fb5bfd3c91d6fbb41ce1aa768db45/extensions/cli/src/services/mcpUtils.ts#L9-L19).

[Records on the `mcp-remote` package, in the advisories repository](https://github.com/playb0t/mcp-remote-oauth-security/tree/main/advisories)
