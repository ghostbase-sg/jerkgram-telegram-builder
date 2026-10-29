# TASK A — canonical preference and UI consumers

## Implementation

`GhostBaseSettingsState.enhancedTranslation` is account scoped and defaults ON. Messages contains bilingual Enhanced Translation / Улучшенный перевод and a footer describing Telegram text translation/system fallback without claiming Premium. The key participates in canonical state values/delta persistence. Policy update occurs on activation and real state change; opening a settings page remains a pure load. The nonvisual key does not join playback/style/metadata invalidations.

`jerkgramEnhancedTranslationEnabled(context:)` replaces the context-free public flag. `AccountContext.isPremium` is confirmed in the pinned protocol and in AccountContextImpl's actual engine account-peer subscription, not fabricated. Premium cloud single/chat routes remain native. NonPremium ON uses the explicit enhanced core interface; OFF preserves native manual/system availability, composeAIMessage, Premium checks and stock `enableLocalIfPossible` interpretation. Existing visible admission/cancellation bounds remain for scheduling.

All existing translation-patch plain-text/caption/poll/transcript render/copy/scheduler boundaries pass the account identity to production `isValidForMessage`. This means old tagged attributes on OFF are hidden and cannot suppress a stock request. Loading-failure helpers likewise receive account identity. Fingerprint/policy validation is owned by core.

Unchanged instant-page readers are outside these claims: enhanced routes do not generate translated instant pages.

The single screen captures input/target/account/request generation and account policy generation before delivery. Policy notifications cancel/reset work and refresh native content/history subscribers. Observers are account filtered and disposed. Detached selection views do not start new policy-triggered work.

Secret chat/input/gallery selections propagate `localOnly` through the actual shared screen protocol/factory, initializer, sheet and component state into enhancedTranslate. Existing public calls retain their old signature via a delegating protocol extension/default init argument. ON secret selection uses installed/system-only routing even for a Premium account; Premium cloud selections use native routing. Core enforces localOnly transport. OFF retains native behavior.

Detection keeps latest32/max16/prefix256/max4/one-hour bounds, ignored/app languages and native hidden-banner gate. Foundation masking works in UTF16 with stable offsets for overlapping entities and end-of-sample ranges; recognizers are per invocation and empty winners are rejected. `forcePredict` is an explicit optional detection API; ordinary banner subscription does not force prediction or override ignored languages. No unbounded history scan or unconditional banner added.

The pristine upstream dormant Google helper remains byte-for-byte; enhanced routing has no call to it. No new external transport or credentials.

## Public interfaces consumed/added

- Core `JerkgramTranslationSettings.{preferenceKey,scopedKey,enabled,update,generation}` as agreed with core owner.
- Core `enhancedTranslate(text:entities:fromLang:toLang:allowLocalDownloads:localOnly:)` and separate `translateMessages(...enhanced:)`.
- Core `TranslationMessageAttribute.isValidForMessage(_:accountPeerId:)`, unavailable helpers with explicit account.
- UI `jerkgramEnhancedTranslationEnabled(context:)`, `jerkgramTranslationPolicyChanges(context:)`.
- SharedAccountContext screen factory new `localOnly` requirement with existing-signature forwarding extension. Pinned `AccountContext/Sources/AccountContext.swift` fetched from exact fb0e62 source and saved as before/source before narrow edits.

## Verification evidence and limitations

Focused test module `tests/test_jg131_translation_ui_repair.py`: initial RED, five failures on the baseline before edits; final GREEN five source contracts, one native production Foundation mask test skipped because this Linux environment has no Swift executable. The source contracts are supplemental evidence, not runtime proof. The native fixture extracts the actual production helper and covers emoji/UTF16 URL offsets, overlap, invalid surrogate offsets, negative ranges, truncation and all-masked content when run on a Swift host.

Command: `JERKGRAM_TRANSLATION_REPAIR_SOURCE=<task-a/source> python -m unittest discover -s tests -p test_jg131_translation_ui_repair.py -q` from builder. Tests support explicit environment path, materialized builder `work/swiftgram-src`, and development fixture fallback. Grep review found no old public flag or context-free validity calls outside core. No heavy build, commit or push performed by this owner.

Actual iOS syntax/type checking, model availability/download consent, backend entitlement/translation quality, OFF-after-ON rendering, secret gallery transport, edit/target/account switching, scroll bounds and full runtime matrix remain required. Source checks do not establish device success.

## Changed UI owners

