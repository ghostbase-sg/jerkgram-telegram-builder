# CoreList asynchronous preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Move the existing item-supplied layout calculations onto one bounded worker, preserving settled geometry, target positioning, row identity and logical animations, then produce Build158.

**Architecture:** Prepare candidate rows without changing the committed collection/window. Stage generation-bound measurements and opaque apply closures. Recompute preparation against the current viewport before entering the existing synchronous atomic commit; deliver backend callbacks after commit.

**Tech Stack:** Swift 5, UIKit, Telegram ListViewItem contracts, CoreVirtualListView, Python canonical materialization, GitHub Actions Xcode 26.6/macOS26.

**Spec:** docs/superpowers/specs/2026-10-11-corelist-async-preparation-design.md

## Global Constraints

- Base product Build157, remote 7be71232f9b723dafe4c771ec57e90f26fe29a59; exact Telegram pin f1dd7a2dbd02cbbf513e75d5695d8d36d1cf5838.
- Existing product source: work/final157 in this worktree. Pinned engine and pristine additional owners: /workspace/scratch/9222bd465490/upstream-corelist.
- Write edited production owners under work/async158, preserving exact relative upstream paths; preserve work/final157 and the pristine upstream checkout.
- No estimates, zero-height substitutions, partial visible apply, semaphores, synchronous queue waits, backend switch, animation disablement or full-history preparation.
- Keep unchanged animation generation/phase/deadline; capture animation pass clock and anchor at commit.
- Keep all accepted logical transactions ordered; every completion once after commit, or explicitly canceled on disposal.
- Stable Build138, production push, telemetry sender/panel, signing, blur/timebase policies, AVPlayer and five regression locks remain outside this task.
- Only worker callbacks supplied by the existing item API execute off-main; obey its setup/completion contract.
- Native gate: dedicated iPhone 17 Pro K2, -parallel-testing-enabled NO -collect-test-diagnostics never. Baseline already passed 994 tests in run38153200750; do not repeat it as evidence of an app fix.
- Do not bump build or launch a device IPA until production implementation, canonical checks and changed native seam tests are ready.

## Review Focus

- A reused quote target changes width while an earlier layout is in flight: target geometry and apply belong to the same generation.
- A fast scroll changes the required band while preparation is blocked: current offset remains authoritative and newest required rows are prepared.
- A deleted stable identity is reinserted: an old callback cannot apply to a new physical binding.
- Two accepted structural transactions arrive before settlement: data effects and completions retain their original order.
- Fresh/far target, edge pin and underfill: final row heights and positioning match the unchanged synchronous oracle.

---

### Task 1: Prepared scroll target geometry

