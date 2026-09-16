# Jerkgram Notifications Beta v1 — Design

Date: 2026-09-16
Status: awaiting user review; implementation not started
Development branch: `dev/build139-notifications-foundation`
Clean product baseline: `f242d55c7d1d4e1736c30488e461f17b71c54762`
Baseline product identity: Jerkgram 1.0.2 Stable / Build138
Target development build: Jerkgram 1.0.2 / Build139
Test deploy repository: `pixxxionix/jerkgram-notifications`
Future production repository: `jerkgram/Jerkgram-Push`
Future production origin: `https://push.jerkgram.app`

## 1. Purpose

Jerkgram Notifications is a Home Screen PWA companion that provides iOS Web Push notifications for sideloaded Jerkgram without requiring native APNs entitlements or an Apple Developer Program push setup.

The architecture keeps a separate Telegram Web K authorization locally on the iPhone inside the PWA. Telegram remains the upstream sender. Apple Web Push delivers the notification to the installed Home Screen web app, whose service worker routes notification taps into native Jerkgram.

Native Jerkgram owns account selection, approval, lifecycle and final routing. GitHub Pages serves static assets only. There is no Jerkgram-owned backend containing Telegram sessions, auth keys, phone numbers, passwords, SMS codes or 2FA secrets.

Beta v1 may expose a single notification account in its user-facing PWA flow, but the native foundation and bridge contracts must be account-scoped from Build139 so the release path does not require a rewrite for multiple native Jerkgram accounts.

## 2. Clean baseline and branch policy

The Notifications implementation starts from the last clean Build138 product commit:

```text
f242d55c7d1d4e1736c30488e461f17b71c54762
Build138: preserve unfiltered chat-list mentions
```

The earlier release commit `a88534f70f90397828b56086d2c2a14b9bf81e9c` created Jerkgram 1.0.2 Stable / Build138; `f242d55...` is the final Build138 fix on top of it and is therefore the implementation baseline.

Old Build139/140/141 notification, native-push and diagnostic experiments are research history only. They are not the product baseline and must not be merged wholesale. Individual ideas or helpers may be re-used only after explicit source review against this design.

The clean development branch is:

```text
dev/build139-notifications-foundation
```

It is based directly on `f242d55...`.

## 3. Product/build identity

The first implementation build remains Jerkgram product version `1.0.2` and advances the Jerkgram internal build identity to `139`.

Required visible identity:

```text
Jerkgram Version: 1.0.2
Jerkgram Build:   139
Telemetry Build:  139
```

About and Telemetry must agree on Build139. Existing rules that keep Telegram/upstream signing identity separate from Jerkgram's own About/Telemetry identity remain in force; the Notifications work must not accidentally replace the upstream bundle/signing version with the Jerkgram product version.

## 4. Goals

Beta v1 must:

- create a dedicated notification-only Telegram authorization for a selected native Jerkgram account;
- avoid phone-number, SMS-code, password and 2FA entry inside the PWA pairing UX;
- receive Web Push while native Jerkgram and the PWA are closed;
- route a notification tap to the correct native account, peer, message and topic when payload data permits it;
- make notification-session creation, repair and deletion explicit;
- revoke the dedicated Telegram authorization when notifications are explicitly disabled;
- make a best-effort revoke before native account logout without blocking the native logout forever if revoke fails;
- survive normal PWA/service-worker updates without intentional re-pairing;
- expose honest lifecycle states rather than a misleading single boolean;
- provide a branded Jerkgram-specific companion UI;
- establish account-scoped native state and a versioned bridge in Build139;
- remain backend-free for Telegram session storage and Push delivery.

## 5. Non-goals for Beta v1

Beta v1 does not require:

- a Jerkgram VPS or application backend for Push;
- server-side Telegram session storage;
- arbitrary Telegram account login directly from the PWA;
- native APNs/Type1 Push;
- native Telegram Web Push registration through Jerkgram's own Telegram API identity (`token_type=10`), which was separately proven blocked by `APP_PUSH_APIKEY_MISSING`;
- quick reply from iOS Web Push;
- a production deployment from `jerkgram/Jerkgram-Push` before test-origin device-runtime verification passes;
- full multi-account PWA UI in the first Beta;
- importing the old experimental Build139/140/141 code as a new baseline.

## 6. High-level architecture