- `submodules/AccountContext/Sources/AccountContext.swift`
- `submodules/GalleryUI/Sources/ChatItemGalleryFooterContentNode.swift`
- `submodules/GalleryUI/Sources/GalleryController.swift`
- `submodules/GalleryUI/Sources/Items/ChatImageGalleryItem.swift`
- `submodules/ListMessageItem/Sources/ListMessageSnippetItemNode.swift`
- `submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift`
- `submodules/SettingsUI/Sources/Language Selection/LocalizationListControllerNode.swift`
- `submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift`
- `submodules/TelegramUI/Components/Chat/ChatMessagePollBubbleContentNode/Sources/ChatMessagePollBubbleContentNode.swift`
- `submodules/TelegramUI/Components/Chat/ChatMessageReplyInfoNode/Sources/ChatMessageReplyInfoNode.swift`
- `submodules/TelegramUI/Components/Chat/ChatMessageTextBubbleContentNode/Sources/ChatMessageTextBubbleContentNode.swift`
- `submodules/TelegramUI/Components/TextProcessingScreen/Sources/TextProcessingScreen.swift`
- `submodules/TelegramUI/Components/TextProcessingScreen/Sources/TextProcessingTranslateContentComponent.swift`
- `submodules/TelegramUI/Components/TranslateHeaderPanelComponent/Sources/ChatTranslationPanelNode.swift`
- `submodules/TelegramUI/Sources/Chat/ChatControllerLoadDisplayNode.swift`
- `submodules/TelegramUI/Sources/ChatController.swift`
- `submodules/TelegramUI/Sources/ChatControllerContentData.swift`
- `submodules/TelegramUI/Sources/ChatHistoryListNode.swift`
- `submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift`
- `submodules/TelegramUI/Sources/ChatPinnedMessageTitlePanelNode.swift`
- `submodules/TelegramUI/Sources/SharedAccountContext.swift`
- `submodules/TranslateUI/Sources/ChatTranslation.swift`
- `submodules/TranslateUI/Sources/Translate.swift`


## UI review round 1 repairs

Verified `UI-REVIEW.md` against production owners before changes. Snapshots of all six touched source owners, test module and this report are in `task-a/ui-review-before/`. The additional `ChatControllerNode.swift` and `JerkgramStrings.swift` owners already have physical Build176 `before` copies; those were retained.

- Secret draft `ChatControllerNode.openAICompose(mode: .edit)` now carries the chat namespace locality into `TextProcessingScreen`. The existing sheet/content propagation reaches the Translate tab without changing unrelated compose/stylize actions.
- Four successful-cache admission shortcuts (reply/original in ChatTranslation, regular/grouped history entries) now explicitly reject `jerkgramUnavailable`, retaining target/account/fingerprint validation. A failed marker no longer permanently suppresses retry after existing bounded cooldown/admission; loading-placeholder validation remains unchanged. A valid untagged stock success still suppresses duplicate work.
- Shared manual `jerkgramTranslateText` request adapter installs the existing system service only if absent and a host view exists, on the main queue using SwiftSignalKit `runOn`. Both direct and factory screens call that adapter through their common translation component, so chat navigation is no longer a prerequisite for Apple fallback. Core dispatch remains asynchronous/bounded; manual download permission remains explicit true and automatic translation remains installed-only.
- RU/EN generic failure text now mentions connection, language/system model availability and unsupported formats, without incorrectly asserting that only on-device translation failed.

Focused command from builder:

`JERKGRAM_TRANSLATION_REPAIR_SOURCE=/home/pixi/ChatGPT/iOS\ DEV/jerkgram-next/task-a/source python -m unittest discover -s tests -p test_jg131_translation_ui_repair.py -q`

RED before fixes: 11 tests, 5 failures, 2 skips (four new regression contracts plus the adjusted adapter integration contract). GREEN after fixes: 11 tests, 9 passed, 2 skipped. `python -m py_compile tests/test_jg131_translation_ui_repair.py` passed.

New source integration tests cover secret draft locality/Translate propagation, all four cache skip sites, cold manual host setup/queue and adapter use, and truthful failure text. The native retry fixture extracts the actual four production predicates and checks failure-marker eligibility, current success, changed target and stale-validator outcome. It stubs external containers/core validity (core has separate tests); it does not substitute a copied admission predicate. Both native retry and Foundation mask fixtures skip on this Linux host because Swift is absent. Native compile, cold profile/gift/story Apple fallback, bounded retry behavior and secret draft transport still require macOS/device execution. No historical/full test run, heavy build, commit or push was performed in this repair round.

Additional UI owners introduced by this round:

- `submodules/TelegramUI/Sources/ChatControllerNode.swift`
- `submodules/TelegramPresentationData/Sources/JerkgramStrings.swift`
