# Translation Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Restore stock OFF behavior and repair enhanced nonPremium translation without regressing independent features.

**Architecture:** Canonical per-account setting, explicit core route separate from stock system flag; native Telegram text API primary and bounded Apple fallback. Existing native UI and compare-and-store ownership retained.

**Tech Stack:** Swift, SwiftSignalKit, Postbox, Telegram13.1.1, Python source materialization and verifiers.

**Spec:** docs/superpowers/specs/2026-10-29-translation-repair-design.md; user TASK A at ../jerkgram-next/TRANSLATION-FOLDER-SPEC.md.

## Global Constraints

Official13.1.1 only. No global Premium, min-iOS change, third-party text transport, secret credentials, history scan or main-thread network. TASK A committed before B. Preserve App Icons/Download Boost/No Ads. Source compile does not prove entitlement/quality/runtime.

## Review Focus

OFF after cached ON, account switch mid-request, edit/target switch during request, malformed backend entity ranges/count, queue saturation/cancellation and local-only privacy. Pin these at their owning policy/backend or renderer tests.

### Task1 — Core route and freshness

**Files:** TelegramCore/Sources/TelegramEngine/Messages/Translate.swift, TelegramEngineMessages.swift; SyncCore_TranslationMessageAttribute.swift; new Utils/JerkgramTranslationPolicy.swift in materialized source.

**Interfaces:** JerkgramTranslationSettings.preferenceKey = jerkgram.EnhancedTranslation; enabled(accountPeerId:Int64)->Bool, update(accountPeerId:Int64,enabled:Bool), scopedKey(accountPeerId:Int64)->String. Jerkgram enhanced core entry takes explicit enhanced Bool default false; stock enableLocalIfPossible unchanged. TranslationMessageAttribute.isValidForMessage(_:accountPeerId:Int64?) accepts default nil for source compatibility but tagged results fail closed without account. Existing freshness helpers gain accountPeerId argument. Single-text wrapper enhancedTranslate(text:entities:fromLang:toLang:allowLocalDownloads:localOnly:) uses bounded route. Exact signatures finalized and documented before consumer edits.

- [ ] Write failing executable policy/bounds/freshness tests.
- [ ] Implement account cache, explicit bounded request route, typed text/entity storage, Apple fallback once and route provenance.
- [ ] Restore pristine stock engine local behavior when enhanced=false.
- [ ] Run tests and Swift syntax checks; review cache/edit/account cancellation paths.

### Task2 — Canonical preference and native UI consumers

**Files:** SettingsUI/GhostBase/GhostBaseSettingsController.swift; TranslateUI/{Translate,ChatTranslation}.swift; TextProcessingTranslateContentComponent.swift; every existing availability/freshness consumer in translation patch plus ChatController.swift.

**Interfaces:** Account policy and core interfaces from Task1, no context-free availability. Keep account IDs explicit at render boundaries.

- [ ] Pin OFF-vs-pristine gates, per-account setting persistence, native single/chat routing, ignored-language handling and 32/16 bounds in failing tests.
- [ ] Add Messages toggle/footer, canonical activation/update, account-scoped gates and cached-result suppression; preserve Premium/native single route.
- [ ] Make enhanced detection UTF16 safe/per-invocation recognizer; reject empty winner, preserve ignored/base languages.
- [ ] Verify all old flag callsites removed, OFF preserves stock compose/core/gates and no visual-style fanout for preference changes.

### Task3 — Source stage, regression evidence and commit

**Files:** patches/jg131-translation-repair.patch/.sha256.json; scripts/materialize_jg131_translation_repair.py; pipeline/verifier runners; tests/test_jg131_translation_repair.py; docs/translation/repair.md and corpus.json.

- [ ] Add failing exact-parent/idempotence/corrupt-parent tests and32-case input corpus with semantic/device rubric.
- [ ] Generate bounded patch from persistent exact Build176 before/source, implement prevalidated idempotent terminal stage and reverse parent view.
- [ ] Integrate after176, run old gates on restored parent view and new final verifier; clean replay/hash agreement, scoped review, no heavy build yet.
- [ ] Commit TASK A separately with research/design/verification evidence. Only then begin TASK B.
