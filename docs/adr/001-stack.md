# ADR 001: Python/FastAPI modular monolith

Status: accepted for development, 2026-10-20.

Python/FastAPI offers runtime request validation and generated OpenAPI, built-in SQLite,
mature content parsers and compatibility with the MIT-licensed `bring-api` reference.
TypeScript offers strong editor tooling and web UI reuse, but would require runtime schema
validation and a different Bring implementation. Go offers small static binaries and good
concurrency, but adds work around schema generation, parser integration and SQLite driver
selection. None needs microservices for a single household.

Choose Python 3.12/FastAPI, Pydantic v2, standard `sqlite3` and Uvicorn. Restrict deployment
to one process with one durable worker. Keep connectors behind interfaces. Use native
Swift/SwiftUI and Apple frameworks for UI, credentials, extensions and notifications.
The small Swift core uses SQLite directly so outbox writes and entity edits share an
explicit transaction. This trades some storage adapter code for precise sync guarantees.

Consequences: larger runtime than Go, explicit limits needed around parsing and Argon2,
and background work must not block the API event loop. Dependencies and images are locked.
