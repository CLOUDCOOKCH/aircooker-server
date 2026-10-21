# ADR 009: Minimal Alpine Python runtime

Status: accepted for development, 2026-10-21; supersedes the Debian runtime packaging only.

The Debian 13 image retained 44 HIGH package/advisory matches across eight util-linux
advisories without published fixes. The application has no mount/login/host-administration
requirement. Removing essential Debian packages or suppressing findings would weaken
maintainability or the release gate. Choose the official Python 3.12.14/Alpine 3.24 image,
locked to the multi-architecture index digest
`sha256:4c47124a8391cb7a9f571164147d154777cf012a4ece5f86097130d7a4478111`.

The base includes timezone data and CA certificates, SQLite 3.53.4 and OpenSSL 3.5.8.
No compiler, external queue or new runtime service is added. The same hashed dependency
lock installs musllinux wheels; builder and runtime share the same libc/base. Preserve
UID/GID 10001, read-only operation, dropped capabilities, `/data` layout, WAL persistence,
health checks and the API. Existing SQLite volumes use the same file format; never downgrade
SQLite without testing and a consistent backup.

The linux/amd64 candidate passed the complete real-HTTP Docker smoke script, including
restart/revocation, media, AI configuration encryption, sync proofs and export/restore.
Trivy 0.70.0 with a freshly downloaded database reports zero HIGH/CRITICAL findings without
ignoring unfixed issues. This is finite advisory coverage, not proof of no vulnerabilities.
It warns that Alpine 3.24 is absent from its static EOL table; OS/package detection and the
3.24 vulnerability repository are used. Keep scanner and base versions under review.

Native AMD64/ARM64 test, Docker smoke and security matrix jobs now validate the packaging.
ARM64 is not claimed verified until those jobs pass. Future dependencies must supply
compatible wheels on both architectures or receive an explicit build/deployment decision;
do not introduce unreviewed compilers/downloads into the production image.
