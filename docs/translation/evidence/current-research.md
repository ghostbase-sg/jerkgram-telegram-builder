# Current Jerkgram translation: bounded TASK A research

Date: 2026-10-29. Read-only source audit; no implementation, branch, commit, build, device test, backend request, or translation-quality claim.

## Evidence and baseline

Requested modern green baseline: Build176, builder commit 2c3540a905d1e64fee668863eb0b65727dc5dfad, CI 40820248325, artifact 12876229430 (provided task baseline; this subtask did not re-query CI).

Materialized source inspected: /home/pixi/ChatGPT/iOS DEV/build176-wave1/source.
All 19 translation-stage owners match the current builder translation manifest's after_sha256, verified from bytes on disk. See evidence-verification.json and translation-stage-manifest.json. The stage's before hashes describe the preceding materialization stage, and must NOT be mistaken for pristine upstream.

The /tmp/jg175-audit source and git store are absent. Many Build176 symlinks are dangling. Instead, exact clean Official 13.1.1 files were fetched through the GitHub connector at fb0e62ba8a147f0821da6aa63c09da7d79a10111. Full selected files are preserved in official-fb0e62; selected line-numbered excerpts are in official-excerpts. Three selected clean-versus-current diffs are in diffs. Current selected source copies are in current-selected. Repo AGENTS.md and referenced CLAUDE.md were read from that exact upstream ref and preserved; no build or visual changes were performed.

Canonical reference: https://github.com/TelegramMessenger/Telegram-iOS/tree/fb0e62ba8a147f0821da6aa63c09da7d79a10111

## Root cause, stated at the level source proves

This is an unconditional Apple translation replacement on iOS 18+, not a backend policy. TranslateUI/Sources/Translate.swift:525-528 defines jerkgramLocalTranslationAvailable solely by OS availability. It does not check Premium, user preference, supported language pair, downloaded models, or service readiness.

That flag bypasses availability gates, redirects single-message plain text, and causes chat translation to enter a local-only early return. Premium users also lose their stock server route. Missing/unsupported models and rich/caption-transcription cases have explicit failure, with no Telegram fallback. These facts plausibly explain poor behavior and missing results. They do not prove that Apple's semantic output is worse for RU/EN/DE; that requires device corpus evaluation.

All Apple-success tuples/attributes use entities: []. No safe translated entity reconstruction exists. URLs and mentions might survive as text but formatting and explicit link destinations are lost. Reusing original entity offsets would be unsafe after translation.

## Current and pristine owners

All paths below are relative to submodules; line numbers are current Build176 unless marked Official.

| Owner / symbol | Current evidence | Pristine contrast |
| --- | --- | --- |
| TranslateUI/Sources/Translate.swift / canTranslateChats | 174-190: hardcoded local flag bypasses server config | Official 175-190: respects auto config and iOS system availability |
| Same / canTranslateText | 193-237: manual config OR local availability; recognition of first 64 characters | Official 192-237: config only; recognizer is global rather than new local instance |
| Same / jerkgramLocalTranslationAvailable | 525-528: OS18 only | Absent in pristine |
| Same / jerkgramTranslateText | 531-548: lazy service init, recognition first512, manual allowDownloads:true, empty entities | Absent in pristine |
| TranslateUI/Sources/ChatTranslation.swift / translateMessageIds | 141-217: skip outgoing, expand replies, force local on OS18+, catch errors | Official 141-216: local selected only by auto=.system; no JG freshness helpers |
| Same / chatTranslationState | 219-393: bounded native history recognition/cache largely unchanged | Official 218-392: same settings, 32 history entries, max16 qualifying incoming, same heuristic |
| TelegramCore/Sources/TelegramEngine/Messages/Translate.swift / _internal_translate | 32-78: native ID-or-text API with entities and neutral tone | Exact same clean API |
| Same / _internal_translateTexts | 174-217: native batched text API with returned entities | Exact same clean API |
| Same / _internal_translateMessages | 219-226: group IDs by peer | Same clean public internal shape |
| Same / jerkgramTranslateLocalMessages | 361-410: local per-message text, fingerprint compare-and-store | Absent in pristine |
| Same / _internal_translateMessagesByPeerId | 413-421: enableLocalIfPossible immediately returns JG local path | Official 283+: stock rich/poll/transcript/ID flow; system local only in plain branch |
| TelegramUI/Components/TextProcessingScreen/Sources/TextProcessingTranslateContentComponent.swift | 255-286: plain inputs use JG adapter; rich inputs fail, local errors visible | Official 282+: native component calls composeAIMessage; OFF should restore this exact stock path, even if ON deliberately uses neutral translation API |
| TelegramUI/Sources/ChatHistoryListNode.swift | 1128-1156: per-visible-message tracked disposables, generation, cooldown | Official1105-1109: native throttled batch startStandalone |
| Same / translation admission | 2409: isPremium OR autoTranslate OR local | Official2319: isPremium OR autoTranslate |
| SettingsUI/Sources/Language Selection/LocalizationListControllerNode.swift | 439-440,481-495: exposes entire-chat path to local nonPremium | Official439+: standard config availability; entire-chat state is premium-gated |
| TelegramUI/Components/TranslateHeaderPanelComponent/Sources/ChatTranslationPanelNode.swift | 182,216,235: gate broadened by local flag | Exact changes visible in translation patch |

