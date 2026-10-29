# TASK A — Translation repair

## Executive summary

Build176's existing translation modification forces Apple/system translation on iOS18+, regardless of real Premium, preference, supported models or readiness. Missing models/unsupported content have no Telegram fallback, local output drops entities, and there is no enhanced preference. These are source-proven causes of unavailable/inconsistent behavior; semantic RU/EN/DE quality remains unmeasured.

Enhanced Translation / Улучшенный перевод lives in **Jerkgram → Messages**, per account, default ON to preserve the previous nonPremium feature. OFF restores native availability/Premium decisions, native single-message composition and the stock engine interpretation of system translation. Tagged enhanced/old Apple cache entries cannot hide originals or suppress stock requests on OFF. True Premium status is unchanged.

| Request | Before | After |
|---|---|---|
|Premium cloud single/chat|Forced Apple on iOS18+|Native Telegram/config-selected route|
|nonPremium enhanced cloud text|Apple only|Telegram text primary, one bounded Apple fallback|
|Enhanced secret selection/chat|Apple path with limited entry coverage|Explicit localOnly transport propagated through native screens|
|OFF|No toggle|Stock native path; enhanced cache ignored|
|Model absent/offline/error|Local failure only|Explicit failure; no original-as-success, no retry storm|
|Typed poll/transcript|Local plain fields, empty entities|Native typed fields, returned entities preserved|
|Rich or caption+completed transcript|Explicit unsupported|Still explicit unsupported for enhanced route; no flattening|

## Official and Swiftgram evidence

Upstream source of truth: TelegramMessenger/Telegram-iOS **fb0e62ba8a147f0821da6aa63c09da7d79a10111**,13.1.1. Public engine owner `submodules/TelegramCore/Sources/TelegramEngine/Messages/TelegramEngineMessages.swift` exposes native ID/text translation. Core `Translate.swift` calls `messages.translateText` with text and entities when IDs are absent. Availability of this API is source-proven; server entitlement/rate limits for a real nonPremium account require runtime evidence.

Genuine Swiftgram reference **e3a392272b182dbf975d4ac5fc33b40a5954d749**: Premium/default uses IDs, other paths translate text. It falls back to Google's URL-query endpoint on several failures; its forcePredict and broad banner gates are more permissive, while its asynchronous text install lacks Jerkgram's source-snapshot check. Its Google transport, global settings, random user-agent/logging and unbounded per-line networking were not ported. Jerkgram keeps current native UI and stronger edit freshness, with account preference and bounded routing. No new external endpoint or API key.

Exact clean owners, current19-owner translation hashes and23 verified Swiftgram source blobs were inspected before implementation. Persistent bounded source evidence remains under `/home/pixi/ChatGPT/iOS DEV/jerkgram-next/research/`; local reports are copied beside this report. Restored source replay also caught an incomplete old sparse wrapper: the TASK A API additions were rebased onto the actual Build176 wrapper to preserve existing transcription accumulation and independent features.

## Ownership and cost

Canonical GhostBaseSettingsState persists only actual deltas and hydrates account policy. Opening a Settings page stays read-only. Translation preference is nonvisual, so it does not trigger wallpaper/style invalidation. A bounded16-account cache reads canonical scoped preferences once on a miss and invalidates generations on change/eviction. No global Premium override, polling, swizzling or network work on main.

All enhanced cloud/manual work shares admission: active≤2; queued+active≤64 texts/128KiB; perjob≤16 texts/16KiB; deadline30s including queue. Dedup key contains account/generation/policy/source+entities/target/locality/download policy. Output cache≤256 entries/1MiB; full encoded entity payload counts toward budgets. Cancellation, timeout, response and policy change converge through one identity-checked terminal operation. Timer ownership is weak and cleared at completion. Apple's existing physical queue remains one active job and retains its own lifetime when framework cancellation cannot terminate the physical operation.

Message content fingerprint is separate from persisted policy provenance. Atomic compare-and-store checks source/edit identity, request cancellation and account generation immediately before success/failure installation. Renderers check account policy before their weak immutable-message fingerprint cache. Failure markers never represent originals as translated output and must remain eligible for a bounded later retry. Entity ranges must fit valid UTF16 boundaries; no source offsets are reused after translation. Apple fallback derives URL/mention offsets from output, and retains hidden links only when their label maps uniquely; ambiguous mapping fails explicitly.

