# Jerkgram Build117 Runtime Boundaries and Release Readiness Specification

## Evidence baseline

- Build116 is runtime-passed for numeric mentions, restored ordinary-user profile panes, and RU/EN send-style localization.
- Build116 is runtime-failed for the Settings/self-profile pane scope, Share, Widget, and Broadcast.
- The Build116 About row opens the canonical channel but is visually rejected because it is only a textual disclosure.
- The copied Build116 diagnostic report contains only the `app` process. Its path ends in `Documents/AppGroup`, not a system `Shared/AppGroup` container.
- `Documents/AppGroup` is absent from the Jerkgram source chain. Treat process-local App Group virtualization after ESign as a strong hypothesis until every extension exposes its own runtime path.
- Build116 already materializes typed `JerkgramSettingsV1` and `JerkgramArchiveV1` foundations. Build117 must preserve them and advance release readiness without claiming that import/export UI already exists.

## Deliverables

1. Distinguish the Settings/self-profile route explicitly from ordinary user profiles. The custom Profile History, Presence, Gift History, and conditional Personal Channel panes remain available in ordinary user profiles and are absent only from the profile embedded in Settings.
2. Replace the static About disclosure with a live native channel-credit row for `@JerkgramApp`. Resolve the channel through `TelegramEngine`, show its avatar and title, show a bounded preview of the latest available post, and open the channel through the normal Telegram navigation path. While loading or offline, show a localized bounded fallback without fabricating peer data.
3. Localize the complete ordinary-profile logging UI through `JerkgramStrings`: all four tab titles, loading/empty states, profile changes, presence states, gift fields/visibility, and personal-channel history. Existing persisted Russian records are translated only at render time so history survives, while user-authored names, captions, and messages remain untouched.
4. Make extension failure evidence visible inside the process that owns it. Share displays a diagnostic surface instead of a blank white controller when initialization cannot reach usable account data. Widget exposes a bounded diagnostic state in its rendered timeline. Broadcast finishes with a stage-specific localized error rather than the undifferentiated `Finished` string. Each visible diagnostic includes process, stage, selected group, and a redacted path classification (`shared`, `processLocal`, `missing`), never a full sandbox UUID.
5. Classify App Group paths consistently in shared source as `shared`, `processLocal`, `missing`, or `other`. A path containing `/Containers/Shared/AppGroup/` is `shared`; a path ending in or containing `/Documents/AppGroup` is `processLocal`. Classification is diagnostic only and must not silently change the selected group or storage root.
6. Add a versioned release-readiness verifier executed after all Build117 source verifiers and before Bazel. It checks the current Build number, semantic localization ownership, absence of raw Runtime/event panes in release Settings, the Settings/self-profile scope invariant, typed Settings/Archive v1 foundations, bounded/redacted extension diagnostics, signer-neutral finalization wiring, and one non-duplicated success artifact.
7. Publish one success artifact named `Jerkgram-build117` containing `Jerkgram-build117.ipa` and `Jerkgram-build117-info.txt`. Failure diagnostics may be uploaded separately only when they are not the same successful IPA payload.

## Release direction

Every later Build must either close a release blocker or add a verified release primitive. The persistent release gates are:

- Official Telegram iOS 12.9.2 remains the source of truth.
- No raw research/debug dumps in normal release UI.
- All Jerkgram UI strings are semantic EN/RU keys following Telegram language.
- Settings and archives are versioned, bounded, migratable, and exclude credentials/signing material.
- Public artifacts remain signer-neutral before ESign.
- Build/verifier success is never reported as runtime success.
- Runtime diagnostics are bounded, redact sandbox UUIDs, and can be removed or hidden behind an explicit developer mode before public release.
- Active workflows publish one canonical success artifact.

## Non-goals

- Do not copy Whitegram proprietary dylibs.
- Do not fabricate access hashes or Telegram peers.
- Do not claim Share, Widget, or Broadcast fixed merely because their diagnostics become visible.
- Do not add user-facing archive import/export in this patch; Build117 preserves and verifies the v1 foundation for that next product step.
- Do not mass-rename legacy internal patch-chain files during this functional Build.

## Acceptance

- Fixture tests prove Settings/self-profile and ordinary profile behavior differ only by an explicit route flag.
- About fixtures prove the row owns an `EnginePeer`, avatar-capable native item, latest-post preview, localized loading/failure fallback, and canonical navigation.
- Extension fixtures prove all three visible failure surfaces use the same path classification and redact UUID-bearing paths.
- Release-readiness fixtures fail on a duplicate success upload, raw Runtime UI, missing archive/settings schema, unlocalized About copy, or a non-Build117 visible artifact name.
- Full focused tests and Python compilation pass before commit.
- Device testing remains required for all runtime claims.
