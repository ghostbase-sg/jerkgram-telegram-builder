# Build176 candidate — Performance Remediation Wave 1

Baseline: Build175 `4881f8573e940ff503b7a5d4db6356050098c6a6`, Telegram13.1.1 `fb0e62ba8a147f0821da6aa63c09da7d79a10111`; Swiftgram reference `e3a392272b182dbf975d4ac5fc33b40a5954d749`. Scope: A/B1/B2/C only. Runtime parity and observed iPhone latency are not claimed fixed.

## Source architecture

The existing23source stages remain before a dependent terminal `jg131-performance-wave1` stage. Its manifest pins23 runtime owners to exact Build175 inputs and exact candidate outputs. Preflight checks all inputs before mutation, validates patch owner scope, applies once and verifies every output. Reverse view preserves older contracts. The only earlier hash change is `JerkgramStrings.swift` before/after identity175→176 in the profile-metadata manifest; patch bytes unchanged. No compiler flags, history backend, translation semantics, credentials or canonical archive cleanup changes.

The build and native-preflight workflows run all earlier175stage gates before applying the terminal stage, then176fixtures, exact verifier and Swift parsing. Full IPA is invoked once after the shared source preflight succeeds. Candidate branch `codex/build176-wave1` is explicitly admitted to the existing build workflow push trigger; no per-patch workflows were dispatched.

## A — ownership

`JerkgramDataAndBackupController.swift`: actions capture weak `actionTarget`; controller constructed as strong `let`, assigned to target and returned strongly. Per-chat picker retains its original weak callback policy; cleanup body is unchanged. Export/import active-operation ownership and archive callbacks are preserved. Narrow ItemListController subclass counts lifetime only under the defaultOFF instrumentation helper. Its generic/context convenience initializer is inherited; the existing convenience initializer lives in PresentationDataUtils.

## B1 — projection

SharedAccountContext's existing two activation sites call SettingsUI's account projector. Initial migration preserves scoped precedence and existing canonical legacy fallback; once an active-projection marker exists, missing values on another account use defaults rather than the previous account's compatibility projection. Ordinary page construction reads an immutable state value; it performs no migration/projection or setter. There are still approximately49once-per-construction reads; no new stale global state cache was introduced.

The49-key catalog is unchanged. Equality guards scoped, compatibility and scheduled suite setters. Hot invalidation intersects actual changed hot keys; activity/blocked publications are domain-gated; visual fields/metadata publish one atomic snapshot. Compatibility writes complete before activation publication, avoiding a queued old-account write crossing handoff. This moves initial migration work to activation: cold worst case100counted writes including marker; unchanged activation0. It is not eliminated startup work and device timing remains required.

Portable import retains the full catalog and legacy scheduled/protected/one-time aliases, while calling the same activation projector after committed import. No archive transaction/data semantics were changed. The known S7cleanup/import race remains deliberately deferred.

## B2/C — coherent visual lifecycle

- `GhostBaseGlassStyle` publishes only actual visual deltas with UInt64 revision; settings translucency/master/playback/phone plus profile metadata delta enter one publication. Theme and existing app-lifecycle/environment callbacks compare actual values. No new global observers/polling.
- Existing scoped controller observer marks hidden owners dirty. Full refresh/layout waits for appearance; Promise ignores repeated revision. Disappearance removes child backdrop from hierarchy to release output, while retaining material for reattachment.
- Actual revision invokes provider with the existing UIView. Same-source/same-style updates reuse it. Root can lazily supply a source for a visible descendant while its own header/sections/layout remain deferred. An async placeholder joins the weak set immediately and receives source updates in place. Replacement inserts/attaches successor before predecessor removal; session transition attaches successor lease before old disposal.
- Root/header/panes/metadata/sections consume coherent revisions; initial masterOFF→ON can create the background, and visible creation activates it immediately. Pane wrapper revision invalidates its native layout cache without replacing panes; Groups row equality includes visual state. Disabling glass restores native fill and clears the owned bio mask.
- Normal mode retains `.26`dark / `.18`light backing. Low Power keeps surface identity while denying video/material; no arbitrary nested `.90`. Reduce Transparency declines translucent theme/background and uses native opaque fill, including fields/report/gift/pane surfaces. Devices detail and emoji popup exclusions175 are untouched.
- Existing app active/resign callbacks and appearance compare system modes. No new mode notification observer is installed. A system state transition that delivers neither lifecycle nor appearance nor existing visual callbacks requires device verification; no polling fallback was added.

## Before / after source acceptance

These are source-operation counts/ownership conclusions, not measured CPU/FPS/disk writes.

