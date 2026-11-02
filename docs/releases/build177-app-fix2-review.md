# APP-FIX2 independent review

Verdict: production fix and provenance scope PASS; native regression configuration NEEDS CHANGE. Native compiler acceptance remains PENDING macOS CI.

## Finding

[P2] `tests/test_jg131_translation_core.py:95` invokes `swiftc -swift-version 5 -typecheck` without `-warnings-as-errors`. The requested regression must detect the issue under the actual warnings-as-errors configuration. A successful exit under this command can accept diagnostics that the application build rejects. Add the corresponding compiler flag and establish on the Apple compiler that the immutable pre-fix extraction fails with the relevant capture diagnostic while the corrected extraction succeeds. The portable source assertion supplies useful structural RED evidence, but is not evidence that this native gate catches the original failure. This host cannot establish native RED/GREEN.

## Spec compliance and code quality

- The production patch changes exactly `return Signal { subscriber in` to `return Signal { [self] subscriber in` in admission request. The generator already strongly captures self through its accesses and nested work; the explicit capture expresses that existing ownership. The timer still captures both self and job weakly. Timeout, cancellation, job cleanup, admission counters, deduplication and limits are untouched. No new timer-to-job strong edge is introduced.
- The native test extracts the complete production admission class verbatim and combines existing pinned Signal/Disposable/Subscriber/Atomic fixtures. The actual Signal initializer has an escaping generator and no fabricated implicit-self attribute. Foundation imports provide real Dispatch types. Replacement payload/entity shapes do not model admission methods and do not change capture analysis. This is an appropriate focused fixture, subject to the compiler configuration finding above.
- The reviewed builder diff against `8e16c783b7f0e958e1881f3e58c11c1e533678d9` contains four files. The terminal patch has one changed added source line. Its manifest changes only the patch digest and Translate after-hash; the stage chain changes only the terminal regenerated patch digest and that same owner after-hash. Parent hashes, historical evidence, other owners and downstream patches/manifests are unchanged in this diff.
- The documented pre-existing Strings chain mismatch does not justify broad regeneration for this fix. The controlled terminal update keeps this compiler fix scoped appropriately.

## Evidence and limits

Reviewed APP-FIX2.md, APP-FIX2-FAILURE.md, APP-FIX2.patch, the current test fixture and fresh production admission source, and the builder diff scope. The supplied actual app failure establishes the original application compiler failure. The parent reports final C → B → A gates passed on fresh `build177-appfix2-source`; these were not repeated. No build, native test, commit, or production edit was performed for this review. Existing Linux skips and portable passes must not be reported as native GREEN.
