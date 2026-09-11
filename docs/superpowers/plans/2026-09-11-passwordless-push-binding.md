# Jerkgram Passwordless Push Binding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Telegram Web K login-token/2FA pairing dependency with a passwordless Web Push binding: the Home Screen PWA creates a browser `PushSubscription`, native Jerkgram validates it and registers it on the already-authorized primary Telegram account with `account.registerDevice(token_type = 10)`.

**Architecture:** Keep the existing Telegram Web K service worker and all proven notification presentation/tap-routing patches unchanged. Add a small pure binding encoder on the web side, a passwordless setup/status surface that talks only to the browser Push API, a narrow TelegramCore type-10 register/unregister helper, and a strict native `/register` + `/unregister` deep-link bridge layered before the existing `/open` click bridge. Fresh PWA installs never create a Telegram Web K authorization. Existing signed-in PWA installs are not logged out or revoked during this migration.

**Tech Stack:** Telegram Web K pinned at `e9428f2a90f73d750f16a0b85817820516466364`, browser Push API / Service Worker, SolidJS auth card shell, vanilla JavaScript helper, Telegram iOS 12.9.2 at `6ad963e5b62d354da79040f388ae2b9132fb17b8`, Swift/SwiftSignalKit/TelegramCore, Python source patchers/verifiers, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-11-passwordless-push-binding-design.md`

## Global Constraints

- Work on `dev/webpush-companion-poc`; do not restart the companion or native port from scratch.
- Keep the pinned Web K and Telegram iOS commits unchanged.
- Test-first only: every behavior change starts with a failing bounded test, the failure must be observed, then the minimum production patch is added.
- Do not run the expensive full iOS/Bazel build during Tasks 1–5. Linux companion CI and bounded native patch tests must be green first. A native build is a separate explicit gate.
- Do not modify `webpush-companion/handoff.js`, `webpush-companion/tap-fallback.js`, `webpush-companion/push-tap-resolver.js`, `webpush-companion/presentation.js`, or the semantics of `scripts/apply_jerkgram_push_click_bridge_v01.py` except for regression assertions.
- Preserve the known-good tap path: `notificationclick -> clients.openWindow(open.html) -> jerkgram://push/open` plus the disappeared-notification root fallback.
- Preserve current sender/text and Telegram no-preview privacy behavior.
- Do not introduce APNs, a server, Time Machine/archive collection, Telegram phone/code login, QR login, 2FA password entry, auth-key export, Keychain/Postbox copying, or a custom Telegram backend.
- The PWA must never send a Telegram account id in the binding. Native Jerkgram chooses the current primary account for v1.
- The only durable PWA binding identity is a random UUID `installationId`. The raw endpoint, `p256dh`, `auth`, and encoded binding must not be logged.
- Native reconstructs the Telegram Web Push token JSON from validated fields; the PWA cannot supply an opaque pre-serialized Telegram token.
- `otherUids` is `[]` in v1.
- Browser `PushSubscription.unsubscribe()` is intentionally not called by v1 Disconnect.
- Status after implementation but before an iPhone test is at most `PATCHED/COMPILED NOT RUNTIME TESTED`; never claim runtime success from CI.

---

### Task 1: Pure web binding envelope and deep-link encoder

**Files:**
- Create: `webpush-companion/binding.js`
- Create: `tests/webpush_binding_test.mjs`
- Modify: `.github/workflows/webpush-companion-poc.yml` only after the new test exists, so the test is exercised by `static-tests`.

**Interfaces:**

```js
normalizeJerkgramPushSubscription(value)
// -> {endpoint, keys: {p256dh, auth}, vapid: true} | null

buildJerkgramBindingEnvelope(installationId, subscription)
// -> {v: 1, installationId, subscription} | null

encodeJerkgramBinding(envelope)
// -> base64url-without-padding string | null

buildJerkgramBindingUrl(action, installationId, subscription)
// action: 'register' | 'unregister'
// -> jerkgram://push/<action>?binding=... | null
```

Use the same strict v1 limits on both web and native sides:

- endpoint: HTTPS URL with a non-empty hostname; UTF-8 length `1...4096` bytes;
- `p256dh`: base64url characters `[A-Za-z0-9_-]`, length `1...256`;
- `auth`: base64url characters `[A-Za-z0-9_-]`, length `1...128`;
- `installationId`: canonical UUID string accepted by `/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i`;
- envelope JSON UTF-8 bytes: at most `5376`;
- encoded `binding`: at most `7168` characters;
- generated URL: at most `8192` UTF-8 bytes;
- exact v1 object keys only: top-level `v`, `installationId`, `subscription`; subscription `endpoint`, `keys`, `vapid`; keys `p256dh`, `auth`.

- [ ] **Step 1: Write the failing Node test.** Cover a valid endpoint/key set, `register` and `unregister` URLs, deterministic round-trip decode, no base64 padding, invalid action, malformed UUID, HTTP endpoint, empty hostname, endpoint/key length boundaries, non-base64url key characters, `vapid !== true`, extra fields, oversized envelope/binding, and absence of Telegram account/auth fields.

The test must also assert that the encoded decoded object is exactly:

```json
{"v":1,"installationId":"123e4567-e89b-42d3-a456-426614174000","subscription":{"endpoint":"https://push.example.test/sub/abc","keys":{"p256dh":"Abc_123-xyz","auth":"Def_456-xyz"},"vapid":true}}
```

- [ ] **Step 2: Commit the test alone** with message `test: define passwordless push binding envelope`.
- [ ] **Step 3: Run/observe RED** using `node tests/webpush_binding_test.mjs`; expected failure is missing `webpush-companion/binding.js` or missing exported helpers, not a test syntax failure.
- [ ] **Step 4: Implement the minimum pure helper** in `webpush-companion/binding.js`. UTF-8 encode the JSON with `TextEncoder`; convert bytes to base64url without `=`. Do not use `localStorage`, `console.*`, Telegram APIs, or account state in this file.
- [ ] **Step 5: Run the Node test green.**
- [ ] **Step 6: Add `node tests/webpush_binding_test.mjs` to `static-tests` and the file paths to the workflow trigger.**
- [ ] **Step 7: Commit implementation** with message `feat: add passwordless push binding encoder`.

---

### Task 2: Replace the Web K auth/pairing surface with browser-only Push binding

**Files:**
- Create: `webpush-companion/apply_webk_jerkgram_passwordless_binding_v01.py`
- Rewrite active expectations in: `tests/test_webk_companion_shell_v01.py`
- Add: `tests/test_webk_passwordless_binding_v01.py`
- Modify later in Task 5: `.github/workflows/webpush-companion-poc.yml`
- Historical but no longer active: `webpush-companion/apply_webk_jerkgram_pairing_v01.py`, `webpush-companion/apply_webk_jerkgram_minimal_ui_v01.py`, `tests/test_webk_jerkgram_pairing_v01.py`.

**Resulting Web K files created/rewritten by the new patcher:**
- `src/lib/jerkgramPushBinding.ts` — copied from `webpush-companion/binding.js`.
- `src/lib/jerkgramCompanionBinding.ts` — owns Push API subscription acquisition and deep-link handoff.
- `src/lib/jerkgramCompanionShell.ts` — notification-only status UI for already-signed-in legacy PWA state.
- `src/pages/cards/SignQRCard.tsx` — repurposed as the passwordless setup card; it no longer executes QR/login-token logic.
- `src/pages/mountAuthFlow.tsx` — every non-authorized auth state routes to the same `signQR` passwordless card; no PasswordCard is reachable from companion setup.
- `src/pages/bootstrapIm.ts` — signed-in legacy Web K state mounts only the same companion shell; no chat UI.
- `src/lib/appImManager.ts` — remove any stale companion overlay injection as today.

**Core browser owner:**

```ts
import App from '@config/app';
import {buildJerkgramBindingUrl} from '@lib/jerkgramPushBinding';

const INSTALLATION_ID_KEY = 'jerkgram.notifications.installation.v1';

function isStandalone(): boolean { /* display-mode or navigator.standalone */ }
function getOrCreateInstallationId(): string { /* crypto.randomUUID(); localStorage UUID only */ }

export async function makeJerkgramBindingUrl(action: 'register' | 'unregister'): Promise<string | null> {
  if(!isStandalone() || !('serviceWorker' in navigator) || !('PushManager' in window)) return null;
  const registration = await navigator.serviceWorker.ready;
  let subscription = await registration.pushManager.getSubscription();
  if(!subscription && action === 'register') {
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: App.pushServerKey
    });
  }
  if(!subscription) return null;
  return buildJerkgramBindingUrl(action, getOrCreateInstallationId(), subscription.toJSON());
}
```