```text
Native Jerkgram Account A
        │
        │ starts and approves pairing
        ▼
Jerkgram Notifications Home Screen PWA
        │
        │ separate local Telegram Web K authorization
        ▼
Telegram Web Push registration
        │
        ▼
Telegram sends Web Push
        │
        ▼
Apple Web Push / APNs infrastructure
        │
        ▼
iOS Home Screen PWA Service Worker
        │ notification tap
        ▼
versioned, validated Jerkgram handoff
        │
        ▼
Native Jerkgram
        │
        └─ exact account → peer/chat → topic → message
```

The PWA may remain closed after setup. No persistent Jerkgram-owned server participates in normal delivery.

## 7. Account model

Notifications must not be implemented as one global `isEnabled` flag.

Native Build139 must introduce account-scoped state conceptually equivalent to:

```text
NotificationAccount
- nativeAccountId
- telegramUserId
- telegramAuthorizationHash
- installationId / companion identity
- lifecycleState
- pushPermissionState
- pushSubscriptionState
- pendingPairing metadata
- pendingRevoke/orphanedRevoke metadata
- bridgeProtocolVersion
```

The first Beta may expose one active companion account through the PWA product flow, but native storage, parsers and lifecycle operations must already be keyed by account. A later release must be able to support every native Jerkgram account without adding a second Home Screen icon per account.

There must be no arbitrary lower Jerkgram-specific PWA account limit. If native Jerkgram exposes seven usable accounts, the release architecture must be able to represent seven independent notification authorizations.

No operation on Account B may silently mutate A, C or any other account.

## 8. Pairing and authentication

### 8.1 Source of truth

Native Jerkgram is the only component allowed to select which account is being connected.

The PWA must not expose an independent "Add Telegram account" flow. Opening the PWA directly without an active native setup request may explain that setup must be started from Jerkgram, but it must not offer phone/SMS/password login as an alternative.

### 8.2 Verified Telegram QR/login-token semantics

The passwordless flow deliberately uses Telegram's official QR login-token protocol.

Verified protocol behavior:

- `auth.exportLoginToken` may run over an unauthenticated connection and returns `auth.LoginToken`;
- a normal `auth.loginToken` contains a short-lived token and expiry, normally around 30 seconds;
- an already-authorized Telegram session accepts the token using `auth.acceptLoginToken(token)`;
- `auth.acceptLoginToken` returns the newly authorized `Authorization` session object, including its session `hash`;
- the logging-in side receives `updateLoginToken`, calls `auth.exportLoginToken` again and receives `auth.loginTokenSuccess` when authorization completes;
- if Telegram returns `auth.loginTokenMigrateTo`, the logging-in side migrates to the requested DC and completes through `auth.importLoginToken`;
- `auth.loginTokenSuccess` contains `auth.Authorization`, including the authorized user identity.

Reference protocol pages:

- `https://core.telegram.org/api/qr-login`
- `https://core.telegram.org/method/auth.exportLoginToken`
- `https://core.telegram.org/method/auth.acceptLoginToken`
- `https://core.telegram.org/method/auth.importLoginToken`
- `https://core.telegram.org/type/Authorization`

This means native Jerkgram can retain the returned notification-session `Authorization.hash` for targeted revocation, while the PWA can independently verify the user identity of the session it just gained.

### 8.3 Pairing sequence

Target sequence:

```text
1. User selects Account A in native Jerkgram.
2. User taps Enable Jerkgram Notifications.
3. Native creates a short-lived pending pairing bound to Account A.
4. User opens installed Jerkgram Notifications PWA.
5. PWA creates a Telegram login token with auth.exportLoginToken.
6. PWA creates a cryptographically random, single-use pairing nonce.
7. PWA hands token + nonce + bridge version to Jerkgram.
8. Native validates the bridge envelope and matching pending pairing.
9. Native shows explicit confirmation for Account A.
10. On Connect, Account A calls auth.acceptLoginToken(token).
11. Native stores the returned notification-session hash against Account A.
12. PWA completes updateLoginToken/export/import handling until loginTokenSuccess.
13. PWA obtains its Telegram user ID.
14. Native/PWA binding is ACTIVE only if PWA user ID == Account A Telegram user ID.
```

No phone number, SMS code, native account password or 2FA password is entered into Jerkgram Notifications for this flow.

### 8.4 Pairing transport is untrusted

