# Jerkgram Notifications Backend PoC — implementation plan

Date: 2026-09-12
Branch: `dev/notifications-backend-poc`
Base: `fcdecd1cf17b3c1506a855ef60a23a167ce5c30c`

## Scope

Build a **test-account-only** proof of concept for rich Jerkgram notifications without APNs and without copying the native Telegram session. The backend creates its own independent Telegram MTProto authorization using Telegram's login-token flow. The already-authorized Jerkgram app will later approve that token explicitly.

This is not approved for production users. A backend Telegram authorization is a full account session, not a notification-scoped credential.

## Milestone 1 — backend pairing API

Create `notifications-backend/` with FastAPI and Telethon. Expose:

- `GET /health`
- `POST /pair/start`
- `GET /pair/{pair_id}`

`POST /pair/start` creates an in-memory pairing attempt, obtains a Telegram login token, and returns a short-lived `jerkgram://push/authorize?...` deep link. Pair IDs are high-entropy and one-time. Tokens and Telegram session material are never logged.

## Milestone 2 — Telegram authorization completion

Use Telethon's login-token/QR-login primitive (`qr_login()` + `wait()`) so the backend waits for approval by an already-authorized Telegram client. On approval, the backend marks the pair `approved` and keeps that independent MTProto session alive for the PoC. Expired/failed attempts become terminal and are closed.

The final native call remains Telegram's official `auth.acceptLoginToken(token)`. Do not copy Keychain/Postbox/auth_key/session data from Jerkgram.

## Milestone 3 — update proof

For the test account, attach a Telegram raw/update listener after authorization and prove the backend receives a complete incoming message update. Do not persist message bodies. Any temporary content inspection used for the PoC must be opt-in and must not write message text to logs or disk.

## Milestone 4 — one native build only

Before any native build, verify the backend can create a login token and wait for completion. Then add the smallest native `jerkgram://push/authorize` handler that validates the token, asks the user to approve the named account, and calls `auth.acceptLoginToken`. Build once and validate the end-to-end flow.

## Explicit non-goals

- no production rollout
- no APNs work
- no retry of Telegram `token_type=10` (`APP_PUSH_APIKEY_MISSING` is already proven)
- no Simple Push as the final rich-notification transport
- no session copying from iOS
- no phone/SMS/code login in the PWA
- no notification archive / Time Machine storage
- no changes to the working notification-tap resolver
- no iOS build while the backend pairing endpoint is still speculative

## Security constraints

- test accounts only during the PoC
- pairing state is in memory and short-lived
- no raw login tokens, api_hash, auth keys, PushSubscription keys, or session strings in logs
- no message-body persistence
- explicit revoke/disconnect must exist before any wider test
- production, if ever approved, requires encrypted session storage with key separation, incident response, privacy/legal review, and a non-Codespaces host

## Verification

Fast backend CI only. It must not invoke Bazel or the iOS build workflow. Tests cover pairing-state lifecycle, terminal-state immutability, deep-link/base64url encoding, health/configuration behavior, pair creation, lookup, expiry, and failure handling.
