from pathlib import Path
import runpy

VERSION = "v0.7D"

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_scheduled_send_fix_v07c.py")))

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramUI/Sources/ChatController.swift").exists():
            return c
    raise SystemExit(f"[{VERSION}] ERROR: cannot find source base from cwd={cwd}")

def clean(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"

def fail(label: str) -> None:
    raise SystemExit(f"[{VERSION}] ERROR: required anchor not found: {label}")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    if old not in text:
        fail(label)
    return text.replace(old, new, 1)

def replace_after(text: str, marker: str, old: str, new: str, label: str) -> str:
    if new in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    start = text.find(marker)
    if start < 0:
        fail(label + " marker")
    pos = text.find(old, start)
    if pos < 0:
        fail(label)
    return text[:pos] + new + text[pos + len(old):]

BASE = find_base()

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
node_p = BASE / "submodules/TelegramUI/Sources/ChatControllerNode.swift"
chat_p = BASE / "submodules/TelegramUI/Sources/ChatController.swift"
media_p = BASE / "submodules/TelegramUI/Sources/Chat/ChatControllerMediaRecording.swift"
video_p = BASE / "submodules/TelegramUI/Components/VideoMessageCameraScreen/Sources/VideoMessageCameraScreen.swift"
story_p = BASE / "submodules/TelegramUI/Components/Stories/StoryContainerScreen/Sources/StoryItemSetContainerViewSendMessage.swift"

settings = settings_p.read_text()
node = node_p.read_text()
chat = chat_p.read_text()
media = media_p.read_text()
video = video_p.read_text()
story = story_p.read_text()

settings = settings.replace("Version: v0.7C", "Version: v0.7D")
settings = settings.replace("Scheduled Send is active in v0.7C.", "Scheduled Send is active in v0.7D.")

for marker, label, text in [
    ("GhostBase v0.7A Scheduled Send runtime", "v0.7A runtime", chat),
    ("GhostBase v0.7B Scheduled Send input clear fix", "v0.7B cleanup", node),
    ("GhostBase v0.7C Scheduled Send stronger compose clear", "v0.7C cleanup", node),
]:
    if marker not in text:
        raise SystemExit(f"[{VERSION}] ERROR: {label} marker missing")

node = replace_once(
    node,
    "            if let _ = effectivePresentationInterfaceState.slowmodeState, !isScheduledMessages && scheduleTime == nil {\n",
    '''            // MARK: GhostBase v0.7D Scheduled Send text transition stabilizer
            let ghostBaseRuntimeScheduledSend = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil && !isScheduledMessages

            if let _ = effectivePresentationInterfaceState.slowmodeState, !isScheduledMessages && scheduleTime == nil && !ghostBaseRuntimeScheduledSend {
''',
    "ChatControllerNode runtime scheduled flag"
)

node = replace_once(
    node,
    "                        if self.shouldAnimateMessageTransition, let inputPanelNode = self.inputPanelNode as? ChatTextInputPanelNode, let textInput = inputPanelNode.makeSnapshotForTransition() {\n",
    "                        if !ghostBaseRuntimeScheduledSend && self.shouldAnimateMessageTransition, let inputPanelNode = self.inputPanelNode as? ChatTextInputPanelNode, let textInput = inputPanelNode.makeSnapshotForTransition() {\n",
    "ChatControllerNode skip text transition"
)

node = replace_after(
    node,
    "GhostBase v0.7C Scheduled Send stronger compose clear",
    '                            state = state.withUpdatedComposeInputState(ChatTextInputState(inputText: NSAttributedString(string: "")))\n',
    '''                            state = state.withUpdatedComposeInputState(ChatTextInputState(inputText: NSAttributedString(string: "")))

                            // MARK: GhostBase v0.7D Scheduled Send input state stabilizer
                            state = state.withUpdatedEffectiveInputState(ChatTextInputState(inputText: NSAttributedString(string: "")))
''',
    "ChatControllerNode effective input clear"
)

chat = replace_once(
    chat,
    "                let ghostBaseHasExistingSchedule = attributes.contains(where: { $0 is OutgoingScheduleInfoMessageAttribute })\n",
    '''                let ghostBaseHasExistingSchedule = attributes.contains(where: { $0 is OutgoingScheduleInfoMessageAttribute })
                // MARK: GhostBase v0.7D Scheduled Send one-time exclusion
                let ghostBaseHasAutoremove = attributes.contains(where: { $0 is AutoremoveTimeoutMessageAttribute })
''',
    "ChatController one-time exclusion flag"
)

chat = replace_once(
    chat,
    "let ghostBaseEffectiveScheduleTime: Int32? = (ghostBaseScheduledSendEnabled && scheduleTime == nil && !ghostBaseHasExistingSchedule && !ghostBaseIsScheduledMessages) ? ghostBaseScheduleBaseTime : scheduleTime",
    "let ghostBaseEffectiveScheduleTime: Int32? = (ghostBaseScheduledSendEnabled && scheduleTime == nil && !ghostBaseHasExistingSchedule && !ghostBaseHasAutoremove && !ghostBaseIsScheduledMessages) ? ghostBaseScheduleBaseTime : scheduleTime",
    "ChatController one-time exclusion condition"
)

chat_marker = "private func commitEnqueueMediaMessages("

chat = replace_after(
    chat,
    chat_marker,
    "                var skipAddingTransitions = false\n",
    '''                var skipAddingTransitions = false

                // MARK: GhostBase v0.7D Scheduled Send media transition stabilizer
                let ghostBaseRuntimeScheduledSend = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil
''',
    "ChatController media runtime scheduled flag"
)

chat = replace_after(
    chat,
    chat_marker,
    "                if shouldDivert {\n",
    "                if shouldDivert || ghostBaseRuntimeScheduledSend {\n",
    "ChatController media shouldDivert guard"
)

chat = replace_after(
    chat,
    chat_marker,
    "                        var addTransition = scheduleTime == nil\n",
    "                        var addTransition = scheduleTime == nil && !ghostBaseRuntimeScheduledSend\n",
    "ChatController media addTransition guard"
)

media = replace_once(
    media,
    "                        if scheduleTime == nil, shouldAnimateMessageTransition, let extractedView = videoController.extractVideoSnapshot() {\n",
    '''                        // MARK: GhostBase v0.7D Scheduled Send circle transition stabilizer
                        let ghostBaseRuntimeScheduledSend = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil

                        if !ghostBaseRuntimeScheduledSend, scheduleTime == nil, shouldAnimateMessageTransition, let extractedView = videoController.extractVideoSnapshot() {
''',
    "MediaRecording circle transition guard"
)

video = replace_once(
    video,
    "                self.isSendingImmediately = true\n",
    '''                // MARK: GhostBase v0.7D Scheduled Send circle immediate-state stabilizer
                let ghostBaseRuntimeScheduledSend = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil
                self.isSendingImmediately = !ghostBaseRuntimeScheduledSend
''',
    "VideoMessageCamera immediate state guard"
)

story = replace_once(
    story,
    "    private func transformEnqueueMessages(view: StoryItemSetContainerComponent.View, messages: [EnqueueMessage], silentPosting: Bool, scheduleTime: Int32? = nil) -> [EnqueueMessage] {\n",
    """    // MARK: GhostBase v0.7D Scheduled Send story helpers
    private func ghostBaseStoryEffectiveScheduleTime(_ scheduleTime: Int32?) -> Int32? {
        return (((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil) ? Int32(Date().timeIntervalSince1970) + 12 : scheduleTime
    }

    private func transformEnqueueMessages(view: StoryItemSetContainerComponent.View, messages: [EnqueueMessage], silentPosting: Bool, scheduleTime: Int32? = nil) -> [EnqueueMessage] {
""",
    "Story helper insertion"
)

story = replace_after(
    story,
    "private func sendMessages",
    """        guard let component = view.component else {
            return
        }
""",
    """        guard let component = view.component else {
            return
        }

        // MARK: GhostBase v0.7D Scheduled Send story sendMessages stabilizer
        let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(scheduleTime)
""",
    "Story sendMessages effective schedule"
)

story = replace_after(
    story,
    "private func sendMessages",
    "messages: self.transformEnqueueMessages(view: view, messages: messages, silentPosting: silentPosting, scheduleTime: scheduleTime))",
    "messages: self.transformEnqueueMessages(view: view, messages: messages, silentPosting: silentPosting, scheduleTime: ghostBaseEffectiveScheduleTime))",
    "Story sendMessages transform schedule"
)

story = replace_after(
    story,
    "private func sendMessages",
    "isScheduled: scheduleTime != nil",
    "isScheduled: ghostBaseEffectiveScheduleTime != nil",
    "Story sendMessages tooltip schedule"
)

story = replace_after(
    story,
    "case let .text(text):",
    "                            let _ = (component.context.engine.messages.enqueueOutgoingMessage(\n",
    '''                            let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(scheduleTime)
                            let _ = (component.context.engine.messages.enqueueOutgoingMessage(
''',
    "Story direct text effective schedule"
)

story = replace_after(
    story,
    "case let .text(text):",
    "                                scheduleTime: scheduleTime,\n",
    "                                scheduleTime: ghostBaseEffectiveScheduleTime,\n",
    "Story direct text schedule arg"
)

story = replace_after(
    story,
    "case let .text(text):",
    "isScheduled: scheduleTime != nil",
    "isScheduled: ghostBaseEffectiveScheduleTime != nil",
    "Story direct text tooltip"
)

story = replace_after(
    story,
    "func performSendStickerAction",
    "                let _ = (component.context.engine.messages.enqueueOutgoingMessage(\n",
    '''                let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(nil)
                let _ = (component.context.engine.messages.enqueueOutgoingMessage(
''',
    "Story sticker effective schedule"
)

story = replace_after(
    story,
    "func performSendStickerAction",
    "                    content: .file(fileReference),\n                    sendPaidMessageStars:",
    "                    content: .file(fileReference),\n                    silentPosting: false,\n                    scheduleTime: ghostBaseEffectiveScheduleTime,\n                    sendPaidMessageStars:",
    "Story sticker schedule args"
)

story = replace_after(
    story,
    "func performSendContextResultAction",
    "            let _ = (component.context.engine.messages.enqueueOutgoingMessage(\n",
    '''            let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(nil)
            let _ = (component.context.engine.messages.enqueueOutgoingMessage(
''',
    "Story context direct effective schedule"
)

# Story direct context result scheduled send.
# Use the real context-result API, not enqueueOutgoingMessage(content: .contextResult),
# because clean Swift rejects added schedule args on that direct wrapper.
context_marker = "func performSendContextResultAction"
context_start = story.find(context_marker)
if context_start < 0:
    fail("Story context direct function marker")

context_end = story.find("    func ", context_start + len(context_marker))
if context_end < 0:
    context_end = story.find("    private func ", context_start + len(context_marker))
if context_end < 0:
    context_end = len(story)

context_section = story[context_start:context_end]

if "GhostBase v0.7D Scheduled Send story context direct stabilizer" not in context_section:
    old_start = "            let _ = (component.context.engine.messages.enqueueOutgoingMessage(\n"
    old_end = "            self.currentInputMode = .text"

    call_start = story.find(old_start, context_start, context_end)
    if call_start < 0:
        fail("Story context direct old call start")

    call_end = story.find(old_end, call_start, context_end)
    if call_end < 0:
        fail("Story context direct old call end")

    new_call = """            // MARK: GhostBase v0.7D Scheduled Send story context direct stabilizer
            let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(nil)
            if component.context.engine.messages.enqueueOutgoingMessageWithChatContextResult(
                to: peerId,
                threadId: nil,
                botId: results.botId,
                result: result,
                replyToMessageId: nil,
                replyToStoryId: focusedStoryId,
                hideVia: true,
                silentPosting: false,
                scheduleTime: ghostBaseEffectiveScheduleTime,
                sendPaidMessageStars: component.slice.additionalPeerData.sendPaidMessageStars,
                postpone: false
            ) {
                Queue.mainQueue().after(0.3) {
                    self.presentMessageSentTooltip(view: view, peer: peer, messageId: nil, isScheduled: ghostBaseEffectiveScheduleTime != nil)
                }
            }

"""

    story = story[:call_start] + new_call + story[call_end:]

story = replace_after(
    story,
    "private func enqueueChatContextResult",
    "            if component.context.engine.messages.enqueueOutgoingMessageWithChatContextResult(\n",
    '''            let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(scheduleTime)
            if component.context.engine.messages.enqueueOutgoingMessageWithChatContextResult(
''',
    "Story inline effective schedule"
)

story = replace_after(
    story,
    "private func enqueueChatContextResult",
    "                scheduleTime: scheduleTime,\n",
    "                scheduleTime: ghostBaseEffectiveScheduleTime,\n",
    "Story inline schedule arg"
)

story = replace_after(
    story,
    "private func enqueueMediaMessages",
    "                var skipAddingTransitions = false\n",
    '''                var skipAddingTransitions = false

                // MARK: GhostBase v0.7D Scheduled Send story media transition stabilizer
                let ghostBaseRuntimeScheduledSend = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil
                if ghostBaseRuntimeScheduledSend {
                    skipAddingTransitions = true
                }
''',
    "Story media transition skip"
)

story = replace_after(
    story,
    "private func enqueueMediaMessages",
    "                        var addTransition = scheduleTime == nil\n",
    "                        var addTransition = scheduleTime == nil && !ghostBaseRuntimeScheduledSend\n",
    "Story media addTransition guard"
)

# Final narrow correction: direct story text tooltip must follow GhostBase effective schedule time.
story = story.replace(
    "self.presentMessageSentTooltip(view: view, peer: peer, messageId: messageIds.first.flatMap { $0 }, isScheduled: scheduleTime != nil)",
    "self.presentMessageSentTooltip(view: view, peer: peer, messageId: messageIds.first.flatMap { $0 }, isScheduled: ghostBaseEffectiveScheduleTime != nil)",
    1
)

# MARK: GhostBase v0.7D Swift compile guard
# Prevent already-seen StoryContainerScreen Swift failures.

dup_direct = """            let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(nil)
            // MARK: GhostBase v0.7D Scheduled Send story context direct stabilizer
            let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(nil)
"""
fixed_direct = """            // MARK: GhostBase v0.7D Scheduled Send story context direct stabilizer
            let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(nil)
"""
story = story.replace(dup_direct, fixed_direct)

inline_marker = "private func enqueueChatContextResult"
inline_start = story.find(inline_marker)
if inline_start < 0:
    fail("Story inline compile guard marker")

inline_end = story.find("    private func ", inline_start + len(inline_marker))
if inline_end < 0:
    inline_end = len(story)

inline_section = story[inline_start:inline_end]
if "let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(scheduleTime)" in inline_section:
    if "scheduleTime: ghostBaseEffectiveScheduleTime," not in inline_section:
        old_arg = "                scheduleTime: scheduleTime,\n"
        new_arg = "                scheduleTime: ghostBaseEffectiveScheduleTime,\n"
        arg_pos = story.find(old_arg, inline_start, inline_end)
        if arg_pos < 0:
            fail("Story inline scheduleTime compile guard")
        story = story[:arg_pos] + new_arg + story[arg_pos + len(old_arg):]

settings_p.write_text(clean(settings))
node_p.write_text(clean(node))
chat_p.write_text(clean(chat))
media_p.write_text(clean(media))
video_p.write_text(clean(video))
story_p.write_text(clean(story))

settings = settings_p.read_text()
node = node_p.read_text()
chat = chat_p.read_text()
media = media_p.read_text()
video = video_p.read_text()
story = story_p.read_text()

checks = [
    ("settings v07d", "Version: v0.7D" in settings),
    ("node text stabilizer", "GhostBase v0.7D Scheduled Send text transition stabilizer" in node),
    ("node input stabilizer", "GhostBase v0.7D Scheduled Send input state stabilizer" in node),
    ("chat one-time exclusion", "GhostBase v0.7D Scheduled Send one-time exclusion" in chat),
    ("chat media stabilizer", "GhostBase v0.7D Scheduled Send media transition stabilizer" in chat),
    ("media circle stabilizer", "GhostBase v0.7D Scheduled Send circle transition stabilizer" in media),
    ("video immediate stabilizer", "GhostBase v0.7D Scheduled Send circle immediate-state stabilizer" in video),
    ("story helpers", "GhostBase v0.7D Scheduled Send story helpers" in story),
    ("story sendMessages", "GhostBase v0.7D Scheduled Send story sendMessages stabilizer" in story),
    ("story media transition", "GhostBase v0.7D Scheduled Send story media transition stabilizer" in story),
    ("story schedule arg", "scheduleTime: ghostBaseEffectiveScheduleTime" in story),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print(f"[{VERSION}] FAILED:")
    for name in bad:
        print("-", name)
    raise SystemExit(1)

# MARK: GhostBase v0.7D final strict Story check
context_marker = "func performSendContextResultAction"
context_start = story.find(context_marker)
context_end = story.find("    func ", context_start + len(context_marker))
if context_end < 0:
    context_end = story.find("    private func ", context_start + len(context_marker))
if context_end < 0:
    context_end = len(story)

context_section = story[context_start:context_end]

if context_section.count("let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(nil)") > 1:
    bad.append("story direct duplicate ghostBaseEffectiveScheduleTime")

inline_marker = "private func enqueueChatContextResult"
inline_start = story.find(inline_marker)
inline_end = story.find("    private func ", inline_start + len(inline_marker))
if inline_end < 0:
    inline_end = len(story)

inline_section = story[inline_start:inline_end]

if "let ghostBaseEffectiveScheduleTime = self.ghostBaseStoryEffectiveScheduleTime(scheduleTime)" in inline_section:
    if "scheduleTime: ghostBaseEffectiveScheduleTime," not in inline_section:
        bad.append("story inline effective schedule variable unused")

if bad:
    print(f"[{VERSION}] FAILED:")
    for name in bad:
        print("-", name)
    raise SystemExit(1)

print("GhostBase Scheduled Send v0.7D FINAL patch OK")
