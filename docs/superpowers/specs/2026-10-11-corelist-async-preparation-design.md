# CoreList: asynchronous row preparation

Status: user authorized implementation; architecture preflight identified a missing
prepared target-geometry contract. App fix NOT IMPLEMENTED, NOT COMPILED,
NOT RUNTIME TESTED. The unchanged upstream native baseline is GREEN.

## Purpose and evidence

Kirill approved investigating an architectural correction to synchronous history
layout, without another general-purpose diagnostic build. The target is responsive
scrolling, keyboard and sending while preserving message geometry and animations.

Baseline: Build157, remote 7be71232f9b723dafe4c771ec57e90f26fe29a59,
Telegram pin f1dd7a2dbd02cbbf513e75d5695d8d36d1cf5838.
The 300-second device report records historyNodeCompute mainMaxMs=497,
historyCoreTransaction mainMaxMs=960, inputSend mainMaxMs=852 and sampled main
queue wait 1432ms. Inclusive spans overlap. These measurements locate blocking;
they do NOT isolate the expensive content-node implementation, exclude Jerkgram
patches, establish the cause of send latency, or establish that all freezes share
one cause.

CoreListNodeHostView.rebuild forwards both item async callbacks as `{ f in f() }`.
ListViewImpl.nodeForItem can instead dispatch those callbacks to its worker queue.
CoreVirtualListView.buildWindow requires a settled height immediately, including
the anchor's height-dependent placement. Its existing onContentDidChange seam
coalesces dirty rows but does not supply an initial unknown height.

## Selected architecture

Use asynchronous preparation BEFORE an atomic settled-window commit, not estimated
heights followed by corrective jumps. Keep the existing backend and animation
model. A direct dispatch substitution is insufficient: the current host would
observe missing layout, return zero height and lose completion handling.

1. Main thread captures a preparation request: list generation, stable identity,
   entry content version, width and side insets, neighbors, loading policy and
   logical transition. Node snapshot/setup follows the existing ListViewItem
   contract; no arbitrary UIKit view/layer operations migrate to a worker.
2. Forward only the work supplied through the item's existing `async` callback
   onto one bounded serial layout executor. Respect its main-thread completion
   contract. Do not replace node implementations or cache an apply closure across
   unrelated content generations.
3. Stage the returned node/layout/apply result without modifying the visible
   settled window. Maintain at most one in-flight calculation and one latest
   pending request per identity. Expire results on content/width/neighbor change,
   deletion, host reuse, chat replacement or disposal; stale results never apply.
   A newer request must not set up or mutate a node whose captured layout is still
   running: mark that generation obsolete and start its latest replacement only
   after the current calculation returns. Globally only one calculation runs;
   pending work is limited to the requested loaded band and canceled when a row
   leaves that band. Do not eagerly enqueue all history entries onto GCD.
4. A resumable window-preparation traversal requests only the target viewport and
   preload-band rows. If a needed row is unresolved, suspend preparation, not the
   main thread. Never block main with a semaphore, DispatchQueue.sync, polling or
   a busy run loop; never prepare the full history collection.
5. Once all needed heights are known, revalidate the request against current list
   state. Capture the pass clock and anchor at COMMIT, not at calculation launch;
   scrolling during preparation must not be rewound to an obsolete offset. Consume
   prepared results through the existing final geometry/animation application
   order, and complete the transaction exactly once after settlement.
6. On a superseding structural or geometry update, abandon the obsolete staged
   window and prepare the latest one. Ordinary scrolling continues displaying the
   existing committed window while preparation runs. First-open/far-jump output
   is committed only with real measured heights; zero-height, guessed-height and
   fabricated blank-row substitutions are forbidden.
   Superseding visual preparation does not discard message-data transactions:
   their ordered effects remain in the logical collection, and every accepted
   caller completion is delivered once for the committed resulting state (or
   explicitly canceled on backend disposal), never silently omitted.

The exact load-band traversal belongs at the engine preparation seam. A host-only
change cannot guarantee the cold/far-jump case. Before modifying that seam, read
the pinned CoreList subsystem sources and retained designs named in its CLAUDE.md,
especially window construction, content reconciliation and projected anchors.

### Required amendment: prepared custom target geometry

The item callback's aggregate size/insets and opaque apply closure are insufficient
to resolve custom center targets against a reused visible node before commit.
`PreparedChatHistoryViewTransition.swift:223-241` produces targets for quoted text
and inner reply subjects. Their getters use the current child text layout and
view frames, whereas the future child layouts and coordinate transforms are
private captures of the bubble's apply closure. Reading the getters during
preparation reads old geometry; applying the result before settlement modifies
the visible node too early.

