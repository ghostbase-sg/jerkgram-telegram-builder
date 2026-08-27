# Jerkgram Private Telegram API Identity — Canary Requirements

Status: approved requirements only. Implementation is explicitly blocked until separate user confirmation.

## Goal

Move Jerkgram production builds away from Telegram sample application credentials to Jerkgram's own Telegram application identity without changing client behavior.

## Identity and secret handling

- Target `api_id`: `22732185`.
- The matching `api_hash` is a private build secret. It must never be committed, printed in logs, embedded in public artifacts outside the required application binary, or copied into documentation and test fixtures.
- Production materialization must not use sample `api_id = 8` or sample hash `7245de8e747a0d6fbe11f7cc14fcc0bb`.
- The private hash must enter through the existing canonical build chain from CI secret storage. No manual edits to the materialized Telegram source are allowed.

## Non-goals and invariants

- Do not modify Ghost Mode, deleted-message recovery, edit history, forwarding behavior, or any other Jerkgram feature.
- Do not modify bundle identifiers, signing, MTProto/DC configuration, or authorization behavior beyond supplying the new application identity.
- Do not mix this migration into an unrelated public release.

## Required verification

Before implementation is accepted, a build-chain verifier must fail both before and after compilation when any of these conditions is true:

1. Materialized production source still contains the Telegram sample API ID or sample hash in an active credential owner.
2. The final IPA contains the Telegram sample API ID or sample hash.
3. The configured API ID is not `22732185`.
4. The private API hash is missing from the canary build environment.

Verifier output must identify only the failing owner or invariant and must never print the private hash.

## Canary gate

The first build using the new identity is a private canary and must not be published as a public release. On test accounts it must pass:

- normal login;
- existing Jerkgram feature smoke tests;
- Jerkgram appears as a separate application/session in Telegram Devices;
- no `unofficial_security_risk` response;
- no `API_ID_*` errors.

Public builds may use the new application identity only after all canary checks are explicitly recorded as successful and a separate promotion decision is made.

## Implementation hold

Until separate confirmation, do not change overlays, workflow files, CI secrets, build scripts, materialized source, or release identity for this requirement.
