#!/usr/bin/env python3
from pathlib import Path
import re

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
                                    || options?.hideNames == true,
                                hideCaptions:
                                    forwardOptions?.hideCaptions == true
                                    || options?.hideCaptions == true
                            )
                        )''',
    "multiplePeersSelected forward options"
)

new_hide = (
    "hideNames: !hasNotOwnMessages "
    "|| (options?.hideNames ?? false) "
)

if forward.count(new_hide) != 2:
    old_hide_candidates = [
        (
            "hideNames: !hasNotOwnMessages "
            "|| (options?.hideNames ?? false)"
        ),
        "hideNames: !hasNotOwnMessages",
    ]

    for old_hide in old_hide_candidates:
        if forward.count(old_hide) == 2:
            forward = forward.replace(old_hide, new_hide)
            break
    else:
        raise RuntimeError(
            "[v1.0X] missing two single-peer hideNames anchors"
        )

saved_start = forward.index(
    "let mappedMessages = messages.map"
)
saved_end = forward.index(
    "let _ = (reactionItems",
    saved_start
)
saved_block = forward[saved_start:saved_end]

saved_pattern = re.compile(
    r"return \.forward\("
    r"\s*source: message\.id,"
    r"\s*threadId: nil,"
    r"\s*grouping: \.auto,"
    r"\s*attributes:.*?,"
    r"\s*correlationId: correlationId"
    r"\s*\)",
    re.S
)

saved_replacement = """return .forward(
                            source: message.id,
                            threadId: nil,
                            grouping: .auto,
                            attributes: (
                                options?.hideNames == true
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
                        )"""

saved_block, saved_count = saved_pattern.subn(
    saved_replacement,
    saved_block,
    count=1
)

if saved_count != 1:
    raise RuntimeError(
        "[v1.0X] Saved Messages forward expression not found"
    )

forward = (
    forward[:saved_start]
    + saved_block
    + forward[saved_end:]
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
                                                                || (options?.hideNames ?? false),
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

legacy_header_state = """        if let peer = peer {
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
"""

official_header_state = """        if let peer = peer {
            // MARK: GhostBase v1.0X hide own phone in profile header
            let ghostBaseHidePhoneInHeader =
                UserDefaults.standard.bool(
                    forKey: "GhostBase.Appearance.HideOwnPhone"
                )
                && peer.id == self.context.account.peerId

            var title: String
"""

if legacy_header_state in header:
    header = header.replace(
        legacy_header_state,
        official_header_state,
        1
    )
elif official_header_state not in header:
    header = once(
        header,
        """        if let peer = peer {
            var title: String
""",
        official_header_state,
        "profile header hide state"
    )

header = once(
    header,
    """if case let .user(user) = peer, let phone = user.phone {""",
    """if case let .user(user) = peer,
                   let phone = user.phone,
                   !ghostBaseHidePhoneInHeader {""",
    "profile header title phone"
)

header = once(
    header,
    """            if self.isSettings, case let .user(user) = peer {
                var subtitle = formatPhoneNumber(context: self.context, number: user.phone ?? "")
                
                if let mainUsername = user.addressName, !mainUsername.isEmpty {
                    subtitle = "\\(subtitle) • @\\(mainUsername)"
                }
""",
    """            if self.isSettings, case let .user(user) = peer {
                var subtitle = ghostBaseHidePhoneInHeader
                    ? ""
                    : formatPhoneNumber(
                        context: self.context,
                        number: user.phone ?? ""
                    )
                
                if let mainUsername = user.addressName, !mainUsername.isEmpty {
                    if subtitle.isEmpty {
                        subtitle = "@\\(mainUsername)"
                    } else {
                        subtitle = "\\(subtitle) • @\\(mainUsername)"
                    }
                }
""",
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
