#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"

FORWARD = SRC / (
    "submodules/TelegramUI/Sources/"
    "ChatControllerForwardMessages.swift"
)

VOICE = SRC / (
    "submodules/TelegramUI/Sources/Chat/"
    "ChatControllerMediaRecording.swift"
)

HEADER = SRC / (
    "submodules/TelegramUI/Components/PeerInfo/"
    "PeerInfoScreen/Sources/PeerInfoHeaderNode.swift"
)

SETTINGS = SRC / (
    "submodules/SettingsUI/Sources/GhostBase/"
    "GhostBaseSettingsController.swift"
)

def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"[v1.0X] missing anchor: {label}")
    return text.replace(old, new, 1)

forward = FORWARD.read_text()
voice = VOICE.read_text()
header = HEADER.read_text()
settings = SETTINGS.read_text()

forward = once(
    forward,
    '''attributes.append(ForwardOptionsMessageAttribute(hideNames: forwardOptions?.hideNames == true, hideCaptions: forwardOptions?.hideCaptions == true))''',
    '''attributes.append(
                            ForwardOptionsMessageAttribute(
                                hideNames:
                                    forwardOptions?.hideNames == true
                                    || options?.hideNames == true
                                    || forceHideNames,
                                hideCaptions:
                                    forwardOptions?.hideCaptions == true
                                    || options?.hideCaptions == true
                            )
                        )''',
    "multiplePeersSelected forward options"
)

old_hide = (
    "hideNames: !hasNotOwnMessages "
    "|| (options?.hideNames ?? false)"
)

new_hide = (
    "hideNames: !hasNotOwnMessages "
    "|| (options?.hideNames ?? false) "
    "|| forceHideNames"
)

count = forward.count(old_hide)

if count not in (0, 2):
    raise RuntimeError(
        f"[v1.0X] unexpected single-peer hideNames count: {count}"
    )

if count == 2:
    forward = forward.replace(old_hide, new_hide)

forward = once(
    forward,
    '''return .forward(source: message.id, threadId: nil, grouping: .auto, attributes: forceHideNames ? [ForwardOptionsMessageAttribute(hideNames: true, hideCaptions: false)] : [], correlationId: correlationId)''',
    '''return .forward(
                            source: message.id,
                            threadId: nil,
                            grouping: .auto,
                            attributes: (
                                forceHideNames
                                || options?.hideNames == true
                            )
                            ? [
                                ForwardOptionsMessageAttribute(
                                    hideNames: true,
                                    hideCaptions:
                                        options?.hideCaptions == true
                                )
                            ]
                            : [],
                            correlationId: correlationId
                        )''',
    "saved messages forward attributes"
)

forward = once(
    forward,
    '''maybeChat.updateChatPresentationInterfaceState(animated: false, interactive: true, { $0.updatedInterfaceState({ $0.withUpdatedForwardMessageIds(messages.map { $0.id }).withoutSelectionState() }) })''',
    '''maybeChat.updateChatPresentationInterfaceState(
                                            animated: false,
                                            interactive: true,
                                            {
                                                $0.updatedInterfaceState {
                                                    $0.withUpdatedForwardMessageIds(
                                                        messages.map { $0.id }
                                                    )
                                                    .withUpdatedForwardOptionsState(
                                                        ChatInterfaceForwardOptionsState(
                                                            hideNames:
                                                                !hasNotOwnMessages
                                                                || (options?.hideNames ?? false)
                                                                || forceHideNames,
                                                            hideCaptions:
                                                                options?.hideCaptions
                                                                ?? false,
                                                            unhideNamesOnCaptionChange:
                                                                false
                                                        )
                                                    )
                                                    .withoutSelectionState()
                                                }
                                            }
                                        )''',
    "already-open target chat"
)

voice = once(
    voice,
    '''            // MARK: GhostBase v1.0T scheduled voice UI cleanup
            let ghostBaseRuntimeScheduledVoice = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil && !isScheduledMessages

            if !ghostBaseRuntimeScheduledVoice {''',
    '''            // MARK: GhostBase v1.0X scheduled voice UI routing
            let ghostBaseVoiceWillBeScheduled =
                scheduleTime != nil
                || (
                    (
                        UserDefaults.standard.object(
                            forKey: "GhostBase.GhostMode.ScheduledSend"
                        ) as? Bool
                    ) ?? false
                ) && !isScheduledMessages

            if !ghostBaseVoiceWillBeScheduled {''',
    "scheduled voice routing"
)

