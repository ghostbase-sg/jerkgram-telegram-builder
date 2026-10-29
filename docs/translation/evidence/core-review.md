# Independent TASK A core review

Reviewed the three changed TelegramCore owners, the policy/admission native extraction fixture and its pinned SwiftSignalKit dependencies. No source edits were made. UI changes were outside this review.

## Actionable findings

### P1 — Every admission job creates a permanent timer retain cycle

Owner: `submodules/TelegramCore/Sources/TelegramEngine/Messages/Translate.swift`, `JerkgramTranslationAdmission.request` / `finish`, approximately lines 156–157 and 186.

`job.timer` strongly owns a `DispatchWorkItem`; that work item's closure strongly captures `job`. Terminal handling calls `job.timer?.cancel()` but never clears this reference. Cancellation sets the dispatch block's cancellation state; it does not break the ownership cycle. Success, error, last-observer cancellation, policy cancellation and timeout all leave this same cycle. The retained job also owns its immutable `start` closure, which captures source texts and the account. Consequently the item/byte counters return to zero while actual retained input grows with the lifetime total of completed jobs. The advertised admission memory bound therefore does not hold.

Minimal fix: capture the job weakly in the timeout closure and clear `job.timer` in terminal handling. Also ensure a completed dispatch work item does not retain its source/account through another capture. Add a weak lifetime assertion to the production native fixture for success, cancellation and timeout; current tests count disposal only and never check deallocation.

### P2 — Entity payload strings bypass both input and cache byte budgets

Owner: the same file, `jerkgramEnhancedTexts` input accounting (around line 208) and `JerkgramTranslationAdmission.finish` cache accounting (around line 190).

Both estimates count each entity as a fixed 64 bytes. An entity can own a variable length `.TextUrl(url:)` payload; this owner itself reads and retains that string. For example a four-character source with one valid `0..<4` TextUrl entity and a very large destination passes the 16 KiB guard as approximately 68 bytes. The full payload is then serialized for hashing, retained by the job, and sent to the server. A returned TextUrl of the same size similarly passes the 1 MiB cache accounting as a tiny entity. Count bounds alone do not bound this memory. This remains an independent defect after fixing the timer cycle.

Minimal fix: account for the full encoded entity payload (or explicitly bound all string-bearing entity data) before admission and when retaining output in the cache. Preserve the existing count limits. Add a case with a large hidden URL whose displayed label remains short, and verify rejection/eviction based on actual retained bytes.

## Verification and limits

The bounded Python test invocation against `task-a/source` passed five source checks and explicitly skipped the one native test because Swift is absent. The native fixture includes Atomic, Disposable, Subscriber and the synchronous Signal implementation; its extraction removes the unrelated async-get extension. No obvious missing direct dependency or new native translation API signature mismatch was found by inspection. This does not constitute a Swift compilation result.

The OFF stock owner bodies have exact comparison coverage in the fixture. Enhanced chat requests select local-only transport for secret peer namespaces, native responses validate count and ranges, policy checks occur inside the postbox update closure, and terminal admission updates are identity guarded. These observations do not prove device behavior, backend entitlement, quality, Apple physical cancellation, or UI integration.

The fixture does not execute production routing/network/postbox code, so its passing policy/admission assertions cannot establish those behaviors. Actual Swift compilation and the device matrix remain required. An attempted additional sparse upstream entity-owner read could not fetch its missing Git object because network DNS is unavailable; the variable-length TextUrl evidence above is present directly in the reviewed production owner.