Notification permission remains a direct user-gesture step in the UI before `makeJerkgramBindingUrl('register')` if permission is `default`.

- [ ] **Step 1: Rewrite `test_webk_companion_shell_v01.py` first** so it requires the passwordless shape and explicitly forbids the old one. Required assertions:
  - all non-signed-in auth states (`authStateSignIn`, `authStateSignQr`, `authStatePassword`, auth-code/name/sign-up states present in the pinned source) map to the passwordless `signQR` card;
  - the generated setup/runtime files contain `navigator.serviceWorker.ready`, `pushManager.getSubscription()`, `pushManager.subscribe`, `App.pushServerKey`, `Notification.requestPermission()`, `crypto.randomUUID()`, and `jerkgram://push/register` / `jerkgram://push/unregister` through the helper;
  - only `installationId` is put in `localStorage`;
  - `subscription.unsubscribe()`, `apiManagerProxy.pushSingleManager.registerDevice`, `unregisterDevice`, `apiManager.logOut`, `apiManagerProxy.getUser`, and `Connected as` are absent;
  - `auth.exportLoginToken`, `auth.importLoginToken`, `auth.loginTokenSuccess`, `SESSION_PASSWORD_NEEDED`, `jerkgram://push/authorize`, phone/code strings and PasswordCard routing are absent from the patched setup files;
  - no `console.log`/`console.error` includes subscription, endpoint, `p256dh`, `auth`, binding, or token data;
  - `appDialogsManager` and full Web K chat bootstrap remain absent.
- [ ] **Step 2: Add `test_webk_passwordless_binding_v01.py`** with a compact pinned-source fixture that verifies the new patcher is idempotent and does not require the old pairing patch to have run first.
- [ ] **Step 3: Run the two tests and observe RED** because the new patcher does not exist and the current minimal UI still depends on QR/login-token auth.
- [ ] **Step 4: Implement `apply_webk_jerkgram_passwordless_binding_v01.py` minimally.** It must copy `binding.js` into `src/lib/jerkgramPushBinding.ts`, write the browser-binding owner and the two small setup/status surfaces, and remove dependency on Web K Telegram account state.
- [ ] **Step 5: UI semantics:** fresh Home Screen card says `Jerkgram Notifications`, explains that Jerkgram must already be installed/logged in, has one `Connect with Jerkgram` button, and shows `Add Jerkgram Notifications to the Home Screen first` outside standalone mode. On click: request permission if needed; create/reuse subscription; generate binding URL; set status to `Approve in Jerkgram…`; then `window.location.assign(url)`. It must not claim registration succeeded.
- [ ] **Step 6: Legacy signed-in shell semantics:** show the same product/status text plus `Connect with Jerkgram` and `Disconnect`. `Disconnect` obtains the existing subscription and opens `/unregister`; it does not log out Web K and does not unsubscribe the browser subscription.
- [ ] **Step 7: Run bounded tests green.**
- [ ] **Step 8: Commit** with message `feat: replace Web K auth with passwordless push binding`.

---

### Task 3: Add a narrow TelegramCore type-10 register/unregister owner

**Files:**
- Create: `scripts/apply_jerkgram_webpush_registration_v01.py`
- Create: `scripts/verify_jerkgram_webpush_registration_v01.py`
- Create: `tests/test_jerkgram_webpush_registration_v01.py`
- Patched upstream file: `submodules/TelegramCore/Sources/TelegramEngine/AccountData/RegisterNotificationToken.swift`

**Public injected interfaces:**

```swift
public func _internal_registerJerkgramWebPushToken(
    account: Account,
    token: String,
    excludeMutedChats: Bool
) -> Signal<Bool, NoError>

public func _internal_unregisterJerkgramWebPushToken(
    account: Account,
    token: String
) -> Signal<Bool, NoError>
```

Registration body must preserve stock APNs/VoIP code byte-for-byte and add a separate helper equivalent to:

```swift
var flags: Int32 = 0
if excludeMutedChats {
    flags |= 1 << 0
}
return account.network.request(Api.functions.account.registerDevice(
    flags: flags,
    tokenType: 10,
    token: token,
    appSandbox: .boolFalse,
    secret: Buffer(data: Data()),
    otherUids: []
))
|> map { _ -> Bool in true }
|> `catch` { _ -> Signal<Bool, NoError> in .single(false) }
```

Unregistration must call `Api.functions.account.unregisterDevice(tokenType: 10, token: token, otherUids: [])`, map success to `true`, and catch to `false`.

- [ ] **Step 1: Write `test_jerkgram_webpush_registration_v01.py` first.** Fixture the current stock file. Assert: APNs maps to 1; VoIP maps to 9; both remain unchanged; new helpers exist once; register type is exactly 10; `appSandbox` is `.boolFalse`; `secret` is empty `Data()`; `otherUids` is `[]`; mute flag bit 0 is preserved; unregister is type 10; no endpoint/key/token printing or UserDefaults is introduced.
- [ ] **Step 2: Run test RED** because the patcher/helper does not exist.
- [ ] **Step 3: Implement the source patcher idempotently** using a single stable anchor after the existing stock functions. Do not add a `.webPush` case to `NotificationTokenType` and do not route through `_internal_registerNotificationToken`.
- [ ] **Step 4: Implement verifier** with the same invariants plus exact-count checks for both helper signatures and stock APNs/VoIP markers.
- [ ] **Step 5: Run patcher test and verifier green.**
- [ ] **Step 6: Commit** with message `feat: add TelegramCore Web Push type 10 registration`.

---

### Task 4: Native strict `/register` and `/unregister` binding bridge

**Files:**
- Create: `scripts/apply_jerkgram_push_binding_bridge_v01.py`
- Create: `scripts/verify_jerkgram_push_binding_bridge_v01.py`
- Create: `tests/test_jerkgram_push_binding_bridge_v01.py`
- Regression test: `tests/test_jerkgram_push_click_bridge_v01.py`
- Patched upstream file: `submodules/TelegramUI/Sources/AppDelegate.swift`

**Dispatch contract:**

```swift
if self.handleJerkgramPushBindingUrl(url) { return true }
if self.handleJerkgramPushUrl(url) { return true }
self.openUrl(url: url)
return true
```

The existing `handleJerkgramPushUrl(_:)` implementation itself must remain unchanged.

**Native parser rules:**
- only `jerkgram://push/register` and `jerkgram://push/unregister` are binding URLs;
- malformed Jerkgram-owned binding URLs are consumed locally (`true`) and never passed to generic Telegram routing;
- total URL UTF-8 bytes `<= 8192`;
- exactly one query item named `binding`, with no other items;
- encoded binding nonempty, `<= 7168`, alphabet only `[A-Za-z0-9_-]`;
- decoded data nonempty and `<= 5376` bytes;
- JSON top object exact key set `{v, installationId, subscription}`;
- `v` is exactly numeric `1` (reject Bool masquerading through NSNumber by checking CoreFoundation boolean identity or JSON type explicitly);
- `installationId` parses as UUID and its canonical lowercased string equals `uuid.uuidString.lowercased()`;
- subscription exact key set `{endpoint, keys, vapid}`;
- `vapid` exactly `true`;
- keys exact key set `{p256dh, auth}`;
- endpoint UTF-8 bytes `1...4096`, `URLComponents` scheme exactly `https`, nonempty host;
- `p256dh` length `1...256`, `auth` `1...128`, both URL-safe base64 alphabet only.

**Canonical Telegram token:** build only from validated subscription fields:

```swift
let subscriptionObject: [String: Any] = [
    "endpoint": endpoint,
    "keys": ["p256dh": p256dh, "auth": auth],
    "vapid": true
]
let tokenData = try JSONSerialization.data(withJSONObject: subscriptionObject, options: [.sortedKeys])
let canonicalToken = String(data: tokenData, encoding: .utf8)!
```

`installationId` is validated as the local binding identity but is not included in the Telegram registration token.