The 19-owner translation manifest is the authoritative full changed-owner list. It covers translation core, detection, native settings/panel/text-processing/history and renderers (text, polls, interactive file, reply, pin, gallery, snippets, context menus). ChatController.swift:4530 is also a flag consumer outside those 19 translation-stage owners. A policy refactor must account for it.

## Single message, chat, detection, fallback, cache

Single: TextProcessingTranslateContentComponent uses native presentation. For .translate on OS18+, plain source enters jerkgramTranslateText; rich source fails. It guards generation, exact input and target before applying result, cancels when detached, supports retry, and displays localized local-unavailable error. Source recognition overrides provided fromLang whenever recognizer finds any language. Target uses native language selection, normalized before Apple.

Chat: translateMessageIds expands qualifying reply originals, excludes own authored primary messages, skips current target/fingerprint results, and routes engine translation. ChatHistoryListNode only gathers visible messages plus extendedRange=2 (3238+); incoming Cloud, no ads; grouped media text/rich is included. New arrivals/old scroll use the same visible admission. Per-message disposable map deduplicates; leaving visible range, background, target changes and edits cancel subscribers. Generation prevents late callbacks from updating wrong screen.

Detection remains the native heuristic: exclude service peer777000; require canTranslateChats and settings.translateChats or peer autoTranslate; ignored list defaults to app base language plus selected system languages. Cache is account engine itemCache keyed peer/thread, base language and timestamp, one-hour validity. On refresh scan latest32 history entries once, require >1 history entry, process up to16 incoming qualifying messages, prefix256, weight prediction by full message length. Language with most characters wins. Empty prediction is not explicitly rejected. No forcePredict parameter exists here. Mixed languages and one long same-language message can dominate the banner. A cached ignored winner can suppress banner until settings/base/timestamp changes. Do not remove ignored-language policy globally.

The chat detection entity masking uses entity offsets as Swift character offsets against a Character prefix, though Telegram entity ranges are UTF16. This is inherited upstream, not newly caused by JG. It can mis-mask emoji/combining text; any repair should safely convert UTF16 ranges after truncation, and recheck cleaned text length rather than original message.text.count. A per-invocation recognizer and utility queue would avoid shared recognizer concurrency and main-queue work; current stock chat recognizer remains global (ChatTranslation.swift:139).

Apple service: Translate.swift:265-394 queue has one physical active job, <=16 items and <=16KiB per job; queued+active <=64 items/128KiB. It deduplicates identical texts/source/target/download flag and uses opaque indices toward framework. Result LRU <=256 items/1MiB, keyed actual texts/source/target; physical task is not abandoned when subscribers cancel/timeout. Logical timeout300s; cancellation preserves physical slot until framework returns. This bounds concurrency but a framework hang can monopolize the only slot.

Downloads: manual explicit request allowDownloads=true. Automatic service protocol uses false; installed-language status is checked asynchronously; iOS26 uses TranslationSession(installedSource:target:) for silent automatic work. Preserve this Build175 consent distinction. Runtime must still validate system UI behavior on iOS18-25.

Failure is explicit nil/error and unavailable attributes, never original-as-success. No active Telegram/third-party fallback in current JG branch. Official Translate.swift already contains alternativeTranslateText at440+ (current550+), a Google-style URLSession GET sending text/language query in URL; its mere presence does not prove this JG native component calls it. Do not wire it into enhanced fallback without privacy decision.

Stored translations: TranslationMessageAttribute records source fingerprint, unavailable flag and target in account postbox. Content fingerprint includes text/entities, poll/options/solution, transcript/pending, rich-presence bit, deleted flag. Compare-and-store prevents stale edit results; renderers call isValidForMessage and hide invalid tagged results. Unfingerprinted native attributes count valid in renderers, but enhanced scheduler insists on fingerprint and retranslates them. One persisted translated variant per message is retained; this is not the 1MiB process LRU. Postbox storage lifetime follows normal message storage; there is no separate JG aggregate postbox byte cap. Caption+completed transcript and rich messages deliberately fail to avoid putting a caption into a transcript or flattening structured content.

## Missing toggle and canonical storage

No translation preference exists in current GhostBaseSettingsState or JerkgramSettingsV1; no JG settings key is consulted by backend availability. Telegram's own TranslationSettings exists, but controls showTranslate, translateChats, ignoredLanguages, rather than enhanced backend selection.