old_cleanup_marker = (
    "                if ghostBaseVoiceWasScheduled {\n"
    "                    // MARK: GhostBase v1.0W "
    "scheduled voice post-enqueue cleanup\n"
)

start = voice.find(old_cleanup_marker)

if start != -1:
    end = voice.find("\n            })", start)

    if end == -1:
        raise RuntimeError(
            "[v1.0X] old voice cleanup end missing"
        )

    voice = voice[:start] + voice[end + 1:]

voice_cleanup = '''            if ghostBaseVoiceWasScheduled {
                // MARK: GhostBase v1.0X scheduled voice immediate success cleanup
                self.recorderDataDisposable.set(nil)

                self.chatDisplayNode.collapseInput()

                self.updateChatPresentationInterfaceState(
                    animated: true,
                    interactive: false,
                    {
                        $0.updatedInterfaceState {
                            $0.withUpdatedReplyMessageSubject(nil)
                                .withUpdatedMediaDraftState(nil)
                                .withUpdatedSendMessageEffect(nil)
                                .withUpdatedPostSuggestionState(nil)
                        }.updatedInputTextPanelState { panelState in
                            panelState.withUpdatedMediaRecordingState(nil)
                        }
                    }
                )

                self.updateDownButtonVisibility()
                self.dismissAllTooltips()
            }

'''

voice_anchor = (
    "            donateSendMessageIntent("
    "account: self.context.account"
)

if "GhostBase v1.0X scheduled voice immediate success cleanup" \
        not in voice:
    if voice_anchor not in voice:
        raise RuntimeError(
            "[v1.0X] voice cleanup insertion anchor missing"
        )

    voice = voice.replace(
        voice_anchor,
        voice_cleanup + voice_anchor,
        1
    )

header = once(
    header,
    '''        if let peer = peer {
            var title: String
''',
    '''        if let peer = peer {
            // MARK: GhostBase v1.0X hide own phone in profile header
            let ghostBaseShouldHideOwnPhone =
                UserDefaults.standard.bool(
                    forKey: "GhostBase.Appearance.HideOwnPhone"
                )
                && peer.id == self.context.account.peerId

            let ghostBaseHidePhoneInHeader =
                self.hidePhoneInSettings
                || ghostBaseShouldHideOwnPhone

            var title: String
''',
    "profile header hide state"
)

header = once(
    header,
    '''if let peer = peer as? TelegramUser, let phone = peer.phone, !self.hidePhoneInSettings {''',
    '''if let peer = peer as? TelegramUser,
                   let phone = peer.phone,
                   !ghostBaseHidePhoneInHeader {''',
    "profile header title phone"
)

header = once(
    header,
    '''if !formattedPhone.isEmpty && self.hidePhoneInSettings {''',
    '''if !formattedPhone.isEmpty
                    && ghostBaseHidePhoneInHeader {''',
    "profile header subtitle phone"
)

settings = once(
    settings,
    '''        UserDefaults.standard.set(
            self.sendTextStyle,
            forKey: ghostBaseSendTextStyleKey
        )

        UserDefaults.standard.set(self.protectedEnabled,''',
    '''        UserDefaults.standard.set(
            self.sendTextStyle,
            forKey: ghostBaseSendTextStyleKey
        )
        UserDefaults.standard.set(
            self.messageSeconds,
            forKey: GhostBaseKey.messageSeconds
        )
        UserDefaults.standard.set(
            self.hideOwnPhone,
            forKey: GhostBaseKey.hideOwnPhone
        )

        UserDefaults.standard.set(self.protectedEnabled,''',
    "appearance state save"
)

FORWARD.write_text(forward)
VOICE.write_text(voice)
HEADER.write_text(header)
SETTINGS.write_text(settings)

print("[v1.0X] forwarding fixed")
print("[v1.0X] scheduled voice cleanup fixed")
print("[v1.0X] own phone header fixed")
