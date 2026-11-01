# Scoped round 1 re-review

**Original P2: ADDRESSED.**

**Spec compliance verdict: PASS for the bounded source migration review.**

**Code quality verdict: PASS for the reviewed source changes.**

No new blocking finding identified in this fix. This closes the sole source-review finding from TASK-REVIEW.md; it does not constitute native or runtime approval.

Reviewed candidate/fix-round1/source-fix.patch and fix-proof.json, the actual final MediaPlayerNode source, the new preservation assertion, and the implementation addendum. Scope was the prior secondary-output rotation omission and risks introduced by its repair. No test suites, build, network or native execution were performed.

The helper applies the effective external angle using each secondary layer's bounds. It is invoked on attachment, secondary bounds changes, and node layout/angle changes. Refreshing secondaries before the primary empty-bounds early return covers independently visible mirrors. This resolves both already-attached and late-attached output cases. The ordinary state rotation/aspect/timebase block is unchanged; clearing external rotation falls back to that existing block.

Lifetime handling is bounded: the duplicate-registration guard precedes observer allocation; one token is stored per registered layer; callback captures are weak; removal drops the registration before invalidating/removing its observer; the helper checks the registered instance before touching it. No retained node/layer cycle or queued stale callback is introduced. The bounds observation executes synchronously on the mutating thread. The reviewed mirror bounds changes originate in UIKit layout, and registration/helper paths assert the existing main-queue contract. No new background layout mutation was found.

The callback writes affine transform rather than the observed bounds property, so there is no direct self-triggering bounds-observer recursion in the repair. Layout and rotation events add a bounded iteration over registered outputs and a transform calculation; no timer or frame-driven subscription is added. Native UIKit/AVFoundation behavior, including transformed mirror resizing, still needs the planned macOS/device validation; source inspection alone cannot establish its runtime result.

The focused regression is a textual source contract, appropriately reported as such. Reported RED-to-GREEN and renewed replay/reversal evidence were read, not rerun. The fix proof confines source changes to MediaPlayerNode and derived Stable/P0 stage records; the prior review's remaining native/full-app/device limitations continue to apply.
