# TASK A final review

Reviewed the complete 28-owner TASK A delta against `before`, final physical `source`, the authoritative patch/hash manifest, TASK A specification and approved design. Also inspected materializer, verifier, build script, native CI ordering and the four designated new test suites. No production edits, subagents, pushes or application builds were performed.

## Result

**No additional actionable material defect found by this review.** This is a source review result, not a native compilation or runtime approval.

- The explicit enhanced engine route leaves the pinned stock text/message implementation intact. OFF decisions use stock availability/Premium/configuration gates. Untagged stock attributes stay valid; tagged enhanced and prior Apple attributes require the account preference and current policy version before immutable-message fingerprint reuse. Canonical account-scoped settings persistence precedes cache update/cancellation and publishes the policy change.
- Enhanced nonPremium cloud requests use text/entities without message IDs. Selected secret input/message/gallery and compose Translate-tab paths propagate `localOnly` to the local service, including Premium secret selection. Unsupported enhanced rich/caption-plus-transcript input fails explicitly. Real Premium cloud selection/chat stays on native routing.
- Input/output entity ranges are validated against UTF16 boundaries; Telegram-returned entities are retained. Local fallback derives ranges from the output and preserves a hidden link only with a unique unchanged label. Source offsets are not copied into changed output.
- Shared enhanced admission has finite active, queued item/byte and per-request limits, deduplication and bounded cache accounting including encoded entity payloads. The deadline includes queue time. Timer capture is weak; the identity-checked terminal path clears the timer and disposes transport. Cancellation and terminal callbacks converge on the serial admission queue. Current policy generation is checked at start, delivery and atomic Postbox installation.
- Enhanced installation compares current message identity/content immediately inside the update transaction, including poll/options/solution and completed transcript content. Failure markers stay eligible for later bounded retry and are not presented as translated originals. The existing visible scheduling cooldown bounds repeated failures.
- Language prediction retains 32-history/16-sample/256-prefix/4-hypothesis limits, per-invocation recognizers, UTF16-safe masking, ignored-language handling and empty-winner rejection. No new full-history scan or unconditional banner was introduced.
- The dependent source stage validates all parent hashes before patching, rejects mixed/unknown owners, reapplies idempotently and restores exact parents for immutable earlier contracts. Build and native CI apply TASK A after Build176 gates; the terminal runner parses the 28 changed Swift owners on an Xcode host. The wrapper additions are on the actual Build176 owner, preserving its transcription methods.

## Independent verification

Executed only the designated new suites for the result below:

| Suite | Result |
| --- | --- |
| `test_jg131_translation_repair_stage.py` | 5 passed |
| `test_jg131_translation_core.py` | 6 passed, 1 Swift skip |
| `test_jg131_translation_ui_repair.py` | 9 passed, 2 Swift skips |
| `test_jg131_translation_corpus.py` | 1 passed |
| Total | **24 tests: 21 passed, 3 explicitly skipped** |

Both `source` and `replay-final` independently matched all 28 final owner hashes. Reversing `source` through the real parent-view helper matched all 28 Build176 parent hashes. Patch hash/scope validation ran through the real manifest loader.

An initial broad filename glob also selected historical translation suites, producing an old-stage hash error and an obsolete literal `allowDownloads: true` assertion against terminal source. These are not terminal-stage requirements: historical gates run on their appropriate preceding stage/parent view. The four correctly scoped suites above were then run individually. No historical 686-test run was repeated.

## Limits and remaining gates

Linux has no Swift/Xcode here. The production-derived Foundation policy/admission, retry-predicate and masking fixtures therefore did not execute; source contracts do not substitute for those fixtures or native module type checking. No concrete Swift API/signature failure was found in the inspected delta, but this review cannot establish successful production compilation.

Backend entitlement, server responses, Apple framework/model readiness, consent UI, Postbox/UI scheduling under real concurrency, semantic RU/EN/DE quality and device behavior remain unverified. Corpus outputs remain NOT_RUN. The combined native build and device matrix remain required, particularly OFF-after-ON cache, account/target changes, edit during request, offline/flood/error, cold manual fallback, secret compose locality, foreground/cancel and existing-feature regression checks. No Ads remains runtime-unproven. TASK B was excluded.
