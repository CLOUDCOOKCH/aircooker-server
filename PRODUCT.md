# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Delegated by the user's master development prompt. Keep Python/FastAPI, SQLite WAL and
one Docker container. Build the primary browser client with React and TypeScript, using
Vite only at build time and IndexedDB for durable local records/outgoing mutations.
The backend owns the canonical versioned OpenAPI contract. No third mandatory repository.

## Users

Households planning breakfast, lunch and dinner together, using phones in the kitchen and
larger screens when planning the week. One shared household account, separate device sessions.

## Product Purpose

Import and edit recipes, plan meals, reuse leftovers, exclude pantry staples and send
required ingredients to an existing Bring! list. The self-hosted backend owns external
integrations; offline edits persist locally and reconcile in server-accepted order.

## Operating Context

User explicitly chose PWA-first on 2026-10-21 and does not own a Mac. Preserve the independent
native iOS repository for later. The browser app installs from an HTTPS server URL without
App Store/TestFlight distribution. Keep the administration console focused on administration.

## Capabilities and Constraints

Preserve the master meal-planning/recipe/privacy/security requirements. On iPhone, replace
incoming native sharing with paste/import and optional documented Shortcuts; native widgets
are deferred, reminders use opt-in connected Web Push, and automatic sync relies on opening
the PWA. Offline caching requires an initial download and browser-storage handling. Do not
claim full native feature parity or bypass source/Bring restrictions. No proprietary hosted
account, payments, analytics or tracking. Third-party AI is optional and needs explicit consent.

## Brand Commitments

aircooker. The user approved an iOS-like glass design and requested the same design in the
PWA: effortless controls, food-led content and uncluttered navigation. Preserve the approved
visual decisions; the private design references were supplied for the conversation only.

## Evidence on Hand

Existing backend has tested real persistence, auth, imports, planning, reconciliation and
exports; external Bring/AI are unverified. The native app builds with Xcode 26.6 and passes
demo onboarding/edit/restart/exit plus German light/dark tests. Native core has 90 tests.
The approved glass image in the conversation is an illustrative concept, never a running
app capture. Original icon and food illustration assets exist in the native repo; use
illustrative food only in a clearly separated demo, never seed household data implicitly.

## Product Principles

- Preserve unsynchronised local work and make its status visible.
- Preview imports and suggestions before explicit approval.
- Modify only identifiable aircooker-owned Bring! items.
- Keep deployment simple and external dependencies replaceable.
- Distinguish tested code, external verification and unfinished work.

## Accessibility & Inclusion

English and German, system light/dark appearance, scalable text, keyboard and screen-reader
controls, sufficient contrast and reduced-motion/transparency fallbacks. Provide explicit
move/copy controls alongside drag-and-drop. Preserve imported recipe language.
