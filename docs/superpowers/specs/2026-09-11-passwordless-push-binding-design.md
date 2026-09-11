# Jerkgram Passwordless Push Binding Design

## Goal

Remove Telegram/WebK authorization from Jerkgram Notifications. A fresh Home Screen companion must be able to obtain a Web Push subscription and hand it to an already-authorized native Jerkgram, which registers that subscription with Telegram using `account.registerDevice(token_type = 10)`.

The user-facing target is:

`Add to Home Screen -> Connect / allow notifications -> Jerkgram confirmation -> notifications active`

There must be no Telegram phone/code/QR login and no Telegram 2FA password in Jerkgram Notifications.

This change must preserve the already device-proven notification presentation and tap routing, including the current ~3.5-4 s cold-start handoff.

## Current source evidence

Pinned Web K creates a Web Push subscription with the browser Push API and serializes it as token type 10. `PushSingleManager` then registers that token through Telegram. With Web K passcode disabled, the registration secret is an empty byte array.

Pinned Web K's service worker can process a non-encrypted full push object directly. Jerkgram's current patched notification click path derives `user_id`, peer and message identifiers from that push object and opens `jerkgram://push/open`; it does not need the Web K Telegram session to construct the Jerkgram handoff.

Official Telegram iOS 12.9.2 exposes the underlying `account.registerDevice` request in `RegisterNotificationToken.swift`, but its stock public token enum only maps APNs (1) and VoIP (9). Therefore Jerkgram needs a narrow TelegramCore helper for Web Push type 10 rather than pretending a Web Push token is an APNs token.

The existing native pairing bridge currently accepts `jerkgram://push/authorize?token=...` and calls `approveAuthTransferToken`, which intentionally creates a separate Web K Telegram authorization. That path is the part being superseded.

## Scope and non-goals

In scope now:

- browser-created Web Push subscription;
- versioned handoff from PWA to native Jerkgram;
- native registration/unregistration of type-10 Web Push token;
- strict validation and privacy handling;
- fresh-install passwordless setup;
- a migration-safe path for installations that still contain the old Web K authorization;
- identifiers that will not conflict with a future optional archive capability.

Not in scope now:

- always-online server/Time Machine collector;
- server-side Telegram authorization;
- deleted/edit history sync;
- APNs;
- copying native auth keys, Keychain, Postbox or Telegram session material;
- changing notification text/media rendering;
- changing the working notification tap bridge.

## Binding model

A companion installation owns a local random `installationId` generated once with a cryptographically strong UUID and stored only in the PWA's local storage.

The handoff envelope is versioned and capability-specific:

```json
{
  "v": 1,
  "installationId": "<uuid>",
  "subscription": {
    "endpoint": "https://...",
    "keys": {
      "p256dh": "...",
      "auth": "..."
    },
    "vapid": true
  }
}
```

The PWA must not include a Telegram account id. Native Jerkgram is the authority for account identity. For v1, the current primary Jerkgram account is used, matching the existing pairing bridge's account-selection behavior. Its stable Telegram `account.peerId` is the durable account identity; runtime account slot numbers are not persisted as identity.

The future model can add sibling capabilities such as `archive` under the same installation/account identity without changing the Web Push subscription format or the current push registration flow. No archive capability is implemented now.

## Handoff protocol

Registration:

`jerkgram://push/register?binding=<base64url(versioned JSON)>`

Unregistration:

`jerkgram://push/unregister?binding=<base64url(versioned JSON)>`

The payload is base64url without padding. Native consumes malformed Jerkgram-owned push URLs locally and never forwards them to Telegram's generic URL router.

Native validation must enforce bounded total URL/payload sizes, exactly one `binding` query item, schema version 1, valid UUID syntax, HTTPS endpoint, bounded endpoint length, exactly one `p256dh` and `auth` key, URL-safe base64 key syntax/lengths, and `vapid === true`. Unknown fields may be rejected in v1 to keep parsing fail-closed.

The subscription JSON sent to Telegram is reconstructed from validated fields; native never trusts an opaque pre-serialized Telegram token string supplied by the PWA.

## Native Telegram registration

Add a narrow TelegramCore helper adjacent to the stock notification token owner. It calls:

- `account.registerDevice`
- `tokenType: 10`
- `token: <validated Web Push subscription JSON>`
- `appSandbox: false`
- `secret: empty Buffer/Data`
- flag bit 0 enabled to preserve the current Web K `no_muted: true` behavior
- no fabricated APNs token conversion

For v1, registration is performed on the current primary account and uses no durable account-slot number. The native confirmation UI shows that account's username/display name before the network call.

