from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work" / "swiftgram-src"

def fail(msg: str) -> None:
    print(f"[v0.7D] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def read(path: Path) -> str:
    if not path.exists():
        fail(f"missing file: {path}")
    return path.read_text()

def write(path: Path, text: str) -> None:
    # Keep generated Swift patches clean for git diff --check.
    text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    path.write_text(text)
    print(f"[v0.7D] patched: {path.relative_to(ROOT)}")

def _strip_trailing_ws(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines())

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        print(f"[v0.7D] already patched: {label}")
        return text

    if old in text:
        return text.replace(old, new, 1)

    text_clean = _strip_trailing_ws(text)
    old_clean = _strip_trailing_ws(old)
    new_clean = _strip_trailing_ws(new)

    if new_clean in text_clean:
        print(f"[v0.7D] already patched: {label}")
        return text_clean + "\n"

    if old_clean not in text_clean:
        fail(f"pattern not found: {label}")

    return text_clean.replace(old_clean, new_clean, 1) + "\n"

def patch_settings() -> None:
    path = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
    text = read(path)
    text = text.replace("Version: v0.7C", "Version: v0.7D")
    text = text.replace(
        "Scheduled Send is active in v0.7C.",
        "Scheduled Send is active in v0.7D Stabilizer."
    )
    write(path, text)

def patch_chat_controller_node() -> None:
    path = SRC / "submodules/TelegramUI/Sources/ChatControllerNode.swift"
    text = read(path)

    old = "            if let _ = effectivePresentationInterfaceState.slowmodeState, !isScheduledMessages && scheduleTime == nil {"
    new = """            // MARK: GhostBase v0.7D Scheduled Send Stabilizer
            let ghostBaseRuntimeScheduledSend = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil

            if let _ = effectivePresentationInterfaceState.slowmodeState, !isScheduledMessages && scheduleTime == nil && !ghostBaseRuntimeScheduledSend {"""
    text = replace_once(text, old, new, "ChatControllerNode slowmode/runtime guard")

    old = "                        if self.shouldAnimateMessageTransition, let inputPanelNode = self.inputPanelNode as? ChatTextInputPanelNode, let textInput = inputPanelNode.makeSnapshotForTransition() {"
    new = "                        if !ghostBaseRuntimeScheduledSend && self.shouldAnimateMessageTransition, let inputPanelNode = self.inputPanelNode as? ChatTextInputPanelNode, let textInput = inputPanelNode.makeSnapshotForTransition() {"
    text = replace_once(text, old, new, "ChatControllerNode text transition guard")

    write(path, text)

def patch_chat_controller() -> None:
    path = SRC / "submodules/TelegramUI/Sources/ChatController.swift"
    text = read(path)

    old = "    func sendMessages(_ messages: [EnqueueMessage], media: Bool = false, postpone: Bool = false, commit: Bool = false) {"
    new = """    // MARK: GhostBase v0.7D Scheduled Send Autoremove Guard
    private func ghostBaseScheduledSendContainsAutoremove(_ messages: [EnqueueMessage]) -> Bool {
        for message in messages {
            switch message {
            case let .message(_, attributes, _, _, _, _, _, _, _, _):
                if attributes.contains(where: { $0 is AutoremoveTimeoutMessageAttribute }) {
                    return true
                }
            default:
                break
            }
        }
        return false
    }

    func sendMessages(_ messages: [EnqueueMessage], media: Bool = false, postpone: Bool = false, commit: Bool = false) {"""
    text = replace_once(text, old, new, "ChatController autoremove helper")

    old = """        guard let peerId = self.chatLocation.peerId else {
            return
        }

        let _ = (self.shouldDivertMessagesToScheduled(messages: messages)"""
    new = """        guard let peerId = self.chatLocation.peerId else {
            return
        }

        let ghostBaseScheduledSendEnabled = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false
        var ghostBaseIsScheduledMessages = false
        if case .scheduledMessages = self.presentationInterfaceState.subject {
            ghostBaseIsScheduledMessages = true
        }
        if ghostBaseScheduledSendEnabled && !ghostBaseIsScheduledMessages && self.ghostBaseScheduledSendContainsAutoremove(messages) {
            return
        }

        let _ = (self.shouldDivertMessagesToScheduled(messages: messages)"""
    text = replace_once(text, old, new, "ChatController central autoremove block")

    old = """                var skipAddingTransitions = false

                if shouldDivert {
                    skipAddingTransitions = true
                }"""
    new = """                var skipAddingTransitions = false

                // MARK: GhostBase v0.7D Scheduled Send Media Transition Stabilizer
                let ghostBaseRuntimeScheduledSend = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil

                if shouldDivert || ghostBaseRuntimeScheduledSend {
                    skipAddingTransitions = true
                }"""
    text = replace_once(text, old, new, "ChatController media transition skip")

    old = "                        var addTransition = scheduleTime == nil"
    new = "                        var addTransition = scheduleTime == nil && !ghostBaseRuntimeScheduledSend"
    text = replace_once(text, old, new, "ChatController media addTransition guard")

    write(path, text)

def patch_media_recording() -> None:
    path = SRC / "submodules/TelegramUI/Sources/Chat/ChatControllerMediaRecording.swift"
    text = read(path)

    old = "                        if scheduleTime == nil, shouldAnimateMessageTransition, let extractedView = videoController.extractVideoSnapshot() {"
    new = """                        // MARK: GhostBase v0.7D Scheduled Send Recording Transition Stabilizer
                        let ghostBaseRuntimeScheduledSend = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil

                        if !ghostBaseRuntimeScheduledSend, scheduleTime == nil, shouldAnimateMessageTransition, let extractedView = videoController.extractVideoSnapshot() {"""
    text = replace_once(text, old, new, "MediaRecording video transition guard")

    old = """            let transformedMessages: [EnqueueMessage]
            if let silentPosting = silentPosting {"""
    new = """            // MARK: GhostBase v0.7D Scheduled Send One-Time Voice Guard
            let ghostBaseRuntimeScheduledSendForVoice = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil
            if ghostBaseRuntimeScheduledSendForVoice && messages.contains(where: { message in
                if case let .message(_, attributes, _, _, _, _, _, _, _, _) = message {
                    return attributes.contains(where: { $0 is AutoremoveTimeoutMessageAttribute })
                }
                return false
            }) {
                return
            }

            let transformedMessages: [EnqueueMessage]
            if let silentPosting = silentPosting {"""
    text = replace_once(text, old, new, "MediaRecording one-time voice block")

    write(path, text)

def patch_video_message_camera() -> None:
    path = SRC / "submodules/TelegramUI/Components/VideoMessageCameraScreen/Sources/VideoMessageCameraScreen.swift"
    text = read(path)

    old = """        guard !self.didSend else {
            return
        }

        var skipAction = false"""
    new = """        guard !self.didSend else {
            return
        }

        // MARK: GhostBase v0.7D Scheduled Send Immediate-Mode Stabilizer
        let ghostBaseRuntimeScheduledSend = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil

        var skipAction = false"""
    text = replace_once(text, old, new, "VideoMessageCamera runtime flag")

    old = "                self.isSendingImmediately = true"
    new = "                self.isSendingImmediately = !ghostBaseRuntimeScheduledSend"
    text = replace_once(text, old, new, "VideoMessageCamera immediate guard")

    old = """                if let messageEffect {
                    attributes.append(EffectMessageAttribute(id: messageEffect.id))
                }

                self.completion(.message("""
    new = """                if let messageEffect {
                    attributes.append(EffectMessageAttribute(id: messageEffect.id))
                }

                // MARK: GhostBase v0.7D Scheduled Send One-Time Circle Guard
                if ghostBaseRuntimeScheduledSend && attributes.contains(where: { $0 is AutoremoveTimeoutMessageAttribute }) {
                    self.completion(nil, nil, nil)
                    return
                }

                self.completion(.message("""
    text = replace_once(text, old, new, "VideoMessageCamera one-time circle block")

    write(path, text)

def patch_story_core() -> None:
    path = SRC / "submodules/TelegramUI/Components/Stories/StoryContainerScreen/Sources/StoryItemSetContainerViewSendMessage.swift"
    text = read(path)

    old = "    private func transformEnqueueMessages(view: StoryItemSetContainerComponent.View, messages: [EnqueueMessage], silentPosting: Bool, scheduleTime: Int32? = nil) -> [EnqueueMessage] {"
    new = """    // MARK: GhostBase v0.7D Scheduled Send Story Helpers
    private func ghostBaseStoryEffectiveScheduleTime(_ scheduleTime: Int32?) -> Int32? {
        return (((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil) ? Int32(Date().timeIntervalSince1970) + 12 : scheduleTime
    }

    private func ghostBaseStoryContainsAutoremove(_ messages: [EnqueueMessage]) -> Bool {
        for message in messages {
            switch message {
            case let .message(_, attributes, _, _, _, _, _, _, _, _):
                if attributes.contains(where: { $0 is AutoremoveTimeoutMessageAttribute }) {
                    return true
                }
            default:
                break
            }
        }
        return false
    }

    private func transformEnqueueMessages(view: StoryItemSetContainerComponent.View, messages: [EnqueueMessage], silentPosting: Bool, scheduleTime: Int32? = nil) -> [EnqueueMessage] {"""
    text = replace_once(text, old, new, "Story helpers")

    old = "        return messages.map { message in"
    new = """        let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(scheduleTime)

        return messages.map { message in"""
    text = replace_once(text, old, new, "Story transform effective time")

    text = replace_once(text, "                if silentPosting || scheduleTime != nil {", "                if silentPosting || ghostBaseEffectiveScheduleTime != nil {", "Story transform condition")
    text = replace_once(text, "                        } else if let _ = scheduleTime, attributes[i] is OutgoingScheduleInfoMessageAttribute {", "                        } else if let _ = ghostBaseEffectiveScheduleTime, attributes[i] is OutgoingScheduleInfoMessageAttribute {", "Story transform remove old schedule")

    old = """                    if let scheduleTime = scheduleTime {
                         attributes.append(OutgoingScheduleInfoMessageAttribute(scheduleTime: scheduleTime, repeatPeriod: nil))
                    }"""
    new = """                    if let ghostBaseEffectiveScheduleTime {
                         attributes.append(OutgoingScheduleInfoMessageAttribute(scheduleTime: ghostBaseEffectiveScheduleTime, repeatPeriod: nil))
                    }"""
    text = replace_once(text, old, new, "Story transform append effective schedule")

    old = """        guard let component = view.component else {
            return
        }
        let _ = (enqueueMessages(account: component.context.account, peerId: peer.id, messages: self.transformEnqueueMessages(view: view, messages: messages, silentPosting: silentPosting, scheduleTime: scheduleTime))"""
    new = """        guard let component = view.component else {
            return
        }

        // MARK: GhostBase v0.7D Scheduled Send Story sendMessages Stabilizer
        let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(scheduleTime)
        if ghostBaseEffectiveScheduleTime != nil && self.ghostBaseStoryContainsAutoremove(messages) {
            return
        }

        let _ = (enqueueMessages(account: component.context.account, peerId: peer.id, messages: self.transformEnqueueMessages(view: view, messages: messages, silentPosting: silentPosting, scheduleTime: ghostBaseEffectiveScheduleTime))"""
    text = replace_once(text, old, new, "Story sendMessages wrapper")

    text = replace_once(text, "                    self?.presentMessageSentTooltip(view: view, peer: peer, messageId: messageIds.first.flatMap { $0 }, isScheduled: scheduleTime != nil)", "                    self?.presentMessageSentTooltip(view: view, peer: peer, messageId: messageIds.first.flatMap { $0 }, isScheduled: ghostBaseEffectiveScheduleTime != nil)", "Story sendMessages tooltip")

    old = """                var skipAddingTransitions = false

                for item in items {"""
    new = """                var skipAddingTransitions = false

                // MARK: GhostBase v0.7D Scheduled Send Story Media Transition Stabilizer
                let ghostBaseRuntimeScheduledSend = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil
                if ghostBaseRuntimeScheduledSend {
                    skipAddingTransitions = true
                }

                for item in items {"""
    text = replace_once(text, old, new, "Story media transition skip")

    text = replace_once(text, "                        var addTransition = scheduleTime == nil", "                        var addTransition = scheduleTime == nil && !ghostBaseRuntimeScheduledSend", "Story media addTransition guard")

    write(path, text)

def patch_story_direct_sends() -> None:
    path = SRC / "submodules/TelegramUI/Components/Stories/StoryContainerScreen/Sources/StoryItemSetContainerViewSendMessage.swift"
    text = read(path)

    old = """            let focusedStoryId = StoryId(peerId: peerId, id: focusedItem.storyItem.id)
            guard let inputPanelView = view.inputPanel.view as? MessageInputPanelComponent.View else {"""
    new = """            let focusedStoryId = StoryId(peerId: peerId, id: focusedItem.storyItem.id)
            // MARK: GhostBase v0.7D Scheduled Send Story Reply Stabilizer
            let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(scheduleTime)

            guard let inputPanelView = view.inputPanel.view as? MessageInputPanelComponent.View else {"""
    text = replace_once(text, old, new, "Story reply effective schedule")

    text = replace_once(text, "                    let _ = enqueueMessages(account: component.context.account, peerId: peerId, messages: messages).start()", "                    self.sendMessages(view: view, peer: peer, messages: messages, silentPosting: silentPosting, scheduleTime: ghostBaseEffectiveScheduleTime)", "Story voice direct redirect")

    text = replace_once(text, "                                scheduleTime: scheduleTime,\n                                sendPaidMessageStars: component.slice.additionalPeerData.sendPaidMessageStars", "                                scheduleTime: ghostBaseEffectiveScheduleTime,\n                                sendPaidMessageStars: component.slice.additionalPeerData.sendPaidMessageStars", "Story text effective schedule arg")

    text = replace_once(text, "                                        self.presentMessageSentTooltip(view: view, peer: peer, messageId: messageIds.first.flatMap { $0 }, isScheduled: scheduleTime != nil)", "                                        self.presentMessageSentTooltip(view: view, peer: peer, messageId: messageIds.first.flatMap { $0 }, isScheduled: ghostBaseEffectiveScheduleTime != nil)", "Story text tooltip effective schedule")

    old = """                let _ = (component.context.engine.messages.enqueueOutgoingMessage(
                    to: peerId,
                    replyTo: nil,
                    storyId: focusedStoryId,
                    content: .file(fileReference),
                    sendPaidMessageStars: component.slice.additionalPeerData.sendPaidMessageStars
                ) |> deliverOnMainQueue).start(next: { [weak self, weak view] messageIds in"""
    new = """                let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(nil)
                let _ = (component.context.engine.messages.enqueueOutgoingMessage(
                    to: peerId,
                    replyTo: nil,
                    storyId: focusedStoryId,
                    content: .file(fileReference),
                    silentPosting: false,
                    scheduleTime: ghostBaseEffectiveScheduleTime,
                    sendPaidMessageStars: component.slice.additionalPeerData.sendPaidMessageStars
                ) |> deliverOnMainQueue).start(next: { [weak self, weak view] messageIds in"""
    text = replace_once(text, old, new, "Story sticker/file effective schedule")

    old = """            let _ = (component.context.engine.messages.enqueueOutgoingMessage(
                to: peerId,
                replyTo: nil,
                storyId: focusedStoryId,
                content: .contextResult(results, result),
                sendPaidMessageStars: component.slice.additionalPeerData.sendPaidMessageStars
            ) |> deliverOnMainQueue).start(next: { [weak self, weak view] messageIds in"""
    new = """            let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(nil)
            let _ = (component.context.engine.messages.enqueueOutgoingMessage(
                to: peerId,
                replyTo: nil,
                storyId: focusedStoryId,
                content: .contextResult(results, result),
                silentPosting: false,
                scheduleTime: ghostBaseEffectiveScheduleTime,
                sendPaidMessageStars: component.slice.additionalPeerData.sendPaidMessageStars
            ) |> deliverOnMainQueue).start(next: { [weak self, weak view] messageIds in"""
    text = replace_once(text, old, new, "Story context result effective schedule")

    write(path, text)

def self_check() -> None:
    settings = read(SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
    node = read(SRC / "submodules/TelegramUI/Sources/ChatControllerNode.swift")
    chat = read(SRC / "submodules/TelegramUI/Sources/ChatController.swift")
    media = read(SRC / "submodules/TelegramUI/Sources/Chat/ChatControllerMediaRecording.swift")
    video = read(SRC / "submodules/TelegramUI/Components/VideoMessageCameraScreen/Sources/VideoMessageCameraScreen.swift")
    story = read(SRC / "submodules/TelegramUI/Components/Stories/StoryContainerScreen/Sources/StoryItemSetContainerViewSendMessage.swift")

    checks = [
        ("settings version", "Version: v0.7D" in settings),
        ("settings note", "Scheduled Send is active in v0.7D Stabilizer." in settings),
        ("node stabilizer", "GhostBase v0.7D Scheduled Send Stabilizer" in node),
        ("node transition guard", "if !ghostBaseRuntimeScheduledSend && self.shouldAnimateMessageTransition" in node),
        ("chat autoremove helper", "ghostBaseScheduledSendContainsAutoremove" in chat),
        ("chat autoremove block", "self.ghostBaseScheduledSendContainsAutoremove(messages)" in chat),
        ("chat media transition", "var addTransition = scheduleTime == nil && !ghostBaseRuntimeScheduledSend" in chat),
        ("media recording transition", "GhostBase v0.7D Scheduled Send Recording Transition Stabilizer" in media),
        ("media one-time guard", "GhostBase v0.7D Scheduled Send One-Time Voice Guard" in media),
        ("video immediate guard", "isSendingImmediately = !ghostBaseRuntimeScheduledSend" in video),
        ("video one-time guard", "GhostBase v0.7D Scheduled Send One-Time Circle Guard" in video),
        ("story helpers", "GhostBase v0.7D Scheduled Send Story Helpers" in story),
        ("story autoremove helper", "ghostBaseStoryContainsAutoremove" in story),
        ("story send wrapper", "GhostBase v0.7D Scheduled Send Story sendMessages Stabilizer" in story),
        ("story direct reply", "GhostBase v0.7D Scheduled Send Story Reply Stabilizer" in story),
        ("story media transition", "var addTransition = scheduleTime == nil && !ghostBaseRuntimeScheduledSend" in story),
        ("story file schedule", "content: .file(fileReference),\n                    silentPosting: false,\n                    scheduleTime: ghostBaseEffectiveScheduleTime" in story),
        ("story context schedule", "content: .contextResult(results, result),\n                silentPosting: false,\n                scheduleTime: ghostBaseEffectiveScheduleTime" in story),
    ]

    bad = [name for name, ok in checks if not ok]
    if bad:
        print("[v0.7D] FAILED:")
        for item in bad:
            print("-", item)
        raise SystemExit(1)

def main() -> None:
    print("[v0.7D] applying v0.7C chain first")
    runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_scheduled_send_fix_v07c.py")))
    patch_settings()
    patch_chat_controller_node()
    patch_chat_controller()
    patch_media_recording()
    patch_video_message_camera()
    patch_story_core()
    patch_story_direct_sends()
    self_check()
    print("[v0.7D] Scheduled Send Stabilizer patch OK")

if __name__ == "__main__":
    main()