- [ ] **Step 1: Add a byte-for-byte click-bridge regression fixture.** Apply `apply_jerkgram_push_click_bridge_v01.py`, capture the exact `handleJerkgramPushUrl` helper body, then apply the future binding patch and assert that helper body is identical. Only the outer dispatch may gain a preceding binding handler.
- [ ] **Step 2: Write `test_jerkgram_push_binding_bridge_v01.py` first.** Require `/register` and `/unregister`, strict size/character/schema checks, exact primary-account selection, username/display-name confirmation, canonical JSON reconstruction, calls to `_internal_registerJerkgramWebPushToken(... excludeMutedChats: true)` / `_internal_unregisterJerkgramWebPushToken`, success/failure alerts, no `/authorize`, no `approveAuthTransferToken`, no `activeSessions`, no UserDefaults, no prints of binding/token/subscription.
- [ ] **Step 3: Include rejection fixtures** for duplicate binding, extra query parameter, invalid base64url, oversized encoded/decoded payload, extra JSON keys at every level, wrong version, invalid UUID, HTTP/no-host endpoint, extra/invalid keys, `vapid: false`, and wrong data types.
- [ ] **Step 4: Run tests RED.**
- [ ] **Step 5: Implement the binding bridge minimally, layered after the existing click patch.** Get `activeAccountContexts |> take(1)`, require `activeAccounts.primary`, read that peer only for confirmation label, present a native `UIAlertController`, and call the TelegramCore helper only from the confirmation action.
- [ ] **Step 6: Use action-specific confirmation copy.** Register: `Allow Jerkgram Notifications for <account>?` / `Connect`; unregister: `Disconnect Jerkgram Notifications from <account>?` / `Disconnect`. Success/failure alerts must not echo endpoint, keys, or binding.
- [ ] **Step 7: Implement verifier and run both tests/verifier green.**
- [ ] **Step 8: Commit** with message `feat: add native passwordless push binding bridge`.

---

### Task 5: Replace old pairing in build chains and companion CI

**Files:**
- Modify: `scripts/install_jerkgram_v12w_build133_probe_hook.py`
- Create: `tests/test_jerkgram_push_binding_wiring_v01.py`
- Stop executing old active test: `tests/test_jerkgram_push_pairing_wiring_v01.py`
- Modify: `.github/workflows/build.yml`
- Modify: `.github/workflows/webpush-companion-poc.yml`
- Keep historical old pairing files in repository for archaeology unless a later cleanup is explicitly requested.

**Required native order before Bazel:**

```text
apply_jerkgram_push_click_bridge_v01.py
verify_jerkgram_push_click_bridge_v01.py
apply_jerkgram_webpush_registration_v01.py
verify_jerkgram_webpush_registration_v01.py
apply_jerkgram_push_binding_bridge_v01.py
verify_jerkgram_push_binding_bridge_v01.py
```

`apply_jerkgram_push_pairing_bridge_v01.py` and `verify_jerkgram_push_pairing_bridge_v01.py` must no longer be in the active installer order or build-workflow preflight.

**Required companion patch order:**

```text
apply_webk_jerkgram_push_v01.py
apply_webk_jerkgram_passwordless_binding_v01.py
apply_webk_jerkgram_branding_v01.py
apply_webk_jerkgram_privacy_v01.py
```

Do not run `apply_webk_jerkgram_pairing_v01.py` or `apply_webk_jerkgram_minimal_ui_v01.py` in the active companion workflow.

- [ ] **Step 1: Write `test_jerkgram_push_binding_wiring_v01.py` first.** Require the six native scripts exactly once in order, before Bazel; forbid active old pairing bridge entries; require `.github/workflows/build.yml` to `py_compile`/test/verifier-preflight the new scripts.
- [ ] **Step 2: Update companion workflow tests first and observe RED.** `static-tests` must include `node tests/webpush_binding_test.mjs`, passwordless Web K tests, new native registration/binding/wiring tests, and all existing push presentation/tap/package/privacy tests. Remove only old pairing-specific tests from the active command.
- [ ] **Step 3: Change the active patch sequence** to the passwordless patcher.
- [ ] **Step 4: Tighten deploy verifier.** It must require strings proving browser Push API + `/register` + `/unregister`, and fail if deployable companion JS contains `jerkgram://push/authorize`, `auth.exportLoginToken`, `auth.importLoginToken`, `auth.loginTokenSuccess`, or `SESSION_PASSWORD_NEEDED` in the companion-owned active setup chunks. Keep all existing `open.html`, `handoff.js`, tap-resolver, branding, source-map, asset-size, and notification-only checks.
- [ ] **Step 5: Keep privacy regression tests.** New passwordless source must not add sensitive `console.*` calls; existing service-worker privacy hardening remains active.
- [ ] **Step 6: Run bounded tests green locally/through Actions.**
- [ ] **Step 7: Commit** with message `ci: switch companion to passwordless push binding`.