The custom scheme is transport, not trust.

A valid pairing requires all of:

- a locally-created native pending pairing;
- a short expiry;
- a cryptographically random single-use nonce;
- a supported bridge protocol version;
- explicit native confirmation naming the selected account;
- Telegram-side acceptance by the already-authorized selected native account;
- final Telegram user-ID equality.

Malformed, expired, replayed or wrong-account handoffs are rejected and must not become ACTIVE.

Universal Links may be evaluated later but Beta must not depend on Associated Domains or Apple Developer signing capabilities.

## 9. Versioned native/PWA bridge

Build139 must establish the bridge contract before the PWA implementation is allowed to depend on it.

Every cross-component handoff must carry an explicit protocol version. Initial version:

```text
Jerkgram Notifications Bridge v1
```

Conceptual native routes:

```text
jerkgram://push/authorize?...   pairing handoff
jerkgram://push/open?...        notification tap routing
jerkgram://push/reconcile?...   lifecycle/repair handoff where needed
```

The concrete field encoding may differ, but v1 parsers must:

- reject unsupported versions;
- reject duplicate single-use pairing nonces;
- validate all numeric identifiers and accepted peer kinds;
- reject missing required account/user identity;
- never interpret arbitrary URLs or commands from Push payloads;
- remain backward/forward diagnosable rather than silently accepting unknown fields as trusted data.

Authentication keys, Telegram session storage, 2FA material and PWA storage databases must never be transported in bridge URLs.

The current prototype behavior that serializes the entire Web Push subscription (`endpoint`, `p256dh`, `auth`) into a native custom-scheme URL is legacy test behavior, not the target v1 contract. The Web Push subscription should stay inside the PWA/Web K path unless implementation proves a specific native requirement.

## 10. Security boundaries

### 10.1 PWA-local data

The PWA may store locally as needed:

- its own Telegram Web K auth/session state;
- installation UUID;
- account-scoped companion/session namespace;
- pairing nonce/state;
- Telegram user ID;
- Web Push subscription;
- minimal lifecycle/UI state.

### 10.2 Data that must not reach Jerkgram hosting or analytics

Do not upload or log:

- Telegram auth keys;
- Telegram session databases/storage dumps;
- native account passwords or 2FA passwords;
- phone login codes;
- phone numbers as an authentication mechanism;
- persistent Telegram secrets.

There is no Jerkgram Push backend in Beta v1.

### 10.3 Production JavaScript is security-critical

Because the PWA origin owns a Telegram authorization, deployed JavaScript and the service worker are part of the security boundary.

Before production migration:

- no third-party analytics or ad scripts;
- no runtime CDN/remote JavaScript;
- dependencies and source revisions pinned;
- no `eval` or remote dynamic-code path;
- strict CSP appropriate to the final build;
- small, reviewable service-worker scope;
- controlled production deployment;
- production branch/deploy protection where available;
- test repository/workflows must not be able to deploy `push.jerkgram.app`.

## 11. Lifecycle state machine

At minimum:

```text
DISCONNECTED
CONNECTING
ACTIVE
PERMISSION_DISABLED
REPAIR_REQUIRED
DISCONNECTING
PENDING_REVOKE
ERROR
```

The UI may use friendlier wording, but the implementation must not collapse these into one boolean.

### 11.1 Enable

`ACTIVE` means all required conditions are true:

- dedicated Telegram notification authorization exists;
- PWA is authorized as the intended Telegram user;
- Web Push registration/subscription is valid;
- native account binding is known;
- routing identity is available;
- setup has completed without account mismatch.

### 11.2 Explicit Disable Notifications

Turning notifications off means the dedicated Telegram authorization must actually be terminated.

Target security sequence:

```text
native Disable Notifications
→ DISCONNECTING
→ account.resetAuthorization(notificationAuthorizationHash)
→ confirmed Telegram revoke
→ clear native binding metadata
→ mark PWA-local cleanup/reconciliation required
→ native may show Not Connected
→ PWA clears/self-logs-out local orphaned companion state on next reachable reconciliation
```

Invariant: native must not claim `Not Connected` while it still knows the dedicated Telegram notification authorization is active.

If Telegram revoke fails, show a retry/error state rather than a false OFF state.

### 11.3 Native account logout

Before ordinary native Telegram account logout, Jerkgram makes a best-effort targeted revoke using the stored notification authorization hash while the native account is still authorized.

