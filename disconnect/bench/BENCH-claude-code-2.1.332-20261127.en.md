# Measured outcomes: Claude Code 2.1.332 on a separate bench

[Project](../../README.md) · [Disconnection page](../MATRIX.en.md) · [Glossary](../../docs/EVIDENCE-POLICY.md#glossary)

This separate bench ran on Windows on 27 November 2026. A synthetic loopback fixture served as the OAuth authorization server and the MCP resource server. The fixture issued access tokens with a 3600 s lifetime and did not rotate refresh tokens. The two modes advertised the revocation endpoint in either the RFC 8414 metadata or the OpenID discovery document. Each window used an isolated client profile, with no real account or model call.

## Client windows

The [disconnection page](../MATRIX.en.md#separate-bench-claude-code-21332-27-november-2026) lists all 12 windows. Each combination of discovery mode, public OAuth client profile (preregistered or DCR), and action (`mcp remove`, `mcp logout`, or Clear authentication in `/mcp`) was measured once. The fixture observed each window for 60 s after the action. A separate controller check used the original grant's client identifier and the same refresh token before and after each action. The fixture journal distinguishes controller requests from Claude Code requests.

The provider accepted the prior refresh token before the action in all 12 windows. With RFC 8414 metadata, the bench recorded no revocation request after `remove` and the prior refresh token was accepted in both profiles. After `logout` and Clear authentication it recorded two revocation requests per window, for the access and refresh tokens, and the provider returned `invalid_grant` on the subsequent refresh. In all six OpenID-only windows, the bench recorded no revocation request and the provider accepted the prior refresh token. The bench recorded no registration DELETE in any of the six DCR windows.

The saved views of the local credentials file show the server entry gone after `remove` and `logout`. After Clear authentication the entry remained without token values. The inspection followed a reconnection attempt, which may account for fields in the remaining entry.

## Fixture controls

Two separate controls ran without Claude Code. In `c01`, OpenID discovery returned HTTP 200 with the advertised endpoint, and RFC 8414 discovery returned HTTP 404. In `c02`, RFC 8414 discovery returned HTTP 200 with the endpoint, and OpenID discovery returned HTTP 404. In each mode, the fixture accepted the refresh token before revocation, returned HTTP 200 at the advertised revocation endpoint, and then refused the same refresh token with `invalid_grant`. These controls are separate from the 12 client windows.

## Evidence and limits

The journal records requests handled by the fixture. The client journals preserve discovery response status codes. Discovery response bodies were retained for the separate controls. The observations leave the internal cause in Claude Code undetermined. The scope is one Windows build on this synthetic fixture. Confidential clients, updates, and in-flight cancellation were outside it.

The [public results](RESULTS-claude-code-2.1.332-20261127.json) list the client windows and fixture controls, with SHA-256 digests of the saved records. The JSON uses LF line endings. The underlying records remain author-held. The results contain no token values.