---

### Task 6: Full companion CI, source review, and runtime handoff

**Files:** no new production files unless CI reveals a real compile defect.

- [ ] **Step 1: Run the complete `Jerkgram Web Push Companion PoC` workflow at the resulting branch HEAD.**
- [ ] **Step 2: Require `static-tests = SUCCESS`.** Do not continue on a failing or cancelled static suite.
- [ ] **Step 3: Require Web K dependency install, TypeScript typecheck, Vite build, notification-only package, deployable verifier, and artifact upload all `SUCCESS` at the same commit.**
- [ ] **Step 4: Inspect the final diff against `c53e0c374174d11416426b5bc9268572c5244991`.** Confirm no changes to notification presentation/tap helper files and no accidental change to the body of native `handleJerkgramPushUrl`.
- [ ] **Step 5: Report statuses precisely:** web side may be `COMPILED NOT RUNTIME TESTED`; native side is `PATCHED NOT COMPILED` until a real iOS/Bazel build is run. Do not relabel static patcher verification as Swift compilation.
- [ ] **Step 6: Only when a native build is explicitly authorized, run the normal Jerkgram build chain.** If it compiles, status becomes `COMPILED NOT RUNTIME TESTED`; if it fails, repair only the concrete compile defect and rerun the bounded regression tests before rebuilding.
- [ ] **Step 7: After full green companion CI, provide the exact builder commit to pin in `pixxxionix/jerkgram-notifications/.github/workflows/deploy.yml`; do not repin Pages before the branch artifact is green.**

**Real-device acceptance, required before `RUNTIME PASSED`:**

1. Start from a fresh Jerkgram Notifications PWA origin/storage with no Telegram Web K authorization.
2. Add/open from Home Screen; tap `Connect with Jerkgram`.
3. Allow notifications if iOS asks.
4. Native Jerkgram opens, shows the current primary account, user confirms `Connect`.
5. No phone number, SMS/code, QR, Telegram password, or Web K account screen appears.
6. Close the PWA; send a message to the bound Telegram account; require Jerkgram Notifications Web Push delivery with the existing sender/text behavior.
7. Tap it; require native Jerkgram to open the correct account/chat/message and keep the current cold-start latency class (~3.5–4 s, allowing ordinary device/network variance but no new deterministic delay).
8. Repeat at least one group/supergroup push and one case with native Jerkgram already open.
9. Open companion, tap `Disconnect`, confirm in native Jerkgram, then verify subsequent Telegram messages no longer produce that PWA Web Push.
10. Confirm Disconnect did not destroy the browser PushSubscription, and reconnect can reuse it.
11. On an existing legacy signed-in PWA installation, verify the new shell can bind through native without forcing logout; legacy Telegram session cleanup remains intentionally deferred.

## Final self-review checklist

- [ ] Every spec requirement is represented by a task/test above.
- [ ] No task contains TODO/TBD placeholders.
- [ ] Web and native limits match exactly: URL 8192, binding 7168, decoded envelope 5376, endpoint 4096, p256dh 256, auth 128.
- [ ] v1 account ownership is unambiguous: native current primary account only; PWA sends no Telegram account identity; `otherUids: []`.
- [ ] Telegram token is canonical validated subscription JSON only; `installationId` is not included in Telegram token.
- [ ] Registration uses type 10, empty secret, `.boolFalse`, mute flag bit 0; unregistration uses type 10.
- [ ] Fresh PWA has no Telegram auth/login/2FA path.
- [ ] Existing working notification renderer and tap bridge are regression-locked.
- [ ] Old Web K session cleanup and future archive/server work are explicitly deferred.
- [ ] Runtime claims require real-device evidence.