If revoke succeeds, logout proceeds normally.

If revoke fails because of network state or Telegram restrictions, native logout still proceeds. Jerkgram must not keep the user's native auth key solely so Push cleanup can retry later.

Jerkgram stores only non-secret orphan/cleanup metadata. On the next reachable PWA reconciliation, the PWA may self-revoke/log out its own notification authorization and clear its companion state.

Backend-free limitation: if native cross-session revoke fails, native logout completes, and the PWA is never opened again, Jerkgram cannot guarantee automatic remote cleanup after destroying the native auth. The leftover Telegram session can still be terminated manually in Telegram Devices.

### 11.4 Session manually terminated in Telegram Devices

The PWA/native state must eventually move to Reconnect/Repair rather than remain ACTIVE forever.

### 11.5 iOS permission disabled

Notification permission loss is not Telegram-session revocation.

State becomes `PERMISSION_DISABLED`. If permission later returns while Telegram authorization and Push subscription remain valid, recover without creating a duplicate Telegram authorization.

### 11.6 PWA removed from Home Screen

A Telegram authorization can outlive the Home Screen installation. Native Jerkgram must not silently create duplicate notification sessions over an unreconciled prior session.

User-facing state becomes Repair/Reinstall until the old binding is reconciled or revoked.

### 11.7 PWA/service-worker update

Normal PWA updates must preserve, when still valid:

- Telegram authorization;
- installation identity;
- account binding;
- PushSubscription;
- tap-routing identity.

A static-site update must not intentionally force every user through pairing again.

## 12. Revocation mechanism

Normal targeted revoke:

```text
account.resetAuthorization(notificationAuthorizationHash)
```

The hash is obtained from the `Authorization` returned to the accepting native account by `auth.acceptLoginToken(token)` and may also be cross-checked through Telegram's account authorization list if needed.

Only the notification authorization associated with the selected native account may be revoked. Multi-account isolation is mandatory.

Telegram may temporarily reject cross-session revoke under freshness/security restrictions. This must surface as an operational error/pending revoke, not be swallowed.

PWA self-logout is an internal cleanup/recovery path, not a second independent user-facing Disconnect ownership model.

## 13. UX ownership

### 13.1 Native Jerkgram owns management

Connect, Disconnect, Reconnect and account selection are managed from Jerkgram.

Example disconnected state:

```text
Jerkgram Notifications
Status: Not Connected
Receive notifications when Jerkgram isn't running.
[ Enable Notifications ]
```

If the PWA is not installed, Jerkgram opens the installation page and gives concise Add to Home Screen guidance. Jerkgram must not assume it can always directly launch an installed Home Screen PWA.

### 13.2 PWA before pairing

The PWA is a companion, not a general Telegram login client.

Example structure:

```text
Jerkgram Notifications
Notifications for Jerkgram without keeping the main app open.
Ready to connect
[ Continue Setup ]
[ Open Jerkgram ]
```

`Continue Setup` may generate a short-lived Telegram login-token handoff. Without a matching native pending pairing, native Jerkgram rejects it.

### 13.3 Native confirmation

The confirmation names the exact native account:

```text
Enable Jerkgram Notifications?
Notifications will be enabled for:
<avatar> Name @username
A separate notification session will be created for this account.
[ Cancel ] [ Connect ]
```

### 13.4 Active PWA

The PWA shows companion status only, for example:

```text
Jerkgram Notifications
● Active
<account identity>
Notifications are being delivered to Jerkgram.
Permission: Allowed
Session: Connected
[ Manage in Jerkgram ]
```

There is no independent red Disconnect button in Beta v1. Normal lifecycle ownership stays in native Jerkgram.

If orphan cleanup requires the PWA to self-logout after a failed native revoke, that action is an internal repair/cleanup state initiated by lifecycle reconciliation, not a second account-management system.

## 14. Visual direction and mascot

The PWA should feel immediately familiar to a Telegram user while remaining visibly Jerkgram-owned.

Direction:

- Telegram-first visual language for the compact setup/status experience: simple centered hierarchy, clean cards/surfaces, familiar spacing and friendly lightweight motion;
- Jerkgram naming and brand remain primary; do not ship the full Telegram Web shell or chat UI;
- light and dark appearance should feel native on iOS;
- use an original yellow duck mascot in the playful Telegram-style visual spirit for setup/status/empty states;
- the duck must be a Jerkgram-owned/original asset, not copied from Telegram proprietary artwork or a Telegram sticker asset;
- animations must be lightweight and must not make the companion UI jank on iPhone.

