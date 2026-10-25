# Native remote MCP host bench

[Project](../../README.md) · [Connectivity page](../MATRIX.en.md) · [Glossary](../../docs/EVIDENCE-POLICY.md#glossary)

Measured on pinned client builds with a synthetic loopback OAuth/MCP provider. No real provider or model calls were made. Outcomes include failures and prevented bridge attempts. Account login for Cursor and Cascade was performed by the author in isolated profiles.

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

Direct no-DCR paths were measured for VS Code, Zed and Cascade. Continue attempted the bridge in all four interactive profiles, including DCR-ON; a stub intercepted the launch. Its direct OAuth compatibility remains unresolved. A failed clientId-only configuration does not establish that every confidential configuration is unsupported.

CIMD limits: VS Code/Zed used a captured metadata document at the local authorization server. Cascade used a manually configured synthetic HTTPS metadata URL with verified live loopback fetch. Automatic discovery of a built-in client identity was not established. Linux results do not establish native Windows behavior.

Receipt locators in the structured results are relative references to author-held sources, not bundled files. The primary result uses `receipt`; `interpretation_receipt` and `traffic_receipt` identify distinct supporting artifacts. All locators use forward slashes.
