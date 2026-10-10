# Build154 client diagnostics implementation plan

> Execution: native, in the existing isolated worktree. User approved implementation; no additional approval round.

**Goal:** repair screen attribution, remove the remaining hot phone preference read, and capture slow input/history/keyboard/media work without content.

**Architecture:** extend the bounded expanded-diagnostics delta after preferences. Fixed owner-aware screen labels; new operations share one timing slot and the existing slow-event budget. The regression-locked row source remains byte-identical; an exact overload accepts the cached phone value.

**Tech stack:** Swift, Python materialization/hash contracts, macOS CI native fixtures.

**Spec:** approved conversation scope and constraints in docs/jg13-build153-expanded-diagnostics.md.

## Global constraints

upstream f1dd7a2dbd02cbbf513e75d5695d8d36d1cf5838; com.jerkgram.ios; product1.1.0Beta1; short version13.0; Build154. Preserve five regression hashes, rendering/playback/animation quality, capture RAM-only ring512/timings32/slow96/utility1Hz/600s. No text/peer/message identifiers or automatic uploads. Actual Swift execution only in CI.

## Review focus

Late outgoing controller must not clear incoming route; unknown labels must not leak; repeated input must not exhaust unbounded state; inactive capture must do no timing/report work; editing overload must differ only by preference injection and retain every action/branch.

## Task1: ownership and bounded operation capture

Files: tests/test_jg13_expanded_diagnostics.py, tests/run_jg13_expanded_diagnostics.py; capture core and route owners in expanded patch.

- [ ] Add failing ownership/operation source contracts against Build153.
- [ ] Implement setVisibleRoute(_:owner:), clearVisibleRoute(owner:) and a fixed operation enum with begin/end helpers. Share client.work timing slot and slow96 pool; unknown labels sanitize to unclassified, gaps during navigation to transition.
- [ ] Extend actual native fixture: incoming-before-outgoing ownership, same-label new owner, invalid labels, all operation enum cases, off/stop/restart behavior, 32-slot rejection and privacy.

## Task2: exact phone preference injection

Files: PeerInfoScreen.swift delta, test contracts. Leave PeerInfoSettingsItems.swift locked.

- [ ] Add failing exact-body equivalence and caller contracts.
- [ ] Copy the original function as overload with hideOwnPhone:Bool, replace only the synchronous defaults expression. Pass GhostBaseGlassStyle.profileHideOwnPhone at existing call.
- [ ] Check original-body equality after normalizing only the parameter/read substitution, plus five locks.

## Task3: client boundary hooks and Build154 gate

Files: pinned ChatTextInputPanelNode, ChatControllerNode, ChatHistoryListNode and existing ChatController; expanded manifest/materializer, build config, workflow, docs.

- [ ] Add failing hooks contract for real text-change/layout/history/scroll/media boundaries identified in targeted source reads.
- [ ] Add begin/defer-end at original functions, without changing original bodies/control flow.
- [ ] Generate exact bounded patch; verify hash/survival/locks/fresh apply/repeat refusal, Python compile and full-suite comparison.
- [ ] Commit, publish against freshly checked remoteHEAD, verify CI head and actual native results. Do not claim device performance fixed.