**Files:**
- Create: work/async158/submodules/Display/Source/ListViewPreparedScrollTarget.swift
- Modify staged copies of submodules/Display/Source/ListViewItemNode.swift, ListViewIntermediateState.swift, ListView.swift.
- Modify staged copies of submodules/TelegramUI/Sources/PreparedChatHistoryViewTransition.swift.
- Modify staged copies of submodules/TelegramUI/Components/Chat/{ChatMessageBubbleContentNode,ChatMessageTextBubbleContentNode,ChatMessageTodoBubbleContentNode,ChatMessagePollBubbleContentNode,ChatMessageBubbleItemNode,ChatMessageItemImpl}/Sources/*.swift, only owners necessary for this contract.
- Tests: tests/native/ListViewPreparedScrollTargetTests.swift (compiled with the actual production helper on K2).

**Interfaces:**
- Produces public enum ListViewPreparedScrollTarget: Hashable with cases quote(String, offset: Int?), todo(Int32?), poll(Data?).
- Produces ListViewItemNodeLayout.preparedScrollTargetRect: ((ListViewPreparedScrollTarget) -> CGRect?)?; existing initializers preserve source compatibility through a default nil parameter.
- Adds ListViewCenterScrollPositionOverflow.preparedCustom(ListViewPreparedScrollTarget, (ListViewItemNode) -> CGFloat). Existing ListView and intermediate-state callers use the supplied live resolver exactly as .custom did.
- PreparedChatHistoryViewTransition emits preparedCustom for the two known quote/inner-subject producers, with the same existing live resolver. Do not alter post-apply getter semantics.
- Exact prepared rects use the final child text/option layout and bubble-local frame transform, immutable once returned. No live UIView reads from worker closures. Freeze fresh-node measurement before attaching or applying its opaque closure.

- [ ] Write native tests for immutable union/translation/missing target behavior and generation-owned snapshots in the actual new production helper. Include quote wrapping bounds, reordered todo/poll identifiers and changed child origins.
- [ ] Run new tests before helper exists: observe compile failure identifying the missing production symbol, not a broken harness. Root owns CI publishing and runs.
- [ ] Implement the above typed contract and thread rects through the actual text/todo/poll final layout results and bubble final ListViewItemNodeLayout. Keep all existing layout/apply order intact.
- [ ] Run native helper tests GREEN, retain actual-producer integration limitations explicitly; device app compilation later must cover every modified production owner.
- [ ] Review staged diffs against the existing getters as oracle and report any untested producer parity or module/build-list requirement. Do not claim the app fix complete at this task.

### Task 2: Bounded candidate-window preparation and host commit

**Files:**
- Modify staged CoreVirtualListView.swift and, if needed, its attachment extension.
- Create staged focused CoreList preparation owner(s) under the existing CoreListDemo source group.
- Modify staged CoreListChatHistoryBackend.swift, based on the exact final157 version.
- Tests: staged CoreListDemoTests/CoreListPreparationTests.swift.

**Interfaces:**
- Consumes Task1 ListViewPreparedScrollTarget and ListViewItemNodeLayout.preparedScrollTargetRect.
- Adds opt-in CoreListPreparedItem protocol; func prepare(view: UIView & CoreListItemView, width: CGFloat, transition: CoreListTransition, completion: @escaping (CGFloat) -> Void). The callback reports actual settled height only; engine controls lifetime and generation.
- Adds CoreListScrollTarget.prepareResolve: ((CGFloat, UIView & CoreListItemView) -> CGFloat?)? with a source-compatible default nil. Chat target callbacks consume the host's staged layout/target metadata, not its live node state.
- Adds CoreVirtualListView.applyChangesPrepared with the existing applyChanges argument list plus completion: @escaping (Bool) -> Void. true means committed, false explicitly canceled; synchronous non-opt-in behavior remains the oracle.
- CoreListEntryItem implements CoreListPreparedItem; host stages the candidate item/neighbor/inset/width/transition binding, and update consumes that result during the original synchronous commit order.
- Preparation suspension occurs before the original applyChanges mutates dirty flags, _items, logical viewport or visible node apply state. Existing synchronous commit remains authoritative.

- [ ] Write tests calling actual new engine APIs with blocked opt-in items: main sentinel completes before worker release; collection and views remain committed until ready; mutate control uses inline callbacks and fails the responsiveness assertion.
- [ ] Observe RED on K2 before implementing the new engine API.
- [ ] Implement a resumable pure measurement traversal preserving anchor/prepend/pin-slack/append/underfill/attachment reservation rules. Candidate collection is separate from committed _items. Only viewport/preload-band requests are retained; no full-history enqueue.
- [ ] Implement host staging via nodeConfiguredForParams/updateNode async callbacks, one bounded serial executor, one current calculation and latest pending binding per identity. New setup waits for that node's prior calculation. Stale result validation includes content/width/neighbors/binding/transition and deletion/reuse/disposal.
- [ ] Cover rebuild/cold target and scroll rebalance as well as applyChanges. Revalidate the current viewport after every asynchronous completion; commit once the required band is ready using prepared results. Commit clock/anchor are sampled at this final point.
- [ ] Move backend insertion-block animation, visible range/offset, trailing-space, header updates and caller completion to the explicit committed callback. Preserve accepted transaction data and ordered completion ledger through supersession/reentrancy/disposal.
- [ ] Run native tests GREEN: unequal fresh/reused heights+insets, far targets, scroll during preparation, changed width/insets, pin and underfill, delete/reinsert/rebind, ordered completions, stale callbacks and unchanged animation tracks.
- [ ] Review all original engine update call sites for synchronous expensive chat fallthrough and report any remaining gap. No build bump until corrected.

### Task 3: Canonical patch integration and release verification

**Files:**
- Create patches/jg13-corelist-async.patch and .sha256.json.
- Create scripts/materialize_jg13_corelist_async.py and tests/test_jg13_corelist_async.py.
- Modify scripts/materialize_jg13.py, verify_jg13_source.py and expanded verifier final-owner delegation.
- Modify .github/workflows/corelist-native.yml to apply the exact changed CoreList owners and shared production target helper/tests before K2 test.
- After gates: jerkgram-migration.json, version configuration/checks and build workflow branch trigger as required for Build158.

**Interfaces:**
- Consumes work/async158 production source delta from Task1+Task2 and the changed native tests. Manifest binds exact upstream pin, before/after hashes, declaration survival and five locks.
- Produces a separate canonical stage after Build157's expanded-diagnostics stage, with immutable earlier stages and explicit final-owner exemptions.

- [ ] Write exact-scope, wrong-before-hash, repeat-refusal and five-lock tests for the canonical stage; observe RED before stage implementation.
- [ ] Generate bounded patch/manifest and implement stage delegation; verify a fresh bounded canonical source fixture and repeat refusal GREEN.
- [ ] Publish only the test branch and run changed K2 suite. Read logs and native results; repair failures and rerun only relevant changed gates.
- [ ] Obtain independent review of production+canonical diff; fix material findings with reproducing tests.
- [ ] Bump Build158 while keeping technical version1.1.0-beta.1 and Telegram bundle-short13.0; run canonical/version checks.
- [ ] Trigger the authorized dev device build, monitor compile/package/export, inspect IPA/build provenance and artifact availability. Compilation does not imply runtime freezes fixed.
- [ ] Deliver exact new CI and IPA links with compiled/runtime status.