The mascot may visually react to states such as Ready, Connecting, Active and Repair, but it must not obscure status or error text.

## 15. Telegram Devices branding

Target visible device model/session name:

```text
Jerkgram Notifications
```

Do not change the working Telegram Web K API identity just to alter branding. The safe target is to report a controlled `device_model`/connection identity while preserving the Web K application identity required by the working Telegram Web Push path.

Telegram can display additional app/API identity fields independently of `device_model`, so exact Devices presentation is a real-device acceptance item.

## 16. Notification tap routing

The service worker extracts only minimal routing information supported by the Telegram Push payload, conceptually:

```text
receiver Telegram user ID
peer kind
peer ID
message ID
top-message/topic ID
bridge version
```

All routing input is untrusted.

Native Jerkgram must:

- map receiver user ID to an existing native account;
- never fall back to the currently active account if the receiver is unknown;
- validate peer kind and integer ranges;
- select the correct account before resolving the peer;
- open the topic when applicable;
- navigate to the message when resolvable;
- safely degrade to the chat if message-level navigation cannot be resolved.

Push/deep links must never expose sensitive action primitives such as sending messages, deleting accounts, changing security settings or logging out arbitrary accounts.

## 17. iOS tap fallback

Tap routing must survive direct custom-scheme failure.

Conceptual sequence:

```text
notification click
→ try jerkgram://push/open?...
→ if direct native open cannot complete, open a same-origin HTTPS bridge page
→ bridge retries the validated Jerkgram route and provides a manual Open Jerkgram control
```

The HTTPS bridge may open only validated Jerkgram routing targets; it must not become a generic arbitrary-URL launcher.

## 18. PushSubscription repair

The PWA/service worker must reconcile PushSubscription replacement or loss when observable by iOS/WebKit.

A changed or missing subscription must not leave the product indefinitely displaying ACTIVE while delivery is broken. The binding enters Repair Required until the current subscription is correctly registered with the working Telegram Web Push path.

## 19. Build139 implementation sequence

The implementation is deliberately split so native Jerkgram defines the contract first and an IPA can be produced early.

Sequence:

```text
A. Start from f242d55 clean Build138 baseline.
B. Add native Build139 Notifications foundation only:
   - product/build identity 1.0.2 / 139
   - account-scoped NotificationAccount state
   - bridge v1 parser/model
   - pending pairing state
   - secure authorize/open/reconcile routing boundaries
   - Settings/About/Telemetry integration required to expose the feature
C. Run native tests and start CI IPA Build139 as soon as the native contract is stable enough for device work.
D. While the IPA workflow runs, continue PWA test-repo work against the frozen bridge v1 contract:
   - QR/login-token flow
   - Web Push lifecycle
   - branded UI and yellow duck mascot
   - service worker and tap fallback
   - repair/reconciliation states
E. Join native + PWA on real iPhone.
F. Fix device-runtime defects without changing the bridge contract casually; bridge revisions require an explicit v2 or a backward-compatible v1 change.
G. Freeze exact passing commits only after end-to-end acceptance.
```

This sequence is about delivery order, not permission to implement before the design/spec gate is approved.

## 20. Multi-account release path

After single-account Beta runtime is stable, the release target is multiple independent `NotificationAccount` instances behind one installed PWA.

Requirements:

- one Home Screen icon;
- one dedicated Telegram notification authorization per native Telegram account;
- no arbitrary Jerkgram-specific account-count cap below the native client;
- account-scoped Web K session/storage namespaces or equivalent isolated session manager;
- revoke B without affecting A/C;
- route receiver user ID to the exact native account;
- native logout of B cleans/queues only B;
- UI can later list independently connected accounts and states.

Beta v1 does not have to expose the final N-account PWA UI, but Build139 native state and bridge contracts must already avoid singleton assumptions.

## 21. Real-device release gate

Unit/static tests are necessary but not sufficient. Beta is not ready until a real iPhone passes at least:

1. clean install / Add to Home Screen;
2. permission grant and denial handling;
3. native-owned passwordless pairing;
4. exact account identity match;
5. notification delivery with native app foreground/background/terminated;
6. notification delivery with PWA closed;
7. device restart;
8. warm tap;
9. cold tap;
10. exact native account selection;
11. private chat routing;
12. group/supergroup/channel routing where payload forms differ;
13. message navigation;
14. topic/top-message routing;
15. malformed receiver/peer/message values rejected;
16. replayed/expired pairing handoff rejected;
17. Telegram Devices session naming checked;
18. explicit Disable actually revokes the dedicated Telegram authorization;
19. revoke failure shows Retry/Error and no false OFF;
20. native account logout is not blocked indefinitely by revoke failure;
21. orphan cleanup path works when PWA becomes reachable again;
22. manual Telegram Devices termination becomes Repair/Reconnect;
23. permission off/on recovers correctly;
24. PWA/SW update preserves valid auth/binding;
25. PushSubscription loss/replacement enters repair and recovers;
26. tap fallback bridge opens only validated Jerkgram targets.

The previously observed cold notification-tap latency of roughly 3.5–4 seconds is acceptable for the Beta unless a regression materially worsens it.

## 22. Test-to-production workflow

All Beta iteration remains in test infrastructure first.

```text
pixxxionix/jerkgram-notifications
→ development and real-device fixes
→ freeze exact passing native/PWA commits
→ final security/source audit
→ clean production snapshot
→ jerkgram/Jerkgram-Push
→ push.jerkgram.app
```

Do not use `jerkgram/Jerkgram-Push` as the development laboratory.

Before production migration:

- remove test-only diagnostics/internal references that should not ship;
- ensure licensing/source obligations are met;
- audit deploy chain and pinned dependencies;
- create a clean production snapshot;
- deploy to `push.jerkgram.app`;
- repeat essential runtime tests on the production origin because PWA origin state does not automatically migrate from the test origin.

The old test origin is retired only after production-origin runtime checks pass.

## 23. Current prototype deltas

The existing test prototype proves that Telegram Web Push can reach an iPhone Home Screen PWA and that a notification tap can route into Jerkgram, but it is not the final Beta architecture.

Known deltas:

- existing prototype connect/disconnect is centered on PushSubscription handoff rather than native-owned Telegram-session lifecycle;
- current custom scheme carries the entire PushSubscription;
- current passwordless patch deliberately excludes the final QR/login-token flow described here;
- current PWA has/has had an independent Disconnect path;
- final account-scoped lifecycle is not implemented;
- final bridge v1 replay/validation rules are not implemented;
- final multi-account-ready native state is not implemented;
- final visual shell/mascot is not implemented;
- final Telegram Devices branding requires runtime proof.

These are implementation deltas, not reasons to abandon the working Web K/Web Push architecture.

## 24. Design invariants

The implementation must preserve all of these:

1. The clean code baseline is `f242d55...`, not an old Push experiment.
2. Jerkgram product version stays 1.0.2 for Build139; About and Telemetry report Build139 consistently.
3. Native Jerkgram chooses and approves the Telegram account.
4. The PWA does not ask for the native account's phone/SMS/password/2FA credentials in the intended pairing flow.
5. Telegram login-token acceptance is performed by the already-authorized selected native account.
6. The new notification authorization's session hash is captured from the `Authorization` returned by `auth.acceptLoginToken` for targeted revoke.
7. A notification authorization belongs to exactly one native account.
8. `Not Connected` is never shown while native Jerkgram still knows the dedicated Telegram session is active.
9. Native account logout cannot be held hostage indefinitely by Push cleanup.
10. No Jerkgram-owned backend stores Telegram sessions in Beta v1.
11. Deep links are untrusted transport and use an explicit bridge protocol version.
12. Unknown receiver identity never falls back to the currently active native account.
13. Production PWA JavaScript/service-worker code is security-sensitive and auditable.
14. The PWA owns its Web K session and Web Push subscription; native Jerkgram does not receive PWA auth keys/storage dumps.
15. Native Build139 is account-scoped and multi-account-ready even if first Beta PWA UX is single-account.
16. PWA management is subordinate to native Jerkgram; there is no independent normal Disconnect ownership in the PWA.
17. The yellow duck is an original Jerkgram asset, not copied Telegram artwork.
18. Production deployment happens only after the test-origin device-runtime gate passes.
19. No product implementation begins until this written spec is explicitly approved.