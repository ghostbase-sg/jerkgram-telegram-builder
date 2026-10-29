# TASK A UI/settings/detection independent review

Reviewed `task-a/before` against `task-a/source`, the TASK A specification, implementation report and design. Scope excludes the concurrently changing core implementation; core public contracts and attribute semantics were read where required to assess UI consumers. No source edits, builds or commits performed.

## Findings

### P1 — Propagate secret-chat locality through the compose screen's Translate tab

**Owner:** `submodules/TelegramUI/Sources/ChatControllerNode.swift`, `openAICompose()`, initializer beginning at line 4929; `inputText: composedInputText` at line 4996.

This direct `TextProcessingScreen(mode: .edit(...))` initializer omits the newly introduced `localOnly` argument and therefore uses `false`, including for a secret-chat draft. `.edit` exposes a Translate tab (`TextProcessingScreen.swift:706–725`), which constructs the same translation component and copies `component.localOnly` into `translateState` at line 834. With Enhanced Translation ON, a nonPremium account subsequently calls `enhancedTranslate(...localOnly: false)` (`TextProcessingTranslateContentComponent.swift:279`), admitting that secret draft to the cloud text route. A Premium account instead reaches native cloud composition because its locality flag is false. The newly protected selected-message/input/gallery entry points do not cover this separate compose entry point.

**Minimal fix:** Pass `localOnly: self.chatLocation.peerId?.namespace == Namespaces.Peer.SecretChat` at this initializer, and include this `.edit` → Translate transition in the secret-path source check. Retain the existing behavior of unrelated compose/stylize operations; this finding concerns translation locality.

### P2 — Failure markers are treated as successful cached translations and cannot retry

**Owners:** `submodules/TranslateUI/Sources/ChatTranslation.swift`, `translateMessageIds`, lines 158 and 170; `submodules/TelegramUI/Sources/ChatHistoryListNode.swift`, visible admission, lines 3265 and 3286.

All four shortcuts now skip a message whenever target language and `isValidForMessage` match. The former enhanced shortcut used `jerkgramLocalTranslationIsCurrent`, whose success check explicitly excludes `jerkgramUnavailable`. The replacement validator checks account policy/version/fingerprint but deliberately permits unavailable markers, because renderers use the same validity check to suppress an indefinite loading placeholder.

The core stores a transient enhanced failure as an empty, current-version attribute with the current source fingerprint and `jerkgramUnavailable: true` (`TelegramCore/.../Translate.swift:641`). Therefore, after an offline/network/model failure, history removes the message from pending IDs and the wrapper independently skips it if called directly or as a reply dependency. The 15-second cooldown cannot restore eligibility. OFF→ON and relaunch also leave this stored version/fingerprint unchanged. No UI clearing path was found; the selection screen's Retry only requests its own text and does not replace the message attribute.

**Minimal fix:** Require `!translation.jerkgramUnavailable` at each successful-cache shortcut, retaining account-aware validity. Apply to originals, reply dependencies, regular visible messages and grouped visible messages. Keep the loading helper's validity semantics. Verify a current failed marker is eligible after the bounded retry admission, while a current successful marker suppresses a duplicate and stock untagged translations remain accepted.

### P2 — Manual translation screens outside chats lose system fallback initialization

**Owner:** `submodules/TelegramUI/Components/TextProcessingScreen/Sources/TextProcessingTranslateContentComponent.swift`, `beginTranslationIfNecessary`, enhanced request at line 279; removed initializer in `submodules/TranslateUI/Sources/Translate.swift`, former `jerkgramTranslateText` adapter.

The old selection adapter initialized `engineExperimentalInternalTranslationService` using the main window's host view before requesting local translation. The new component calls the engine directly, and the replacement adapter also delegates directly. The only remaining service installation in this source tree is `ChatControllerLoadDisplayNode.swift:701–705`, so it happens only after loading a chat controller.

Manual screens can be opened independently: profile/about uses a direct initializer (`PeerInfoScreenOpenPeerInfoContextMenu.swift:99`), gift text uses the shared factory (`GiftViewScreen.swift:956`), and story text has another direct initializer. On a fresh session before any chat is loaded, the core local fallback sees a nil service and fails immediately even on iOS 18+ with an installed supported model. A Telegram text API failure consequently loses the promised system fallback solely because of navigation history.

**Minimal fix:** Restore idempotent service installation at a shared main-actor manual translation-screen boundary with an available host view, covering both factory and direct initializers. Preserve current consent/model policy. Verify fallback initialization without first constructing a chat controller.

## Other review results and limits

- Account-aware validity arguments in the changed plain-text, poll, transcript, reply, pinned, gallery and clipboard consumers refer to available context fields. No concrete Swift type/signature error was identified by source inspection.
- The shared screen factory's old call signature forwards to the new requirement; the provided production conformer forwards locality into the screen. This preserves old callers. Compilation and the complete conformer universe are not established by this review: the sparse upstream checkout is missing some objects and attempts to read those encountered an unavailable network.
- The preference is default ON, participates in canonical account state/delta persistence and activation, and its key does not join the visual/playback invalidation sets. Policy notifications are account filtered and observers are disposed. Enhanced single-result delivery checks input, target, account, request generation and policy generation.
- OFF restores the inspected native availability decisions, native selection composition branch and `enableLocalIfPossible` interpretation; Premium cloud selections retain native routing. Existing visible scheduling/cancellation bounds remain; this is not a claim that all scheduler code is byte-identical to stock.
- Detection retains latest-32/max-16/prefix-256/max-4 and one-hour caching, per-invocation recognizers, ignored-language and hidden-banner gates. The UTF-16 mask validates ranges against the original sample and preserves offsets across overlapping masks. Ordinary banner subscription does not force prediction.
- Two unchanged rich-page readers lack the new validity call (`ChatMessageRichDataBubbleContentNode.swift:360`, `ChatInterfaceStateContextMenus.swift:1406`). Current and predecessor enhanced routes do not generate a translated `instantPage`, so these were not promoted to actionable findings for the present patch. This is a limit on the report's broad “all cached boundaries” wording.

## Executed verification

`JERKGRAM_TRANSLATION_REPAIR_SOURCE=<absolute task-a/source> python -m unittest discover -s tests -p test_jg131_translation_ui_repair.py -q` in the builder: **6 tests, OK, 1 skipped**. The five source contracts pass. The actual production Foundation mask fixture is skipped because Swift is unavailable on this Linux host. These contracts do not cover the three findings above and are supplemental source evidence only. No native compile, simulator, device, backend entitlement, quality or runtime-success claim is made.
