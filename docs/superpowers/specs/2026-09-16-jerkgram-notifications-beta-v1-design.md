# Jerkgram Notifications Beta v1 — Design

Date: 2026-09-16
Status: approved for planning; implementation not started
Development branch: `dev/webpush-companion-poc`
Baseline commit before this design: `1b8b720f3ac935d4a169c7a81e79611e7acd967e`
Test deploy repository: `pixxxionix/jerkgram-notifications`
Future production repository: `jerkgram/Jerkgram-Push`
Future production origin: `https://push.jerkgram.app`

## 1. Purpose

Jerkgram Notifications is a Home Screen PWA companion that provides reliable iOS Web Push notifications for sideloaded Jerkgram without requiring Apple Developer Program push entitlements.

The working architecture keeps a separate Telegram Web K authorization locally inside the PWA and uses Telegram's Web Push path. The native Jerkgram client owns account selection, approval, lifecycle and routing. GitHub Pages serves only static PWA assets and must never become a store for Telegram sessions, auth keys, phone numbers, passwords or 2FA secrets.

Beta v1 is intentionally single-account at the product/UI level, but its internal data model and lifecycle must be multi-account-ready so the release version can support every account available in Jerkgram without a separate PWA installation per account.

## 2. Goals

Beta v1 must:

- support one Jerkgram account end-to-end;
- create one separate notification-only Telegram authorization for that account;
- avoid phone-number, SMS-code, password and 2FA entry inside the PWA;
- receive Web Push while Jerkgram and the PWA are closed;
- route notification taps to the correct native Jerkgram account, peer, message and topic when available;
- make notification-session creation and deletion explicit and auditable;
- revoke the notification Telegram authorization when notifications are disabled;
- attempt to revoke it automatically when the native account logs out, without blocking logout if revocation is temporarily impossible;
- survive normal PWA/service-worker updates without forcing re-pairing;
- expose honest lifecycle states instead of a misleading boolean toggle;
- present a branded Jerkgram-specific UI rather than Telegram Web UI;
- use a data model that can later represent multiple notification accounts independently.

## 3. Non-goals for Beta v1

Beta v1 does not need:

- multi-account UI;
- an application backend or VPS;
- server-side storage of Telegram auth/session data;
- arbitrary Telegram account login directly from the PWA;
- native APNs/Type1 push;
- native Telegram Web Push registration through Jerkgram's own API identity (`token_type=10`), which is currently blocked by `APP_PUSH_APIKEY_MISSING`;
- quick reply from iOS Web Push;
- a public production deployment from `jerkgram/Jerkgram-Push` before device-runtime verification passes.

## 4. High-level architecture

```text
Native Jerkgram Account A
        │
        │ starts/approves pairing
        ▼
Jerkgram Notifications PWA
        │
        │ separate local Telegram Web K authorization
        ▼
Telegram Web Push registration
        │
        ▼
Apple Web Push delivery on iOS
        │
        ▼
PWA Service Worker
        │ notification tap
        ▼
validated Jerkgram deep-link handoff
        │
        ▼
Native Jerkgram
        │
        └─ account → peer → topic → message
```

The PWA may be closed after setup. No persistent Jerkgram-owned backend is part of Beta v1.

## 5. Account model

The implementation must not model the feature as a single global `session` or `isEnabled` boolean. It must use an account-scoped entity conceptually equivalent to:

```text
NotificationAccount
- nativeAccountId
- telegramUserId
- telegramAuthorizationHash
- installationId
- lifecycleState
- pushPermissionState
- pushSubscriptionState
- pendingPairing metadata
- pendingRevoke metadata
```

Beta v1 exposes only one active `NotificationAccount` in UI, but the storage and code boundaries must permit multiple independent instances later.

Release target: the number of notification-enabled accounts must not have a separate hardcoded PWA limit. If Jerkgram can host seven accounts, all seven should eventually be able to have their own notification authorization inside one installed PWA.

## 6. Pairing and authentication

### 6.1 Source of truth

Native Jerkgram is the only component allowed to select which account is being connected. The PWA must not expose an "add arbitrary Telegram account" flow.

### 6.2 Passwordless pairing

The target flow is based on Telegram's login-token/QR-login protocol rather than phone/password login in the PWA.

1. The user opens the notification settings for native Account A and selects Enable Notifications.
2. Jerkgram creates a short-lived local pending-pairing record bound to Account A.
3. The user opens the installed Jerkgram Notifications PWA.
4. The PWA obtains a short-lived Telegram login token using the Web K authorization flow and creates a cryptographically random one-time pairing nonce.
5. The PWA hands the temporary token and nonce to Jerkgram through the pairing transport.
6. Jerkgram accepts the handoff only if a matching non-expired local pending pairing exists.
7. Jerkgram displays an explicit confirmation naming Account A.
8. On confirmation, Account A calls the Telegram acceptance method for the login token.
9. The returned new authorization metadata, including its authorization hash when available from Telegram's authorization object, is associated with Account A for targeted later revocation.
10. The newly authorized PWA validates that its Telegram user ID matches Account A before marking pairing complete.