| Scenario | Build175 | Build176 source result |
|---|---|---|
|Ordinary migrated GhostBase page construction|49keys treatedchanged;99sets (69caller/30deferred)|0projection setter calls;49read snapshot|
|Same page hot invalidation|1unconditional|0|
|Same page playback/style publication|1unconditional playback, style event|0|
|No-op persistence|hotinvalidate/playback publication|0setters/invalidation/publication|
|Nonvisual setting delta|broad style publication|0visual publication; affected domain only|
|Visual multi-key batch|potential multiple style events|1atomic publication/revision|
|Hidden style callback|refresh/state/layout/material work|dirty only; full refresh0|
|Repeated same style|remove/create backdrop possible|sameUIView/material/session retained|
|Popped DataBackup page|strong state/action/controller cycle|weak action target; ARC/device live count pending|
|Nested reduced backing|LowPower OR ReduceTransparency→black.90|LowPower normaltint/nomotion; accessibility nativeopaque|
|Last native source lease replacement|oldlease disposed before replacement|successor acquired/attached before release|

## Default OFF instrumentation

`JERKGRAM_PERF_AUDIT` is not enabled in candidate build settings. No permanent display link, polling, observer, formatting or network sink is added. Diagnostic counters are thread-safe only when enabled; release bodies compile away. `JerkgramWave1Instrumentation.snapshot()` returns an empty dictionary when disabled.

Counters: `liveDataBackupControllers`, `projectionWrites`, `hotInvalidations`, `visualPublications`, `styleCallbacks`, `deferredStyleCallbacks`, `visibleOwnerRefreshes`, `hiddenOwnerRefreshes`, `materialEffectCreations`, `activeVideoOutputLeases`. Leases count admitted visible descendant attachments, including suspended handles; they are not a count of decoders or currently playing frames. Missing key means zero after instrumentation bootstrap. Capture snapshots at scenario boundaries through development debugger; no removed diagnostics UI is reintroduced. The defaultOFF candidate supports manual timings/screen recordings but does not secretly enable counters.

## Verification

Local Linux: focused source/materialization checks and phase-correct prior contracts; native Swift/Apple Foundation and UIKit are unavailable. Native fixtures extract production projector/hot helpers, actual pane wrapper, actual playback session/output method and production visual policy; their framework/UI boundaries are explicitly stubbed where needed. Source checks establish wiring/ownership, not rendered appearance or actual ARC on iPhone.

Replayed24stages from clean pinned upstream owner inputs;323/323finaloutputs matched, no mismatches. No credential configuration was invoked by the replay. Exact apply/reverse/reapply-refusal/corrupt-last-parent-before-first-mutation checks pass. Full syntax/native fixtures and compilation remain CI gates; the Actions result and artifact are recorded after the run.

Cross-review found and fixed: hidden-root theme layout bypass, visible masterenable scene activation, stale bio mask, hidden child output release, expired weak lease count, hidden root masterenable/provider reuse, async placeholder readiness. Each regression was observed failing before the bounded fix. These checks do not establish whole-client Swiftgram parity.

## Device validation — iPhone14Pro / iOS26.7.1

Record Build175 and176install identities, power/accessibility/theme/translation settings, same account/media and comparable temperature/cache state. Each trial records start→first usable frame/response and visible hitch, plus crash/visual notes. Use10warm and3cold trials where feasible, then20/100navigation repeats. Do not mix framework model downloads with steady-state typing measurements.

| Scenario | Build175 | Build176 | Required observation |
|---|---|---|---|
|Cold first Settings|pending|pending|latency to usable UI, first material/source|
|Warm second Settings|pending|pending|latency/hitches|
|Nested Settings|pending|pending|no darkness jump/native modal boundaries|
|20push/pop|pending|pending|latency drift, memory/live objects|
|100push/pop|pending|pending|progressive lag/retained objects|
|Repeated DataBackup|pending|pending|popped controllers release; export/import/picker/cancel work|
|Self-profile|pending|pending|first/repeat/crash/layout correctness|
|Foreign profile|pending|pending|first seconds/metadata/panes|
|Static avatar|pending|pending|correct image/no unused video output|
|Animated avatar|pending|pending|one native timeline; child transition/offscreen/resume|
|Typing30–60s|pending|pending|fresh vs after100navigation; IME/selection unchanged|
|Fast scrolling|pending|pending|hitches/frame pacing|
|LowPowerON/OFF|pending|pending|normal tint; video/material admission/resume|
|ReduceTransparencyON/OFF|pending|pending|readable opaque fallback across root/nested/fields/panes|

