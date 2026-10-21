# mealf identity and compatibility

The product was renamed from aircooker to **mealf** by the user on 2026-10-21. The
approved identity comprises a flirty peach icon and a lowercase mealf wordmark. Keep the
existing glass interface, system appearance, food content and accessible controls.

The exact source files are named `mealf-flirty-peach-logo.png` and
`mealf-flirty-peach-wortmarke.png`. Their images are visible in the conversation, but the
original files were not mounted or supplied with downloadable file identifiers. The local
Windows file paths cannot be read by the cloud workspace. Do not recreate, trace, regenerate
or claim to have installed these images. The previous application icon remains until the
original PNG files are made available. Wordmark-image placement and new install icons are
therefore pending; the current delivery changes product names only.

The PWA, console, English/German onboarding, browser title, manifest names, dependency
notices, download filenames and native app/extension display copy use mealf. Household
names chosen by users are preserved. The PWA manifest's `/app/` identity/start URL stays
stable. Existing installations may need the normal explicit application update and an
OS/browser refresh before their displayed name changes.

Internal compatibility names intentionally remain unchanged:

- GitHub repository URLs and local package/module/build-target names.
- SQLite filenames, IndexedDB and localStorage keys, BroadcastChannel/Web Locks names.
- Cookies, CSRF/API headers, native bundle IDs, App Groups, Keychain services, deep links
  and notification/widget identifiers.
- Versioned household/browser recovery formats, import receipts and Bring! ownership IDs.
- The service-worker cache namespace, whose existing cleanup must still recognise old caches.

These identifiers are not the product's display name. Changing them without migration could
lose access to offline work, duplicate owned external items or invalidate working sessions.
Repository/build identifier renames can be handled separately with explicit migration and
redirect validation. Historical validation records and pinned native OpenAPI files retain
their exact tested source names. The current server's API documentation title uses mealf;
that metadata change does not change its wire fields or compatibility version.
