# Beta 3 follow-up implementation plan

> For agentic workers: use superpowers:executing-plans inline; independent read-only investigations use dispatching-parallel-agents. Implementation stays serialized per shared owner/stage; one final fresh review.

**Goal:** deliver all user corrections and genuine Telegram13.2 in one common Build180.
**Architecture:** retain source-native32-stage pipeline and accepted local tag store/Core, add reviewed source deltas for lifecycle/UI/native filtering, then sequentially rebase on verified release13.2.
**Tech Stack:** Swift/UIKit/AsyncDisplayKit/Postbox/SwiftSignalKit, Python exact materializers, Bazel/GitHub Actions macOS.
**Spec:** docs/superpowers/specs/2026-11-11-beta3-followup-design.md

## Global constraints

Same chat/current isolated workspace; no account deletion/live-state rewrite/second poller/global Premium spoof/local tags on API. User JSON stays outside Git. User screenshots define actual Wallet and About scopes. Preserve Translation behavior and existing canonical preferences. Source/native gates required; app build only after accepted integration; monitor initial minutes only. One common IPA after all corrections.

## Review focus

- Routine reset during outstanding state fetch must not terminalize or stall importer; auth loss/account removal must cancel before any late write.
- Existing persisted softReset with zero committed pages must recover once within finite request/time budgets; never reset completed/corrupt foreign records blindly.
- Clearing/editing Stars, rapid input then pop/account switch must preserve last valid value without keypress disk I/O or cross-account write.
- Local tag strip empty/nonPremium entry must create/assign/filter without hitting cloud paywall; nil filter restores exact original history and cancelled results cannot publish.
- Genuine upstream merge must retain all32feature deltas and source-derived APIs; required native fixtures cannot silently skip and syntax parsing cannot be called module typecheck.

## Task 1 — Bot lifecycle recovery

Owners: TelegramCore Account/Account.swift, State/JerkgramBotBridgeDiagnostics.swift, State/JerkgramBotBridgeHistory.swift and focused native controller/lifecycle/codec fixtures. Use completed source+runtime reset recon before selecting precise bounded recovery fields. RED: actual routine-reset sequence cancels initial request; retainedsoftReset staysterminal. GREEN: routine reset is observation-only with current running custom manager operation retained; hard lifecycle cancels. Migration for exact retained zero-page softReset is one-time and wire-compatible. Verify owner/generation/late callback/request budgets, persist/reopen bothopts. Preserve current sole state manager and live state.

## Task 2 — Settings, Wallet and Stars

Owners: GhostBaseSettingsController.swift (dedup, About section2footer, officialiconmapping), JerkgramStrings.swift (Translation/current hints), JerkgramStarsEditorController.swift (autosave), WalletScreen.swift or actual screen surface owner after recon. Minimal native surface/card contrast; no global transform. Tests: canonical controls appear once, no preference key/scope migration, Stars valid/invalid/empty/large/rapid/pop account-isolated coalesced commits, same native wallet operations. Exact scope/materializer apply/reverse.

## Task 3 — Native Saved Tags

Owners to finalize from exactnative recon: ChatSearchTitleAccessoryPanelNode / ChatSearchNavigationContentNode, ChatController and history pipeline, typed inline adapter and existing local service/store. Remove Search chooser and pushed results route; keep CRUD sheet/assignment owners as needed. Add typed local tag state separate from reaction tag. Same peer controller bubble history consumes bounded indexed provider; no history mutation. Test empty strip+create, nonPremiumassign, multiselect, >500 bothdirections, nilrestore, unavailable retention, account/pop/reset races, unchanged cloud Premium semantics. Compile exact new adapters against pinned native types in preflight where feasible; full TelegramUI app build remains required.

## Task 4 — Genuine13.2 migration

Confirm tag metadata/toolchain and complete owner tree diff beyond GitHub300compare cap. Reuse prior candidate regeneration engine extended for current32stages and additional feature deltas, keep pristine old/target parents verified against official blob SHAs. Sequentially merge; explicitly resolve feature/native conflicts, preserve untouched patch sections. Two deterministic replays, exact stage reverse/preservation gates, genuine HEAD/index/full checkout only in CI. Retarget only active pins; retain historical snapshots/provenance/native golden fixtures explicitly.

## Task 5 — Integration and common release

Reconcile Build180/Beta3 and newbranch trigger/artifact, exact source proof/focused regression suite, one final independent review and one scoped correction. Commit separate deliverables, publish exact trees under lease, launch common required macOS source/native→app pipeline. Monitor first fewminutes only, record exactremote/localmapping/CI. Final report includes actual runtime findings and remaining device matrix; never claim missing bot history recovered before device/server evidence.
