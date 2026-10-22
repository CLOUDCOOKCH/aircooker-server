# Personal ChatGPT import UI finish review

Date: 2026-10-22. Scope: the optional personal ChatGPT connection in PWA Settings, its local-computer helper instructions, and the personal recipe-text import path through editable review and explicit Save. This is a narrow extension of the established interface. It introduces no new visual world, approved comp, seed or design card.

**Disposition: ship within the reviewed UI scope.** The fresh independent finish reviewer returned persistence **pass** and TYPE, MATERIAL and GROUND **match**, including Settings, helper instructions, import and review continuity. Phone wrapping was accepted as a responsive adaptation. No material UI fixes remain at this scope. This records the supplied independent review and browser evidence; the documentation handoff inspected sources and opened all four captures without rerunning the workflow. It is neither production acceptance nor a security audit.

## Authority and inspected sources

The incumbent [product requirements](../../PRODUCT.md), [design reference](../../DESIGN.md), [project-owned design snapshot](../../.impeccable/design.json) and [PWA surface brief](../../.impeccable/surfaces/pwa.md) remain authoritative. The extension preserves system typography, semantic theme roles, solid reading/editing surfaces, glass navigation and the original artwork. Setup, privacy, failure and recovery copy stays literal.

Source inspection covered `frontend/src/ChatGPTSettings.tsx`, `frontend/src/Imports.tsx`, the ChatGPT English/German copy in `frontend/src/i18n.ts`, and the related Settings, pairing, command and import rules in `frontend/src/styles.css`. The [setup and behavior guide](../CHATGPT.md) owns technical details and functional limits. Older design records include historical green/system-only descriptions, old publication status and older component/layout snapshots. That documentation drift is acknowledged here and preserved; it was not repaired or adopted as a new design constraint.

## Genuine browser evidence

All captures below were opened with `view_image`. They show synthetic household/account/recipe data from real Chromium renders. The pairing value and local origin are fixture values, not real connection credentials. Desktop images are actual section crops from a 1440px-wide page; the connected phone image is a section crop from a 390px-wide page. The import image is full-document at a 390×844 viewport, so fixed navigation retains its viewport position within the longer image.

| Capture | Image pixels | Reviewed state |
| --- | --- | --- |
| [pairing-desktop.png](../screenshots/chatgpt/pairing-desktop.png) | 539×645 | English download/run/paste instructions, selectable one-use code, Copy, Cancel and waiting feedback |
| [connected-desktop.png](../screenshots/chatgpt/connected-desktop.png) | 539×560 | English connected account/model, model choice, personal-session confirmation, reconnect/disconnect and allowance disclosure |
| [connected-phone-de-dark.png](../screenshots/chatgpt/connected-phone-de-dark.png) | 350×669 | German dark connected section, wrapped ownership and allowance copy |
| [import-phone-de-dark.png](../screenshots/chatgpt/import-phone-de-dark.png) | 390×1298 | German dark personal-account selection, text-only disclosure, destination, recipe source, checked background consent, preview action and a saved import |

SHA-256 of the reviewed bytes:

```text
pairing-desktop.png          1b4451b8783882919672a9bba8cad2041cce968936bf9829bc41ea4356951daa
connected-desktop.png        99a2fd26e74681941c263b620a44ac408e3978cfdb7a2683eb771710388f261c
connected-phone-de-dark.png  fd56f1587a2a69064f0b461ccd84b01b9d51ebd6bd97f49d65a2d746557321af
import-phone-de-dark.png     13324b71d2fb1748ad901bce657cc46c2ee8bada3920e9601f5ae9bb6ad7d577
```

## Reviewed behavior and continuity

- **Settings and helper:** the bounded solid Settings group leads with personal-session ownership, then connection/account/model state. Pairing provides ordered download/run/paste instructions for a Windows-friendly Python standard-library helper on the browser computer, a copyable one-use code, expiry/privacy guidance and cancellation. The command and account text permit wrapping. Connected controls distinguish model selection, confirmed personal use, reconnect and destructive disconnect. A usage link and literal eligibility/allowance warning avoid promising unlimited access or automatic paid API fallback.
- **Import and approval:** the personal account choice appears in Link or text. It presents recipe text, account/model/destination and explicit consent to send that text and finish this import after the app closes. Photos, attachments and videos are excluded from this first personal path. Submission requires connected status, a model, nonempty text and consent. The durable queued task binds the selected connection/model and approval. Results use the existing editable preview and explicit Save; a prepared preview alone creates no recipe. Reviewed recipes become shared household content; the session-owned connection is not pooled across household members. Encrypted server credential handling is a functional implementation claim documented in the guide, not independently audited by this UI review.
- **Responsive and state clarity:** German dark phone controls and copy wrap within the reviewed width. The long usage link spans lines acceptably. The full-document import image places the fixed navigation over one document band; that capture position alone does not establish permanent obstruction. Source uses native labelled controls, status/alert feedback, offline/busy guards, pairing expiry, copy fallback, reconnect guidance and unconfirmed remote-revocation wording. Not every error, loading, model-catalog or review-editor state is pictured in these four images.

## Verification and limits

The inspected local `build/chatgpt-browser.log` reports a pass for the real PWA/server flow, standalone helper loopback callback, signed-token verification, personal model selection, English desktop/German dark phone checks with Axe, explicit reviewed saving, and offline queued import/reload replay. OpenAI identity/inference responses and HTTPS helper-origin routing are explicit synthetic doubles. Those results do not establish live ChatGPT subscription eligibility, real allowance/extraction, or production connectivity.

The context launcher and automated detector were unavailable; no passes are claimed. The independent finish review is a separate supplied review, not an unavailable launcher/detector result. Actual Windows helper execution, physical iPhone/Safari behavior and exact-source CI/device evidence remain unverified here. Screenshots and Axe do not establish complete keyboard, screen-reader, motion, text-enlargement or accessibility acceptance. No further UI change is required by this bounded review; complete-product and live-service acceptance remain separate.