Extend preparation with an explicit target descriptor and a generation-bound
immutable target geometry result computed by the same quote, todo and poll child
layout producers. Include the final bubble-local transform and missing-match
semantics. Thread that result through item preparation to the target resolver.
Keep the existing post-apply getters as the parity oracle. This extension must
not duplicate visible message state or execute an opaque apply early.

Do not claim that such descriptors support arbitrary `.custom(getOverflow)`
closures: those can inspect arbitrary live node state. Enumerate every actual
producer at the pinned revision; any additional producer needs a prepared
resolver contract before the corresponding asynchronous path can ship.

Tests must compare prepared and post-apply results for changed-width reused
targets, quote wrapping and missing matches, reordered todo/poll options,
rotation/insets and stale content generations. The engine/host-only refactor
does not satisfy this requirement.

## Boundaries and alternatives

Retain primary and secondary timebase policies, backend selection, all logical
animation curves/durations, blur quality, identity rotation and five regression
locks. No AVPlayer/UniversalVideoNode, server killswitch changes, Stable edits,
signing changes, full-history clone/audit or telemetry-protocol edits.

Alternative A: host-only asynchronous update with old-height fallback. Smaller,
but leaves fresh-node blocking and can alter geometry/animation timing; not the
selected complete solution.
Alternative B: switch back to ListView. Existing asynchronous machinery, but
changes backend policy explicitly outside the agreed scope; not selected.

This change removes forced synchronous scheduling, not the underlying cost of
every content calculation. Send preparation may have independent synchronous work
and must not be claimed fixed merely because history scheduling changes.

## Required tests and release gates

Use actual production preparation/commit owners, not a separate scheduler model
that never crosses the host/engine seam. Drive a deliberately blocked worker and
prove a main-queue sentinel completes BEFORE releasing the worker. Mutation control
must fail against the existing inline callback. Then assert:

- fresh and reused rows produce the same final height, insets and apply order as
  the synchronous oracle; exactly one completion, no zero/guessed geometry;
- delete/reinsert, reuse, content change and width/neighbor changes reject stale
  callbacks; bounded work survives rapid repeated requests without a task flood;
- scroll during preparation preserves current anchor and does not rewind offset;
- keyboard insets, underfill, pin-to-edge, far jumps, reversed identity geometry,
  headers and send insertion retain the upstream contracts;
- unchanged tracks keep generation, phase and deadline; changed tracks retain the
  existing logical curves and one clock at commit; unrelated animation properties
  are untouched;
- background/dispose and callback reentrancy cannot apply to detached/rebound rows.

Run existing CoreList geometry/animation tests unchanged plus new actual seam
tests on the mandated iPhone 17 Pro K2 simulator. Its availability is a prerequisite
for UIKit integration claims: this environment has no local Swift/iOS toolchain.
CI availability was verified on 2026-10-11: workflow
`.github/workflows/corelist-native.yml`, commit
`ad08375b2fc0693904f9fce093792e98c5f1881a`, run
https://github.com/ghostbase-sg/jerkgram-telegram-builder/actions/runs/38153200750
passed all 994 unchanged upstream tests with zero failures on the dedicated K2
(iOS 26.5). Artifact `CoreList-K2-baseline-native-evidence`, id 11706939772,
contains the result bundle and test log. This establishes the BASELINE ONLY;
it does not validate an asynchronous app change or produce a new IPA.
Foundation facade/component tests may cover pure bookkeeping but cannot substitute
for the UIKit integration gate. If CI cannot provide that destination, report the
exact verification blocker; do not silently weaken the gate or ship on structural
Python tests alone.

Canonical patch-chain must pass fresh bounded application, before/after hashes,
function survival, five locks, repeat-apply refusal and source diff checks.
No build-number bump or CI launch before implementation and verification readiness.
GREEN + verified IPA permits only COMPILED, NOT RUNTIME TESTED. It does not permit
claims of eliminated freezes, rendered FPS or beta runtime readiness.

## Telemetry: independent investigation boundary

Existing sender posts schema1 activity to the configured Cloudflare Worker and
uses product technicalVersion/build, not CFBundleShortVersionString=13.0.
configure_jg13.py currently configures 1.1.0-beta.1 / 157. Existing native fixture
uses HTTP stubs; it does not prove live receiver or dashboard acceptance.

The four-hour interval is measured from last ATTEMPT, including transport and HTTP
failures. That can defer observation of an update but is not evidence that this is
the reported dashboard defect. Do not reset stored identities, bypass opt-out,
change cadence/schema/version format or inject synthetic production events.

Repository discovery currently exposes only ghostbase-sg/jerkgram-telegram-builder;
no receiver/dashboard repository was found. To finish end-to-end diagnosis, obtain
the actual panel URL or its receiver/dashboard source repository. Read the request
validation, persistence and version grouping/filtering before proposing a patch.
The performance capture remains RAM-only and separate from anonymous analytics.
