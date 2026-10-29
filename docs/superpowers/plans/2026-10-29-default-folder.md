# Default Chat Folder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or executing-plans task-by-task.

**Goal:** Native reorder chooses a durable local default for nonPremium accounts without changing server entitlement or limits.

**Architecture:** Canonical opt-in bool; current account Postbox local order separate from synchronized native state; shared engine facade projects effective order and saves compatible server order. Native UI/startup only.

**Tech Stack:** Swift, Postbox, SwiftSignalKit, Telegram13.1.1, Python exact source stages.

**Spec:** docs/superpowers/specs/2026-10-29-default-folder-design.md; user TASK B in ../jerkgram-next/TRANSLATION-FOLDER-SPEC.md.

## Global Constraints

Real isPremium unchanged. Folder count/chats-per-folder/tag/color/sharing limits stock. TASK A committed and survives. No global ID, polling, unbounded reads, credentials, new picker or full build before final combined gate.

## Review Focus

Deleted default numeric-ID reuse; uninitialized startup vs cached offline data; unknown real Premium; toggle/account change during reorder; hidden/over-limit default and ordinary navigation. Tests belong to the owning policy and UI tasks.

### Task1 — Account local order and engine facade

**Files:** TelegramCore/Sources/TelegramEngine/Peers/{ChatListFiltering,TelegramEnginePeers}.swift; SyncCore_Namespaces.swift.

**Interfaces:** JerkgramDefaultFolderSettings.preferenceKey="jerkgram.UnlockDefaultChatFolder"; enabled(accountPeerId:Int64)->Bool defaultfalse; update(accountPeerId:Int64,enabled:Bool); generation(accountPeerId:Int64)->UInt64. Engine peers.updatedJerkgramChatListFilters()->Signal<[ChatListFilter],NoError>; updateJerkgramChatListFilterOrder(ids:[Int32])->Signal<[ChatListFilter],NoError>. Existing native APIs stay stock and remain available for exact OFF/Premium branching.

**Builder-check correction:** The facade produces a coherent presentation struct including filters, known actual Premium, applicable limit/allowed IDs, local-loaded readiness, generation and missing-default state. Names/signatures are finalized by the combined core+UI implementer and recorded before integration; it must not remain a bare [ChatListFilter] stream. The reorder proposal captures generation at drag start. Tasks1+2 execute as one coupled implementation/review unit because both consume this snapshot; no parallel overlapping source edits. Stage/replay remains independent.

- [ ] Write actual-production policy fixture tests and observe RED.
- [ ] Implement bounded local order model/key and projection/server normalization, generation guard, current native peer entitlement, preference event signal, facade and delete cleanup at all native transaction boundaries.
- [ ] Execute scoped tests; record macOS-only skips honestly, verify confirmed APIs and preserve existing native sync/contents.

### Task2 — Canonical toggle/native reorder/startup

**Files:** SettingsUI/GhostBaseSettingsController.swift; ChatListUI/Sources/{ChatListController,ChatListFilterPresetListController,TabBarChatListFilterController}.swift; additional active-owner path only when source proof requires.

**Interfaces:** Task1 fixed policy/facades. Both native reorder surfaces use shared facade only while enhanced nonPremium; read helper projects same effective order for counts/editor/list.

- [ ] Pin exact OFF/Premium paths, unchanged limit blocks, two reorder surfaces, one-shot startup and missing-default fallback in tests.
- [ ] Add Interface toggle/footer and canonical activation/delta policy. Route native reads/saves through scoped facade; scope only default-specific UI gates/coercions. Preserve current layout/performance diagnostics.
- [ ] Validate local-first selection before initializedFilters, safe .all missing/default boundary, limits/hidden IDs and ordinary navigation. Run scoped tests/native extraction fixture where meaningful.

### Task3 — Source stage/replay/review/commit

**Files:** jg131-default-folder patch/manifest/materializer; build and source verifier chain; tests; docs/default-folder report.

- [ ] Add failing stage atomicity/idempotence/reverse tests; generate delta only from byte-exact actual TASK A parent owners.
- [ ] Integrate after TASK A and reverse into A for old verifiers. Clean replay and all new gates; scoped/final review, no claims beyond evidence.
- [ ] Publish separate TASK B commit and source-only native gate. Record result before starting glass. Combined IPA/build number later.