The PWA must never ask for or store a native account's phone number, SMS code, password or 2FA password as part of this pairing UX.

### 6.3 Pairing transport is untrusted

The custom scheme transport (`jerkgram://...`) is not itself an authentication boundary. All values received through it are untrusted input.

A valid pairing requires:

- a native locally-created pending pairing;
- a short expiry;
- a single-use random nonce;
- explicit user confirmation in native Jerkgram;
- Telegram-side acceptance by the already-authorized selected account;
- final Telegram user-ID equality between the PWA authorization and the selected native account.

A mismatched account, expired pending request, replayed nonce or malformed token aborts the pairing and must not create an active binding.

Universal Links may replace or supplement the custom scheme later if the signing/Associated Domains setup permits it, but Beta v1 must not depend on that capability.

## 7. Security boundaries

### 7.1 PWA-local data

The PWA may keep locally, only as needed:

- its own Telegram Web K authorization/session storage;
- an installation UUID;
- pairing nonce/state;
- the Telegram user ID of the notification authorization;
- its Web Push subscription;
- minimal UI/lifecycle state.

### 7.2 Data that must not be sent to Jerkgram hosting or analytics

The project must not upload or log:

- Telegram auth keys/session database contents;
- 2FA passwords;
- phone login codes;
- phone numbers as an authentication mechanism;
- Web K storage dumps;
- persistent Telegram secrets.

There is no Jerkgram Push backend in Beta v1.

### 7.3 Deep-link minimization

The current prototype embeds the full Web Push subscription (`endpoint`, `p256dh`, `auth`) in `jerkgram://push/register`. That mechanism is considered legacy/test-only for the target design.

Production-oriented Beta work should minimize the deep-link payload. Native Jerkgram should not receive the PWA's Telegram auth material. Web Push subscription ownership and registration should stay with the PWA/Web K path unless a concrete native dependency is proven during implementation.

### 7.4 Production JavaScript is security-critical

Because the PWA origin owns the browser storage that contains the notification Telegram authorization, production JavaScript is part of the security boundary.

Before production migration:

- no third-party analytics or ad scripts;
- no remote/CDN JavaScript at runtime;
- dependencies pinned;
- no `eval` or dynamic remote code execution;
- a strict CSP appropriate to the final build;
- a small, reviewable service worker;
- controlled production deployment;
- production branch protections/deployment review where available;
- test infrastructure must not be able to deploy to `push.jerkgram.app`.

## 8. Lifecycle state machine

The product must model at least these states internally:

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

The UI may use friendlier text, but it must not collapse these states into a single toggle value.

### 8.1 Enable notifications

On success:

- a dedicated Telegram notification authorization exists;
- the PWA has a valid Web Push registration;
- native Jerkgram has a binding to the correct Telegram user/account;
- tap routing is verified;
- the UI reports Active only after all required binding steps complete.

### 8.2 Disable notifications

Turning notifications off means more than disabling UI or unregistering a push endpoint.

Target sequence:

```text
native Disable Notifications
→ revoke the dedicated Telegram notification authorization
→ confirm successful revoke
→ clear native binding metadata
→ remove/disable the corresponding push binding
→ clear PWA-local account binding state
→ show Not Connected
```

Invariant: `OFF` / `Not Connected` must not be shown while the dedicated Telegram notification authorization is still known to be active.

If revocation fails, the UI stays in Disconnecting/Error with Retry rather than pretending the session is gone.

### 8.3 Native account logout

Native account logout must attempt to revoke that account's notification authorization first.

If revocation succeeds, logout proceeds normally.

If revocation fails because of connectivity or a temporary Telegram restriction, logout must still be allowed. Jerkgram records a pending revoke task and retries when possible. Push lifecycle must never trap a user inside an account they want to log out of.

### 8.4 Session removed manually from Telegram Devices

If the user terminates the notification authorization elsewhere, Jerkgram Notifications must eventually detect loss of authorization and surface a reconnect/repair state instead of remaining Active indefinitely.

### 8.5 iOS notification permission disabled

Disabling notification permission in iOS does not imply Telegram-session revocation.

State becomes `PERMISSION_DISABLED` and the user is directed to iOS Settings. If permission later returns and the Telegram authorization and subscription are still valid, the system should recover without creating another Telegram authorization.

### 8.6 PWA removed from Home Screen

