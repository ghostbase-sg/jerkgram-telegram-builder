# Swiftgram translation reference — current source audit

Scope: TASK A architecture research only. No product source, branch, build, translation request, or outbound message was changed. No text was sent to a translation service.

## Provenance

Connected GitHub `get_repo` established official public repository `Swiftgram/Telegram-iOS`, default branch `master`. Connected GitHub `fetch` of [branches/master](https://api.github.com/repos/Swiftgram/Telegram-iOS/branches/master) returned **e3a392272b182dbf975d4ac5fc33b40a5954d749**, authored/committed 2026-10-24T22:02:08Z, message “Make call confirmation wrapper capture explicit”. Rechecked 2026-10-29; the historical pin is still current at this check. Files were fetched individually at this immutable SHA, not inferred from old local copies. `manifest.json` lists original Git blob SHAs and exact source URLs. Every saved source byte sequence was checked against its Git blob SHA.

`work/swiftgram-src` was never used. Prior build170 research was used only to discover paths, then relevant files were fetched again at the verified SHA.

All source links below have prefix:
https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/

## Routing actually implemented

| Entry / condition | Initial route | Error fallback |
|---|---|---|
| `ChatTranslation.translateMessageIds`, Premium + backend default + viaText=false | Telegram message IDs (with optional system auto configuration) | forceGTranslate=true text path |
| Same, non-Premium OR viaText=true OR selected alternative backend | `translateMessagesViaText` | chosen backend's fallback below |
| Text path + backend default | Telegram `messages.translateText` with text, no message IDs | Google |
| Text path + backend gtranslate | Google | error, swallowed by outer chat wrapper |
| Text path + backend system | internal Apple/system service | Google if unavailable, nil, missing/empty result, or error |
| Engine single/multiple text translation | `sgWrappedTranslateSingle/Multiple` chooses default / Google / system | default and system errors -> Google |

Exact owners:
- [ChatTranslation.swift#L153](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/submodules/TranslateUI/Sources/ChatTranslation.swift#L153): route selection lines 155–159; reply inclusion and Set dedup; matching target translation skip; own-author skip except quick translate; collects local text. Rich text, polls, audio transcription, missing-local IDs are only supported on message-ID branch. Non-Premium text route cannot translate those nontext-only forms using this method.
- [SGTranslate.swift#L199](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/Swiftgram/SGTranslate/Sources/SGTranslate.swift#L199): `sgTranslateRawText` confirms default means Telegram raw-text API, not immediate Google.
- [Translate.swift#L45](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/submodules/TelegramCore/Sources/TelegramEngine/Messages/Translate.swift#L45): `_internal_translate` chooses peer/id flags only if both are supplied, otherwise text-with-entities; normalizes target. FLOOD_WAIT, invalid ID, empty/too-long text, invalid language and disabled-alt map to TranslationError.
- [Translate.swift#L296](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/submodules/TelegramCore/Sources/TelegramEngine/Messages/Translate.swift#L296): ID implementation separates rich messages, polls, transcriptions; system result count/nonempty checks precede native attribute construction.
- [TelegramEngineMessages.swift#L739](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/submodules/TelegramCore/Sources/TelegramEngine/Messages/TelegramEngineMessages.swift#L739): engine single-message API may still pass messageId into default wrapper; this differs from the explicitly non-Premium-aware whole-chat helper. Multiple-text wrapper at line 786.

Nuance: `translateMessagesViaText(... enableLocalIfPossible: ...)` accepts that argument but its body at SGTranslate.swift 240–243 does not use or forward it. Explicit backend `.system` drives its system path. Do not assume the auto-local flag makes the default non-Premium text path local.

Chat outer catches complete silently on failure. Default/system wrappers fall back on errors; a default API success containing nil is not explicitly converted into an error by all wrappers. Thus “has fallback” is not proof every incomplete response is handled.

## Exact Google data flow and privacy

[SGGTranslate.swift#L8](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/Swiftgram/SGGTranslate/Sources/SGGTranslate.swift#L8):
- Shared ephemeral URLSession; asynchronous URLSessionDataTask, cancellation on dispose.
- HTTPS **GET** endpoint `https://translate.googleapis.com/translate_a/single`.
- Query: `client=gtx&sl=auto&tl=<mapped target>&dt=t&ie=UTF-8&oe=UTF-8&otf=1&ssel=0&tsel=0&kc=7&dt=at&dt=bd&dt=ex&dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=ss&q=<percent-encoded text>`.
- Explicit fromLang is ignored by Google helper; source is always auto.
- Target mappings: zh-hans/zh -> zh-CN, zh-hant -> zh-TW, he -> iw; lowercases/strips raw suffix and most region suffixes.
- Random hard-coded iPhone Safari or Windows Chrome User-Agent. No API key, authentication token, Telegram peer/message ID, explicit account identity or original entity payload is added by this code.
- Text is split by newline; each nonempty trimmed line becomes a parallel request. Leading whitespace is reattached, empty lines retained, trailing whitespace on nonempty lines removed. First elements of returned segment arrays are concatenated. HTTP non-200, absent/malformed/empty results -> network/generic error.
- Full source text, URLs, @mentions etc. in each line are transmitted to Google in the URL query. HTTPS protects transport; recipient still receives the text and connection metadata/IP. Ephemeral session does not make it on-device or prevent recipient-side retention/logging. URL query placement may expose content to URL-level diagnostics. No dedicated consent check appears in these audited helpers; fallback can occur even when user selected system/default.
- Existing translation diagnostic wrappers log lengths/language/error, not the full source; separate language-recognition debug logging in ChatTranslation.swift can log sampled text for some languages. Do not import that logging policy.

No translation endpoint was contacted during this audit.

## Detection, banner, target selection

[ChatTranslation.swift#L270](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/submodules/TranslateUI/Sources/ChatTranslation.swift#L270):
- Excludes Telegram service peer 777000.
- App language strips -raw; default ignored languages are app + system languages, or explicit ignored list.
- Recognition reads recent history with **count 32**, takes first view with >1 entry, uses at most **16** eligible incoming messages, each text >=10 chars. NL recognizer sees prefix **256** chars and max **4** hypotheses; supported languages only, weighted by full original message length. Summarization fromLang can supply language without recognition.
- Cached detection state is per account engine item cache, key peer ID + optional thread ID, stores base/from/to language, timestamp, enabled flag. Valid for **one hour** with matching app base language.
- forcePredict bypasses settings.translateChats/autoTranslate absence and ignored-language output suppression. It does not erase all guards: service peer/iOS/canTranslateChats remain.
- Entity removal for recognition uses original offsets against Swift String character counts; that code should not be copied blindly because Telegram entity offsets are UTF-16. It also rechecks original message length rather than filtered text length and excludes removal ending exactly at text.endIndex.

[Translate.swift#L167](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/submodules/TranslateUI/Sources/Translate.swift#L167): canTranslateChats ends `chatTranslationAvailable || true`, explicitly broadening availability.

[ChatControllerContentData.swift#L2233](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/submodules/TelegramUI/Sources/ChatControllerContentData.swift#L2233): banner eligibility includes `|| true` alongside Premium/suggestion/autotranslate, but honors translation hidden. Requires nonempty predicted source and source != app base unless enabled. Separate forcePredict subscription at 2271 supplies predictedChatLanguage once, independently of visible banner. Default target is app base language; stored per-chat/thread toLang overrides it.

[ChatControllerLoadDisplayNode.swift#L4322](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/submodules/TelegramUI/Sources/Chat/ChatControllerLoadDisplayNode.swift#L4322): native toggle updates cached isEnabled; native language selection normalizes langCode, updates toLang and enables translation; ignored language updates canonical translation settings.

## Bounds, cache, edits and entities

- [ChatHistoryListNode.swift#L3161](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/submodules/TelegramUI/Sources/ChatHistoryListNode.swift#L3161) translates visible messages plus **2** neighboring entries each side, excludes ads, noncloud and own-author messages; skips matching TranslationMessageAttribute.toLang. New/old messages entering that range are scheduled, not all history.
- Translation processing manager is created with submitInterval **1 second**, default delay **1 second** (line 661), hands Set IDs to helper at 1111.
- [ChatMessageThrottledProcessingManager.swift#L6](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/submodules/TelegramUI/Sources/ChatMessageThrottledProcessingManager.swift#L6): Set buffer dedups pending IDs; processed timestamp/list trims first **200** entries when list count >**1000**. This is throttle bookkeeping, not a bounded translation-text cache or an in-flight concurrency limiter. Repeated IDs can be resubmitted after interval.
- SGTranslate.swift 173–197 creates a signal per message and combineLatest; SGGTranslate creates a request per nonempty line. No explicit max concurrent requests, max queued items, response bytes, text bytes, custom timeout or explicit retry/backoff budget in these helpers. URLSession defaults may constrain transport but are not an app-level bound.
- SGGTranslate.swift 153 contains `gtranslateSplitTextBySentences(maxChunkLength:1500)`, **unused by gtranslate/gtranslateSentence**. It is not proof of a 1500-char cap and does not split a single oversized sentence.
- Successful text result replaces the message's TranslationMessageAttribute (one current target, persisted with message) at SGTranslate.swift 173. No standalone bounded LRU/size/TTL translation result cache in these owners; message database lifecycle governs persistence. Detection TTL is a separate cache.
- When backend supplies no entities, whole-chat path regenerates entities from translated output using generateTextEntities(.all). It does not reuse source offsets; semantic formatting/text links/custom emoji are not thereby guaranteed preserved. Direct single wrappers can return empty entities.
- [ServerMessageMerge.swift#L22](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/submodules/TelegramCore/Sources/State/ServerMessageMerge.swift#L22): retains previous translation only when source text AND entities are unchanged, otherwise server merge drops it. This is useful edit invalidation.
- **Race remaining in Swiftgram text path:** asynchronous result installation updates current message without comparing its current source text/entities with request snapshot. An edit arriving while translation is in flight can receive stale translation. Cache skip keys on toLang only and has no source fingerprint. This should be fixed in a Jerkgram adaptation, not replicated.

## Quick translation and settings

[ChatMessageBubbleItemNode.swift#L7333](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/submodules/TelegramUI/Components/Chat/ChatMessageBubbleItemNode/Sources/ChatMessageBubbleItemNode.swift#L7333):
- Uses associatedData.translateToLanguageSG or app language; passes fromLang=nil, forQuickTranslate=true to normal helper.
- On success stores QuickTranslationMessageAttribute(original text/entities), replaces local message text/entities with translated result. Next press restores originals. Native translation attribute remains in this restoration code (comment mentioning removing Telegram translation data does not match actual filter).
- This replacement behavior creates additional edit/cache semantics and is unnecessary for a narrow native translated-message presentation repair.

[SimpleSettings.swift#L232](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/Swiftgram/SGSimpleSettings/Sources/SimpleSettings.swift#L232): backend enum default/gtranslate/system; default backend .default (325), quickTranslateButton false (273); backend stored via @UserDefault (584), translationBackendEnum invalid-value fallback .default (637). UserDefault defaults to .standard, is globally shared singleton settings, unlike per-account message/detection state.

[SGSettingsController.swift#L221](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift#L221): dedicated Translation section has backend selector, fallback notice if backend not Google, quick button toggle and native language-settings disclosure, no-Premium-needed notice. Backend action sheet at 635 offers enum cases, hiding system before iOS 18.

[TranslationSettings.swift#L10](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/submodules/TelegramUIPreferences/Sources/TranslationSettings.swift#L10): canonical Telegram showTranslate=false, translateChats=true, ignored languages nil, shared accountManager settings.

[Translate.swift#L250](https://github.com/Swiftgram/Telegram-iOS/blob/e3a392272b182dbf975d4ac5fc33b40a5954d749/submodules/TranslateUI/Sources/Translate.swift#L250): system implementation uses iOS 18 TranslationSession, async translations, explicit language pair configuration and nil for auto-source; validates through SG wrappers. Queue-backed task container has no explicit hard cap. Host installed on iOS 18 in ChatControllerLoadDisplayNode 695–699. No minimum-target increase is necessary to availability-gate such a route.

## Narrow patterns worth adopting

1. One Jerkgram policy owner controls opt-in behavior; OFF returns Official 13.1.1 paths exactly. Preserve real Premium state.
2. Keep native translation presentation and canonical settings; choose raw-text path for non-Premium cloud text instead of forcing an entitlement-bound ID call.
3. Separate bounded local source prediction from banner presentation. Honor ignored languages and translation-hidden state; do not copy unconditional `|| true`.
4. Consider Official 13.1.1's system service only after its current owners/signatures/language support are verified. System unavailable/incomplete should produce an explicit policy outcome; an implicit Google fallback means “Local Translation” is misleading.
5. If adding Google, explain that text is sent to Google and make that an informed backend policy choice. Do not transplant Swiftgram's URL obfuscation, random UA or logging.
6. Add global concurrency/queue limits, dedup by account+message+source fingerprint+target+backend, finite request timeout, bounded cache, bounded supported text splitting. Discard in-flight responses when source/entities or generation changed.
7. Regenerate output entities rather than copying stale source offsets; validate URL/mention/emoji/newline behavior with corpus.
8. Availability/fallback architecture can improve success rate. This audit contains **no evidence Google/system produces better linguistic quality**; bounded RU/EN/DE corpus and device runtime comparison remain required.

No translation quality or device runtime success is claimed.