Detection retains latest32/max16/prefix256/max4 and one-hour account cache; per-invocation recognizers, UTF16-safe masking and empty-winner rejection. App/ignored language and hidden-banner choices remain in force. No whole-history scan or unconditional banner. Visible scheduling, cancellation, edits and target changes use current native owners plus bounded Jerkgram admission.

## Source stage and verification

Authoritative changed file list and before/after hashes: `patches/jg131-translation-repair.sha256.json`. The dependent terminal stage follows all24Build176 stages, validates every parent before mutation, supports byte-exact idempotent reapply and a reverse parent view for immutable earlier verifiers. No prior patch is silently rewritten.

Baseline replay: clean pinned sparse upstream →24stages; all230 available saved physical owners matched, previous source verifier and Build176 regression runner passed. Credential configuration was not invoked. New source tests cover route separation, exact stock bodies, provenance/account checks, stage atomicity/idempotence/reverse and input corpus coverage. Native Foundation fixtures execute extracted production policy/admission/validity/masking with pinned SwiftSignalKit on the macOS gate; local Linux skips them explicitly. Source contracts supplement those fixtures and do not prove network, Postbox or UIKit runtime.

Native preflight/commit results are recorded below when available. No application build or device success is claimed by this draft.

## Runtime matrix / quality

`translation-corpus.json` contains32 INPUT cases: RU→EN, EN→RU, RU→DE, DE→RU × ordinary/slang/emoji/URL/@mention/newline/long/mixed. Outputs intentionally remain null/NOT_RUN. Compare Apple baseline and enhanced route on the same iPhone14Pro/iOS26.7.1 for meaning/negation/time/names, protected targets/entities, paragraphs and explicit error behavior. No LLM rewriting and no fabricated quality score.

Required: OFF-after-ON cache, real Premium vs nonPremium, separate accounts, single/chat, new/old visible scroll, mixed languages, target/app/ignored-language changes, edit during request, model absent/download consent, offline/flood/error, background/cancel/relaunch. Secret draft editor→Translate, selected input/message/gallery and cold profile/gift/story translation entry points must preserve locality and fallback initialization. No Ads remains runtime-unproven. App Icons/Download Boost/No Ads/Ghost/deleted-edit history/transcription/protected content/navigation are regression checks.

## Local terminal result — 2026-10-29

28changed owners, patch sha2568e05ff87b580635fe0573b21a60c2b647ce435cf6c1ff2dd950a3f0ac0773b8c. Every parent matched actual24stage Build176 replay. Exact apply, repeated apply and reverse prior contract gates passed. New designated24tests:21passed,3explicit nativeSwift skips,0failures/errors. Swift parsing/app compilation/device quality not run locally. Independent core and UI reviews each had one fix round, scoped re-reviews have no open findings. Whole-delta final review and macOS preflight are pending; this is not a device success statement.

A broad historical unittest discovery performed during core implementation had29failures/37errors outside the designated new gate (old workflow literals, old stage contracts and unavailable fixtures). Every name is retained in evidence/core-implementation.md; no full686suite-green claim. Immutable earlier contracts are evaluated on the reversed source view or before the new stage in CI.

Final independent review: no new actionable material defect. Reviewer independently verified all28output/parent hashes and designated24tests (21pass/3native skips). Native macOS source preflight remains the next gate; IPA build not started.

## First macOS preflight and focused repair

TASK A commit2843fd010c223ec949de9fe46d4c099b14b4a332; source-only run40889023877 FAILED two actual production fixture assertions. Previous175/176gates passed and all changed Swift owners parsed. Core entity range validation and UI language masking accepted an endpoint inside an emoji surrogate pair because Foundation Range(NSRange,in:) did not reject it on Swift6.4. The fixtures retained their expected outcomes. Both helpers now explicitly validate UTF16 code units at both endpoints; combining scalar boundaries remain permitted. Expanded native cases cover both invalid endpoints, complete emoji, combining sequences and sample clipping. Independent focused review found both addressed with no new actionable breakage.

Updated28owner patch sha25688e382764a84292c1ef2471840f0bedd5c8fad2b9139ac9d2b00be8df1eeef93; rebuilt from exact176parents, apply/reapply/reverse/previousgates PASS. Local terminal24tests:21pass/3explicitnative skips. Native rerun must establish success, including queue cases not reached after the first assertion failure. No IPA build started.