The actual live canonical JG owner is SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift:
- GhostBaseKey starts65; message keys80+.
- jerkgramScopedSettingsKey432 returns jerkgram.account.<peer>.setting.<key>.
- jerkgramStateValues508+ projects state; jerkgramPersistChangedSettings560+ persists deltas and updates account policies.
- jerkgramActivateAccountSettings632+ restores account projection; GhostBaseSettingsState.readStored700+ loads scoped values.
- .messages page entries2164+.
JerkgramSettingsStore.swift is a small V1 archive model, not the full live controller owner. Do not add an isolated defaults key there and assume runtime consumers see it.

Feasible policy precedent: TelegramCore/Sources/Network/JerkgramDownloadBoostPolicy.swift:11-48 and Utils/JerkgramSponsoredContentPolicy.swift:5-33 use canonical scoped key, locked bounded per-account cache and explicit update. Copy the architecture, not unrelated feature behavior. Account parameter must reach all policy checks; the current context-free global availability var cannot represent account-scoped ON/OFF simultaneously.

## Recommended bounded route (proposal, not implemented)

Name Enhanced Translation / Улучшенный перевод, Jerkgram > Messages. Default ON to preserve existing nonPremium functionality during migration, with OFF explicitly restoring clean stock behavior. Apple-only naming would misdescribe a native Telegram text primary route.

OFF: pristine13.1.1 availability/premium gates, native ID/auto-system selection and native text-processing action; bypass enhanced schedulers and enhanced result presentation. Merely changing the availability var is insufficient: core currently interprets enableLocalIfPossible with JG early return, history scheduling is changed unconditionally, and previously tagged JG attributes can still display. Hide/invalidate only JG provenance results on OFF or provide explicit policy-aware acceptance; keep originals and unrelated attributes.

ON Premium: keep native/default ID path and app-config-selected native behavior; do not hardcode local for all Premium accounts.

ON nonPremium: native Telegram text translation primary, with current bounded Apple text backend as fallback where appropriate and language installed (manual downloads only by existing explicit action). This is a feasible source API route, not a promise of server entitlement or better semantic output. _internal_translate already sets flags bit1 and TextWithEntities when no peer/messageId is supplied. _internal_translateTexts already handles text batches. Preserve associated entities returned by Telegram. Do not send secret chat content to cloud automatically; use existing privacy/native semantics and installed local path for explicitly local content.

Core recommendation: a small explicit account-scoped policy and per-request route enum/flag distinct from stock enableLocalIfPossible. Existing engine's bool already means stock system translation and must not be redefined to imply JG ON. At context boundary query real Premium and ON state; propagate chosen route, or compute policy in core using account-scoped data, without global premium override. A new helper in the existing Translate.swift core can be exposed through the confirmed public TelegramEngine wrapper only after its precise owner/signature is fetched; wrapper source is currently dangling and two guessed connector paths were 404. Core signatures are confirmed, wrapper owner is not claimed confirmed.

Fall back once on actual backend availability/alternative/generic failure; do not indiscriminately retry limitExceeded/FLOOD_WAIT, invalidLanguage, empty or too-long input. _internal_translate maps these separately; .tryAlternative exists for TRANSLATIONS_DISABLED_ALT. Network implementation maps all otherwise unknown errors to generic, so offline vs entitlement is not currently a distinct type. No retry loop, no silent external Google route, no API keys.

Preserve fingerprint compare-and-store for text results from either backend, include backend/policy version in provenance and validity so old apple-v1 is not mistaken for new text route, validate result count/order and nonempty output, preserve per-request cancellation and target checks. Current ephemeral cache contains full source/target and account/message keys; maintain equivalent keys for new backend. For Apple fallback rebuild only entities derived from translated text or mapped protected tokens; never copy source offsets. Keep rich/caption/transcript incompatibility explicit unless a typed native representation is implemented.

Detection repair: add explicit bounded forced prediction only when enhanced user/native action needs recognition despite ordinary state gating, reuse32/max16 limits, keep app language/ignored languages, reject empty source, keep per-message recognition for actual mixed-language translation. Do not always display banner or scan full history. Policy/toggle changes should cancel pending work, invalidate route-mismatched results, and refresh native state once without loops.

Runtime quality remains unmeasured. Corpus must compare current Apple vs proposed Telegram-text route on RU→EN, EN→RU, RU→DE, DE→RU: ordinary, slang, emoji, URL, mention, newline, long and mixed texts. Include caption+transcript, poll, rich unsupported, edit-during-request, offline, model absent, target switch, account switch and OFF-after-ON cache. Success requires meaning, protected text/entities, native UI and error behavior; structural verification alone does not establish translation quality.

## Material remaining uncertainty

Telegram text API route existence and signatures are source-proven; nonPremium entitlement/limits and RU/DE runtime quality are not. Apple language/model availability and fallback UI consent need actual device execution. The real TelegramEngine public wrapper owner/signature must be fetched before implementation. No product decision is required to exclude third-party Google or retain minimum iOS; the proposed policy does both.