Unregistration uses `account.unregisterDevice(tokenType: 10, token: ..., otherUids: ...)` through the same bounded TelegramCore owner.

No Web Push endpoint/key or binding payload is printed, logged, sent to analytics, or persisted in debug output.

## PWA setup without Telegram auth

The setup surface must no longer depend on `auth.exportLoginToken`, `auth.importLoginToken`, `auth.loginTokenSuccess`, `SESSION_PASSWORD_NEEDED`, or `PasswordCard`.

The companion performs only these steps:

1. Require installed Home Screen standalone mode.
2. On an explicit user gesture, request Notification permission if needed.
3. Obtain the existing PushSubscription or create one with the pinned Web K VAPID application server key.
4. Validate/normalize the subscription locally.
5. Generate/reuse `installationId`.
6. Build the versioned binding envelope.
7. Navigate to `jerkgram://push/register?...`.
8. Native Jerkgram presents confirmation and registers the token.

The PWA does not need a Telegram account, MTProto auth state, user profile, phone number, QR token or password to receive later Web Push notifications.

The existing service worker remains the receiver. For full non-encrypted Telegram push objects, its existing defaults are sufficient for notification display when no signed-in Web K page has populated account state. Jerkgram's patched tap handoff continues to use `user_id` and peer/message fields from the push itself.

## Existing-install migration

Do not automatically revoke or destroy an old working Web K session before the new native registration has been runtime-proven. Existing signed-in installations may use the new passwordless binding UI while their legacy Web K authorization remains temporarily present.

Once the passwordless path is device-proven, legacy-session cleanup can be a separate bounded migration. It must not be coupled to registration success in v1 and must not risk breaking already working pushes.

Fresh installations never create the legacy Web K Telegram session.

## Disconnect behavior

Disconnect must stop Telegram delivery without requiring Web K authorization. The PWA obtains its current subscription and sends the `unregister` binding to native Jerkgram. Native performs Telegram type-10 unregistration for the selected account.

For v1, the browser PushSubscription may remain locally allocated after server-side unregister so reconnect can reuse it and so a suspended custom-scheme handoff cannot leave us without the token needed for cleanup. Local subscription destruction can be added after a proven acknowledgement mechanism; it is not required for stopping Telegram delivery.

The PWA keeps only a local UI marker that a binding was requested/disconnected. Native success/failure alerts are authoritative in v1; the PWA must not claim Telegram registration success merely because the custom-scheme navigation was attempted.

## Security and privacy

- Telegram auth/session material never leaves native Jerkgram.
- The PWA never receives `authKey`, Keychain/Postbox credentials or a Telegram login token.
- Web Push endpoint, `p256dh` and `auth` are treated as sensitive capability material.
- No logging/analytics of the binding envelope or subscription.
- Strict scheme/host/path/query allowlists.
- Strict size and character bounds before base64/JSON parsing.
- Native reconstructs canonical subscription JSON before registering it.
- Do not persist the raw binding in UserDefaults or native logs.

## Preservation constraints

The following current behavior is regression-locked and must not be changed by this work:

- notification sender/text presentation;
- privacy/no-preview behavior;
- Web Push service-worker notification rendering;
- tap fallback cache/resolver;
- `notificationclick -> open.html -> jerkgram://push/open` fast path;
- root-screen disappeared-notification fallback;
- exact account/chat routing already proven on device;
- current cold-start latency behavior.

## Testing and evidence gates

Test-first coverage must include:

- binding envelope encode/decode and strict rejection cases;
- no Telegram login-token/auth methods in the fresh companion setup path;
- no password route required for setup;
- Home Screen-only permission/subscription behavior;
- native strict `/register` and `/unregister` parsing;
- native registration uses token type 10, empty secret and canonical JSON token;
- malformed/duplicate/oversized binding rejection;
- primary-account confirmation before registration;
- no sensitive logging/persistence;
- old `jerkgram://push/open` routing remains byte-for-byte/structurally untouched by the new binding patch;
- Web K typecheck/build/package verifier;
- native patch/verifier compile coverage before any IPA build.

Runtime acceptance is real-device only:

1. Fresh PWA state with no Telegram Web K authorization.
2. Tap Connect, allow notifications, approve in native Jerkgram.
3. No phone/code/QR/password appears.
4. Telegram message produces a Jerkgram Notifications Web Push while the PWA is closed.
5. Tap opens the correct native chat with the current proven latency class.
6. Disconnect stops subsequent Telegram Web Push delivery.

Until those device checks pass, the passwordless binding remains `COMPILED NOT RUNTIME TESTED` at best.