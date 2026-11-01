# TASK C review

Spec-compliance verdict: PASS for the reviewed source and builder integration.
Code-quality verdict: PASS; no actionable findings identified.

Reviewed the design specification first, recovered IMPLEMENTATION.md and REVIEW-DIFF.patch, the four final source owners in replay-final, the materializer and manifest, terminal runner, inherited adversarial stage tests, focused policy/source fixtures, build/native workflow wiring, recursive source verification, and final syntax-owner inclusion. This review covers the complete small TASK C source and builder delta and can serve as its final unit review.

## Findings

None. No severity/file/symbol findings to report.

## Basis

- GhostBaseGlass.swift / JerkgramSettingsMaterialPolicy: separate extraction markers; explicit opt-in, master and Settings admission with Reduce Transparency exclusion; exact item dark 0.34/light 0.26 and card dark 0.60/light 0.70; Low Power does not select another tint.
- PresentationTheme.swift / jerkgramSettingsSurfaceTheme: consumes the production item policy while preserving native text/icon colors and the existing accessibility guard.
- RecentSessionScreen.swift / RecentSessionMaterialState, both component equality functions, initializer and jerkgramSettingsVisualStateUpdated: appended default-false opt-in, captured style state/revision, existing visible/disposed update machinery, no per-layout persistence reads. Updating the same component types and existing Child identities preserves the existing component state and session actions. Both equality levels invalidate when material state changes.
- RecentSessionsController.swift: exactly the session, connected-bot and website detail callers explicitly opt in. Generic full-screen Settings opt-out remains false. Native card background is the sole sheet input changed; native dimming, clipping, bounds, dismissal and gestures remain under ResizableSheetComponent. Its inspected research source retains independent black 0.4 dimming and applies the supplied color to the background layer.
- Source scope remains the four specified owners. No new blur, global observer, runtime hook, generic container edit or premium/global-theme edit was introduced.
- materialize_jg131_settings_glass_expansion.py: validates patch digest and declared owner scope, checks every parent before mutation, accepts exact reapplies, verifies outputs, and restores verified parent bytes in a disposable view. Build and native workflow order places C after B. verify_jg13_source.py reverses C before recursively checking B/A/176; final syntax runner includes C owners.
- Focused fixtures cover all 16 admission combinations, exact light/dark values, absence of a Low Power branch, both equality levels, scoped callers/live callback, and retained native state/action sections. Existing generic stage fixtures exercise apply/reapply, corrupt and mixed parents, reverse restoration, and patch tampering.

## Evidence limits

No tests were rerun, no edits to implementation were made, and no build or network action was performed for this review. The handoff records C 9 tests, reverse B 13, reverse A 24 and older contracts passing on the portable host, with five Swift skips total. macOS source gate remains pending; portable source assertions do not establish Swift type-check/build success or UIKit behavior. Device visual quality, bright/busy-wallpaper readability, light/dark and accessibility changes, tablet/landscape bounds, session/web/bot actions and repeated navigation remain runtime checks. These source-review verdicts do not authorize an IPA or claim device visual success.

## Non-blocking cache observation

RecentSessionSheetContent.body (RecentSessionScreen.swift:311) calls withModalBlocksBackground before the cached Settings mapping. PresentationTheme.withModalBlocksBackground returns a fresh theme when blocksBackgroundColor.rgb equals plainBackgroundColor.rgb; in that branch, the subsequent weak base-identity cache cannot reuse the mapped theme on the next body evaluation. If the colors differ, it returns the stable original theme and reuse remains possible. This can allocate an additional transformed theme/list/chatList per actual body evaluation while the card is active. Existing body triggers include user toggles, bot peer/recipient state updates and environment/layout changes; the diff does not introduce an unconditional per-frame or polling loop. No measured hot-path regression is available, so this is an optional optimization rather than a blocking defect. A future scoped cache could retain the modal base keyed by original environment theme identity, preserving modal placeholder coloring and style invalidation. Merely reversing the two transformations requires care because it can change the modal-color condition and placeholder brightness.