The Telegram notification authorization may outlive the PWA installation. Native Jerkgram must not silently create another authorization over the old one.

The target user-facing state is Repair Required / Reinstall Jerkgram Notifications, followed by reconciliation of the existing authorization before any replacement is created.

### 8.7 Service-worker/PWA update

Normal PWA releases must not intentionally reset:

- the Telegram authorization;
- the account binding;
- the installation ID;
- a still-valid PushSubscription;
- tap-routing identity.

A site update must not force all users to pair again.

## 9. Revocation mechanism

The intended native revoke mechanism is account-scoped Telegram authorization management rather than a generic local logout toggle.

Jerkgram should retain enough authorization metadata to identify and terminate exactly the notification authorization associated with the native account. Multi-account design requires Account B revocation to have no effect on A/C/etc.

Telegram may temporarily refuse cross-session revocation under freshness/security restrictions. This must be represented as an operational failure/pending revoke rather than silently ignored.

The PWA may also need a self-logout/recovery path as a fallback, but the normal user-facing owner of connect/disconnect is native Jerkgram.

## 10. UX

### 10.1 Native Jerkgram — disconnected

Example structure:

```text
Jerkgram Notifications
Status: Not Connected
Receive notifications when Jerkgram isn't running.
[ Enable Notifications ]
```

If the PWA is not installed, Jerkgram provides concise install instructions and opens the installation page. If installed, it tells the user to open Jerkgram Notifications from the Home Screen.

### 10.2 PWA — before pairing

The PWA is not a Telegram login screen. It shows Jerkgram branding and a single guided setup action.

Example:

```text
Jerkgram Notifications
Notifications for Jerkgram without keeping the main app open.
Ready to connect
[ Continue Setup ]
[ Open Jerkgram ]
```

`Continue Setup` can prepare the short-lived login-token handoff, but the PWA cannot choose a Telegram account or authorize itself without a matching native pending pairing and native approval.

### 10.3 Native confirmation

The native confirmation must show the exact selected account, including enough identity information to prevent an accidental wrong-account connection.

Example:

```text
Enable Jerkgram Notifications?
Notifications will be enabled for:
<avatar> Kirill @username
A separate notification session will be created for this account.
[ Cancel ] [ Connect ]
```

### 10.4 PWA — active

The active PWA should be a small branded companion, not a Telegram Web interface.

It may show:

- Jerkgram logo;
- Jerkgram Notifications title;
- Active status;
- bound account identity;
- permission status;
- session status;
- Manage in Jerkgram action.

The PWA must not expose a separate independent Disconnect control in Beta v1. Native Jerkgram owns connect/disconnect lifecycle.

### 10.5 User-facing status language

User-facing states should be concise, for example:

```text
Active
Not Connected
Notifications Disabled in iOS
Session Expired — Reconnect
Jerkgram Notifications Needs Repair
Disconnecting…
Could Not Disconnect — Retry
```

## 11. Branding and Telegram Devices session name

PWA branding target:

- name: `Jerkgram Notifications`;
- short name: `Jerkgram`;
- no visible Telegram Web branding in the companion shell;
- light/dark appearance aligned with iOS/Jerkgram visual language.

Telegram Devices target device name: `Jerkgram Notifications`.

Do not change API identity merely for branding. The working Telegram Web K identity is part of the functioning Web Push path. The safe target is to control the reported device model / connection metadata where possible while preserving the working Telegram Web Push application identity.

Exact presentation in Telegram Devices remains a device-runtime verification item because Telegram may display secondary application/API identity fields independently of `device_model`.

## 12. Notification tap routing

The service worker extracts only the minimal routing fields supported by the Telegram push payload, conceptually:

```text
receiver/native account user ID
peer kind
peer ID
message ID
top message/topic ID
```

All incoming routing data is untrusted and must be validated by native Jerkgram before opening content.

Native Jerkgram must:

- match the target Telegram user ID to an existing native account;
- validate peer kind and numeric ranges;
- select the correct account before resolving the peer;
- open the topic when applicable;
- navigate to the message when available;
- degrade safely to the chat if message-level routing cannot be resolved.

Notification deep links must not provide sensitive action primitives such as logout, account deletion, sending messages or changing security settings.

## 13. Tap fallback inspired by Komet

Komet's public PWA implementation demonstrates a useful two-step iOS fallback:

```text
notification click
→ attempt custom-scheme native open
→ if direct open fails, open an HTTPS `open.html` bridge
→ bridge retries the custom scheme and presents a manual Open App button
```

Jerkgram Beta should preserve or implement the same conceptual fallback for iOS reliability:

```text
jerkgram://push/open?... 
↕ fallback
/open.html?to=<validated native URL>
```