Also toggle master while root is hidden under a child, change avatar/theme/account, enter/exit app, cancel a transition, and open Devices detail/emoji popup. Instruments development-signing remains separate from the defaultOFF distributed IPA. Runtime acceptance requires stable memory after idle, no retained popped pages, zero hidden full refresh, zero unused output leases and paired hitch/latency evidence.

## Deferred findings

Patch D research request disposal/payment ownership; E residual typing/diagnostic locks/unread consumer/menu gates; F gift JSON main queue, capture admission bounds and presence/profile caches; G conditional translation fingerprint/scheduling cost; H archive atomicity/retention/index/import/export memory. S7must be fixed before any automatic cleanup. Compatibility dylib startup/picker/keychain overhead and GPU/thermal impact remain measurement candidates. No new feature work is part of this candidate.

### Local result before integration CI

- Focused wave suite45executions:43passed /2native-skipped; existing animation suite5:3passed /2native-skipped. Foundation projector fixture extraction succeeded; execution explicitly skipped on Linux. No Swift syntax execution was available locally.
- Prior-phase contracts77:60passed /17native-skipped; preceding-source UI contracts5:5passed. Total132unittest executions:111passed,21skipped,0failures/errors. These are intentionally phase-correct contracts, not132UIKit tests.
-24stage replay323/323outputs matched after final review fixes; exact terminal stage23owner apply/reverse/refusal tests pass. Root verifier passes through reversed terminal view. YAML/Python/shell syntax checks pass.
- Existing `jg131-ui-repair.patch` emits its known trailing-whitespace warning during reverse-view setup. `git diff --check` also flags whitespace-only context lines inside the generated terminal `.patch` text; exact source bytes/context are preserved. No semantic/hash gate was weakened to hide these warnings.

Actions run/IPA: pending single candidate push; native/compilation results will be recorded separately. Source wave acceptance is complete; runtime performance validation remains pending.

### First macOS preflight

Commit59b8998 / run40819114434 stopped before IPA (`build-probe` skipped). Actual native visual policy and shared playback/output fragments passed; Swift owner parse passed. Two fixture-only failures: missing parentheses around the pane fixture Path before `.read_text()`, and top-level inferred `Set<Dictionary<..., private JerkgramSettingValue>.Keys.Element>` requiring explicit private/type annotation in the Foundation fixture. Both corrected without changing runtime source/manifest. This is an additional source-preflight attempt, not an additional heavy IPA build. Candidate source acceptance is pending successful native fixture rerun.

### Second macOS preflight

Commit9eb58912 / run40819680258: actual production Foundation projection/migration/account/import/cache fixtures PASS, as did native visual policy, shared playback/output fixtures and syntax parsing. Pane fixture still lacked `import CoreGraphics`, so the standalone macOS executable did not see the CGSize equality overlay that UIKit imports in the app. Added the missing fixture import; runtime sources unchanged. IPA job again skipped; heavy build count remains0.

### Successful macOS source gate / active integration

Candidate runtime commit `2c3540a905d1e64fee668863eb0b65727dc5dfad` (same runtime patch as59b8998; follow-ups only repair fixtures). [Actions40820248325](https://github.com/ghostbase-sg/jerkgram-telegram-builder/actions/runs/40820248325), preflight job123270788167 SUCCESS. All45wave tests passed with native policy/wrapper enabled; actual production Foundation projection/migration/account/import/cache fixture PASS, native shared playback/output fixtures PASS, Swift syntax parse PASS. See `build176-evidence/native-preflight-success.json`.

**Performance Remediation Wave 1 source acceptance complete.** This denotes source/native-fragment gates, not iPhone ARC/rendering performance or Swiftgram parity. The single heavy `build-probe` job123271206223 has started; IPA artifact pending.

### Integration complete

Both jobs in run40820248325 SUCCESS. IPA artifact12876229430, `Jerkgram-1.2.0-Build176`, archive95,197,521bytes, digest `sha256:c62985f8a824fec4dca81e49a07cc25ee821d48ba95ed98c3bc2fc58b004c83e`. [Artifact](https://github.com/ghostbase-sg/jerkgram-telegram-builder/actions/runs/40820248325/artifacts/12876229430). Diagnostics artifact12876259298. Full compilation/packaging succeeded for runtime commit2c3540a9. Exactly one heavy IPA build ran; two earlier attempts stopped in native fixture preflight before IPA.

**Performance Remediation Wave 1 complete at source/native/compilation gates.** Device latency, ARC counts, appearance, power/accessibility transitions and Swiftgram parity still require the matrix above. No phone runtime success is implied by GREEN CI. Latest user subsequently authorizes a separate future Devices glass scope, replacing the175native-only exclusion for that future patch;176exclusion itself remains unchanged.
