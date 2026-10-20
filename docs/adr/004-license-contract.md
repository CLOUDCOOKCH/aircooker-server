# ADR 004: Apache-2.0 and independently pinned API contracts

Status: accepted for development.

Use Apache-2.0 in both repositories: permissive reuse plus an express patent grant fits an
independent self-hosted application. The Bring SDK is MIT and can remain a replaceable
dependency without relicensing project code. This is an engineering recommendation, not a
legal opinion; a complete transitive license inventory remains a release gate.

The server owns generated OpenAPI v1. A committed snapshot must match runtime generation.
The iOS repository vendors its own exact contract copy and SHA-256, rather than requiring a
third shared-code repository. Contract fixtures verify native codecs. Server and iOS may
release independently when API-major and sync-protocol remain compatible. A breaking API
must use a new namespace and keep an explicit client support/migration policy.
