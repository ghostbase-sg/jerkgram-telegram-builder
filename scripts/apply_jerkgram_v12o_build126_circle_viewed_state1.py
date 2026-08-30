#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveInstantVideoNode/Sources/ChatMessageInteractiveInstantVideoNode.swift"
MARKER = "// MARK: Jerkgram v1.2O BUILD126_OUTGOING_ONETIME_VIEWED_CIRCLE1"
OLD_MARKER = "// MARK: Jerkgram v1.2M BUILD124_OUTGOING_ONETIME_VIEWED_CIRCLE1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build126 circle viewed state] " + message)


def patch_text(text: str) -> str:
    if MARKER in text:
        return text

    start = text.find(OLD_MARKER)
    require(start >= 0, "Build124 circle viewed owner missing")
    end = text.find("            var updatedPlaybackStatus: Signal<FileMediaResourceStatus, NoError>?", start)
    require(end >= 0, "circle playback-status boundary missing")

    replacement = '''            // MARK: Jerkgram v1.2O BUILD126_OUTGOING_ONETIME_VIEWED_CIRCLE1
            // `consumed` comes from Telegram's remote content-read update.
            // It must not depend on a local preservation toggle, and it must
            // not be rewritten to keep the old unread-dot layout alive.
            var notConsumed = false
            var jerkgramOutgoingOneTimeCircleViewed = false
            for attribute in item.message.attributes {
                if let attribute = attribute as? ConsumableContentMessageAttribute {
                    if !attribute.consumed {
                        notConsumed = true
                    } else if !item.message.effectivelyIncoming(item.context.account.peerId) && attribute.consumed {
                        jerkgramOutgoingOneTimeCircleViewed = true
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
    require(TARGET.is_file(), f"missing circle owner: {TARGET}")
    TARGET.write_text(patch_text(TARGET.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build126 circle viewed state] GREEN")


if __name__ == "__main__":
    main()