The bridge must only accept/construct validated Jerkgram routing targets and must not become a generic arbitrary-URL launcher.

## 14. PushSubscription changes and repair

The service worker must detect or reconcile PushSubscription replacement/loss where iOS exposes `pushsubscriptionchange` or equivalent observable state.

A changed subscription must not silently leave the UI Active while delivery is broken. The account enters Repair Required until the current subscription is registered correctly with the working Telegram Web Push path.

This is another useful behavior confirmed by the public Komet PWA, but Jerkgram's repair flow must account for the additional Telegram notification authorization layer.

## 15. Multi-account release path

After Beta v1 is stable, the release extension is conceptually N independent `NotificationAccount` objects inside one PWA installation.

Requirements for the later multi-account release:

- no separate Home Screen icon per account;
- one independent Telegram notification authorization per native Telegram account;
- no PWA-side fixed account-count limit;
- account-scoped storage namespaces and lifecycle state;
- revoke one account without affecting others;
- route each notification to the matching native account before opening the peer;
- logging out Account B only revokes/queues revocation for B;
- UI can list the connected native accounts and their independent states.

Beta must not introduce storage keys, singletons or APIs that make this extension require a complete redesign.

## 16. Testing and release gate

Static/unit tests are necessary but not sufficient. Beta is not considered ready until real-device runtime testing passes on iPhone.

Device-runtime verification must cover at least:

1. clean install / Add to Home Screen;
2. notification permission grant and denial handling;
3. passwordless single-account pairing;
4. account identity match;
5. notification received with native Jerkgram foreground/background/terminated;
6. PWA closed;
7. iPhone restart;
8. warm tap routing;
9. cold tap routing;
10. correct account selection;
11. private chat, group/supergroup and channel routing where payloads differ;
12. message-level navigation;
13. topic/top-message routing;
14. session name as rendered in Telegram Devices;
15. Disable Notifications actually removes the dedicated Telegram authorization;
16. revoke failure produces an honest retry state;
17. native logout is not blocked by revoke failure;
18. manual Telegram Devices termination becomes Reconnect/Repair;
19. iOS permission off/on lifecycle;
20. PWA/service-worker update without forced re-pairing;
21. PushSubscription change/loss repair;
22. malformed/replayed/expired pairing handoffs are rejected;
23. malformed notification routing cannot trigger sensitive native actions.

## 17. Development and production workflow

All remaining Beta work happens on the test/development path first.

The existing public-test deployment may contain iterative commits and diagnostics. It remains disposable/laboratory infrastructure.

Do not populate `jerkgram/Jerkgram-Push` with development history during Beta work.

After Beta reaches the release gate:

1. freeze the exact tested source commit(s);
2. perform a final security/source audit;
3. remove test-only diagnostics and internal/development references that must not ship;
4. make the public production source self-contained enough to comply with licensing and auditing requirements;
5. create a clean production snapshot in `jerkgram/Jerkgram-Push`;
6. deploy that snapshot to `push.jerkgram.app` through the production GitHub Pages workflow;
7. repeat essential device-runtime checks against the production origin because PWA origin changes do not migrate Web Storage, Service Worker state or Telegram authorization automatically.

The old test origin is retired only after the production-origin runtime check passes.

## 18. Current prototype deltas

The current prototype proves the core Web Push and native tap-routing concept but does not yet satisfy this design.

Known design deltas include:

- current connect/disconnect flows rely on Web Push subscription handoff and do not yet implement the final native-owned notification-session revoke lifecycle;
- current `jerkgram://push/register` contains the full PushSubscription payload;
- current PWA has an independent Disconnect action;
- current passwordless patch explicitly excludes Web K logout paths;
- final account-scoped state machine is not yet implemented;
- final security validation/replay resistance is not yet implemented;
- final multi-account-ready storage model is not yet implemented;
- final Devices branding must be proven on real hardware;
- final production shell/security hardening is not yet implemented.

These are implementation tasks, not reasons to abandon the already working Web K/Web Push architecture.

## 19. Design invariants

The implementation must preserve these invariants:

1. Jerkgram chooses and approves the account; the PWA does not independently add accounts.
2. No native-account phone/password/2FA login UI in the PWA.
3. One notification authorization belongs to exactly one native Telegram account.
4. `Not Connected` means the dedicated authorization is actually revoked or no longer exists; no false OFF state.
5. Native account logout cannot be blocked indefinitely by Push cleanup.
6. No Jerkgram-owned backend stores Telegram sessions for Beta v1.
7. Production JS/service-worker code is part of the security boundary and must be auditable.
8. Tap routing is validated as untrusted input.
9. Beta UI is single-account, architecture is multi-account-ready.
10. Production deployment occurs only after the test-origin device-runtime release gate passes.
