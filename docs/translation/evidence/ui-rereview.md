# TASK A UI review round 1 — scoped rereview

Compared the six amended Swift owners in `task-a/ui-review-before` with `task-a/source`, read the appended repair evidence in `UI-REPORT.md`, and inspected the revised test module. Scope is the three previous findings, their fixes and directly introduced breakage. No implementation edits or builds performed.

| Previous finding | Result | Source evidence |
| --- | --- | --- |
| P1: Secret compose/edit screen's Translate tab loses locality | **ADDRESSED** | `ChatControllerNode.swift:4997` now passes the chat's SecretChat namespace as `localOnly`. Existing screen → sheet → content → translate-state propagation reaches the Translate tab; the common translation component supplies that state to the request adapter. This covers both nonPremium enhanced and Premium local-only admission. |
| P2: Valid failure markers permanently suppress retry | **ADDRESSED** | `ChatTranslation.swift:158,170` and `ChatHistoryListNode.swift:3265,3286` now require `!translation.jerkgramUnavailable` before skipping. Target/account/fingerprint validation remains. Failure markers can enter existing bounded admission again, while valid successful stock or enhanced attributes still suppress duplicate requests. Loading-failure validity remains unchanged. |
| P2: Manual screen system fallback depends on previously opening a chat | **ADDRESSED** | `Translate.swift:543–561` initializes the existing service when absent and a main-window host is available, before subscribing to the enhanced engine request. `runOn(Queue.mainQueue())` places initialization and subscription on main. `TextProcessingTranslateContentComponent.swift:279` now uses this adapter, covering direct and shared-factory screen construction. Backend cancellation is forwarded by returning the engine subscription's disposable. |

The revised RU/EN `localTranslationUnavailable` strings (`JerkgramStrings.swift:1015`) describe generic translation failure, connection, language/system model availability and unsupported format. They no longer incorrectly attribute every failure to on-device translation.

**New actionable breakage from these fixes: none identified by source inspection.** The adapter preserves entities, source/target, explicit manual model-download permission and locality. Initialization is idempotent across the inspected main-queue entry points. It does not claim fallback availability when no host exists or a model/language is unavailable.

## Verification and limits

Executed the focused suite from the builder with `JERKGRAM_TRANSLATION_REPAIR_SOURCE` pointing to the absolute `task-a/source` directory: **11 tests, OK, 2 skipped** (9 source checks passed).

The new native retry fixture extracts all four actual production cache predicates and checks failure-marker eligibility, successful-cache suppression, changed target and invalid validator outcome. It stubs external containers and core validity rather than claiming to execute the full scheduler. That fixture and the production Foundation mask fixture are explicitly skipped because Swift is unavailable on this Linux host.

These results establish source-level repair of the three findings. Native compilation, cold profile/gift/story system fallback, bounded retries after transient failure and secret compose-draft translation transport remain macOS/device checks; none was executed or claimed here.
