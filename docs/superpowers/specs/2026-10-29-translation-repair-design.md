# Translation repair — TASK A design

## Intent and constraints

Repair the existing translation route on Official Telegram iOS13.1.1 (fb0e62ba8a147f0821da6aa63c09da7d79a10111), preserving native UI and all independent Jerkgram features. Current GREEN baseline is Build176 / 2c3540a905d1e64fee668863eb0b65727dc5dfad, with evidence-only successor21fe2239738836371caa9727c2b7256e713dd44f. User supplied a bounded implementation spec and delegated routine choices/order. No new chat/project, no minimum iOS change, no global Premium override, no credentials, no third-party translation transport.

## Approaches and decision

1. Keep Apple-only and add toggle: smallest, leaves unavailable-model failures and displaces Premium native route.
2. Copy Swiftgram Google fallback: broader languages but sends text in third-party query URLs, adds unbounded requests and privacy behavior. Excluded.
3. Chosen: Telegram native path for real Premium; Telegram text translation for enhanced nonPremium with bounded installed Apple fallback. Use the current consent-aware Apple service and native translated-message UI. Backend entitlement and semantic quality remain runtime requirements.

## Preference and presentation

Canonical GhostBaseSettingsState per-account preference enhancedTranslation, default ON to preserve existing nonPremium functionality. Jerkgram → Messages: Enhanced Translation / Улучшенный перевод. Honest footer: Telegram text translation with system fallback; does not confer Premium. Account policy uses bounded locked cache and canonical scoped key, updated only on account activation/preference changes, no per-bubble I/O. OFF restores pristine availability, Premium gates, core local meaning and single-message native compose action. Jerkgram-tagged cached attributes must be hidden on OFF without scanning history; account parameter must accompany validity checks. Ungagged stock attributes stay valid. Preference change cancels stale work and refreshes the relevant native state once.

## Routing, limits and freshness

Explicit enhanced route distinct from stock enableLocalIfPossible. Premium/default uses pristine engine route; nonPremium enhanced uses native text API without IDs, preserves returned entities, and falls back once to current Apple queue only on availability/alternative/generic failure. No fallback retry on flood/limit, invalid language, empty or too-long input. Secret/local-only content must never gain cloud transport; preserve native privacy semantics. Rich/poll/transcript paths require native typed semantics; never flatten caption into transcript. A failure remains failure, never original-as-success.

Preserve current per-visible-message cancellation/dedup/generation and edited-message compare-and-store fingerprint. Bound Telegram-text work alongside Apple: finite active concurrency, finite queued input/count, timeout, cancellation, bounded LRU keyed account/source/target/entities/policy. Reject result count mismatch, empty output and invalid UTF16 entity ranges. Never reuse source entity offsets after translation. New policy provenance distinguishes old Apple attributes. Preserve manual-only model-download consent and auto installed-only Apple behavior. No full-history scanning or synchronous I/O/network on main.

## Language detection and whole-chat

Preserve native ignored/app languages and hide-banner preference. Explicit enhanced prediction can bypass ordinary feature availability only, not ignored languages. Keep latest32/max16/prefix256 bounds and one-hour account cache; avoid global recognizer races, fix UTF16 masking, reject empty predictions. New messages, old visible scroll, edit, target/account/toggle changes reconcile through bounded native visible admission. Do not always show banner.

## Verification and delivery

Separate source-dependent, idempotent TASK A stage after Build176; validate all parent hashes before mutation, expose reverse parent view for existing gates. Exact clean owners and public engine signatures fetched before editing. Red/green policy/routing/freshness tests, bounded corpus32 cases (4 directions ×8 kinds), source gates, clean replay and native compilation at combined build after B/UI. Separate TASK A commit before TASK B. Runtime matrix includes OFF-after-ON cache, two accounts, real Premium, offline/error/model absent, entities/links, mixed chat, edits and target switches. Corpus contains input/expected invariants, not fabricated backend outputs. Device iPhone14Pro/iOS26.7.1; no runtime quality claim without actual run.

## Source evidence

Persistent current/official research: ../jerkgram-next/research/current-translation/REPORT.md; genuine Swiftgram e3a392272b182dbf975d4ac5fc33b40a5954d749 research in ../jerkgram-next/research/swiftgram-translation/REPORT.md. Public wrapper confirmed: submodules/TelegramCore/Sources/TelegramEngine/Messages/TelegramEngineMessages.swift, translate(text:toLang:entities:tone:messageId:), translate(texts:toLang:tone:), translateMessages(messageIds:fromLang:toLang:enableLocalIfPossible:tone:).
