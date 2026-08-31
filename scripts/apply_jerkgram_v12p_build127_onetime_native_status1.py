#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
VOICE = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift"
CIRCLE = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveInstantVideoNode/Sources/ChatMessageInteractiveInstantVideoNode.swift"
VOICE_MARKER = "// MARK: Jerkgram v1.2P BUILD127_NATIVE_ONETIME_VOICE_STATUS1"
CIRCLE_MARKER = "// MARK: Jerkgram v1.2P BUILD127_NATIVE_ONETIME_CIRCLE_STATUS1"
BUILD126_VOICE_MARKER = "// MARK: Jerkgram v1.2O BUILD126_OUTGOING_ONETIME_VIEWED_VOICE1"
BUILD126_CIRCLE_MARKER = "// MARK: Jerkgram v1.2O BUILD126_OUTGOING_ONETIME_VIEWED_CIRCLE1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build127 native one-time status] " + message)


def patch_voice_text(text: str) -> str:
    if VOICE_MARKER in text:
        return text
    start = text.find(BUILD126_VOICE_MARKER)
    require(start >= 0, "Build126 voice renderer missing")
    end = text.find("\n                        break", start)
    require(end >= 0, "Build126 voice renderer end missing")
    replacement = '''// MARK: Jerkgram v1.2P BUILD127_NATIVE_ONETIME_VOICE_STATUS1
                        // Keep Telegram's own consumable-media states. The Build126
                        // renderer drew an additional dot/check image for consumed
                        // outgoing voice messages, which conflicted with the message
                        // read receipt and was not a native one-time-media status.
                        if !attribute.consumed {
                            if arguments.incoming {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentIncomingIcon(arguments.presentationData.theme.theme)
                            } else {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentOutgoingIcon(arguments.presentationData.theme.theme)
                            }
                        }
'''
    return text[:start] + replacement + text[end:]


def patch_circle_text(text: str) -> str:
    if CIRCLE_MARKER in text:
        return text
    start = text.find(BUILD126_CIRCLE_MARKER)
    require(start >= 0, "Build126 circle renderer missing")
    end = text.find("            var updatedPlaybackStatus: Signal<FileMediaResourceStatus, NoError>?", start)
    require(end >= 0, "Build126 circle renderer end missing")
    replacement = '''            // MARK: Jerkgram v1.2P BUILD127_NATIVE_ONETIME_CIRCLE_STATUS1
            // Preserve only Telegram's native consumed/not-consumed state. There is
            // no separate outgoing viewed marker in the circle renderer.
            var notConsumed = false
            for attribute in item.message.attributes {
                if let attribute = attribute as? ConsumableContentMessageAttribute {
                    if !attribute.consumed {
                        notConsumed = true
                    }
                    break
                }
            }
            if item.message.id.namespace == Namespaces.Message.Local || item.message.id.namespace == Namespaces.Message.ScheduledLocal || item.message.id.namespace == Namespaces.Message.QuickReplyLocal {
                notConsumed = true
            }

'''
    return text[:start] + replacement + text[end:]


def main() -> None:
    require(VOICE.is_file(), f"missing voice owner: {VOICE}")
    require(CIRCLE.is_file(), f"missing circle owner: {CIRCLE}")
    VOICE.write_text(patch_voice_text(VOICE.read_text(encoding="utf-8")), encoding="utf-8")
    CIRCLE.write_text(patch_circle_text(CIRCLE.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build127 native one-time status] GREEN")


if __name__ == "__main__":
    main()
