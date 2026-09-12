#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()

CHAT_HISTORY_LIST = ROOT / "submodules/TelegramUI/Sources/ChatHistoryListNode.swift"
VIDEO_GALLERY = ROOT / "submodules/GalleryUI/Sources/Items/UniversalVideoGalleryItem.swift"

CHAT_MARKER = "// JERKGRAM_NO_ADS_V1_CHAT"
GALLERY_MARKER = "// JERKGRAM_NO_ADS_V1_GALLERY"

CHAT_OWNER = '''        let adMessagesState: Signal<AdMessagesHistoryContext.State?, NoError>
        if let adMessagesContext = adMessagesContext {
            adMessagesState = adMessagesContext.state
            |> map { state -> AdMessagesHistoryContext.State? in
                return state
            }
        } else {
            adMessagesState = .single(nil)
        }
'''

CHAT_REPLACEMENT = '''        let adMessagesState: Signal<AdMessagesHistoryContext.State?, NoError>
        // JERKGRAM_NO_ADS_V1_CHAT
        adMessagesState = .single(nil)
'''

GALLERY_START = "        let adContext = context.engine.messages.adMessages(peerId: message.id.peerId, messageId: message.id)\n"
GALLERY_END = "        }))\n"
GALLERY_REPLACEMENT = '''        // JERKGRAM_NO_ADS_V1_GALLERY
        self.adDisposable.set(nil)
        self.adContext = nil
        self.adState = nil
        self.adSchedule = []
'''


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build140 no ads] " + message)


def patch_chat_history_list(text: str) -> str:
    if CHAT_MARKER in text:
        require(text.count(CHAT_MARKER) == 1, "chat marker is ambiguous")
        require(CHAT_OWNER not in text, "stock chat ad-state owner survived beside marker")
        return text

    require(text.count(CHAT_OWNER) == 1, f"chat ad-state owner: expected 1, found {text.count(CHAT_OWNER)}")
    text = text.replace(CHAT_OWNER, CHAT_REPLACEMENT, 1)
    require(text.count(CHAT_MARKER) == 1, "chat marker count after patch")
    return text


def patch_video_gallery(text: str) -> str:
    if GALLERY_MARKER in text:
        require(text.count(GALLERY_MARKER) == 1, "gallery marker is ambiguous")
        return text

    require(text.count(GALLERY_START) == 1, f"gallery ad-context owner: expected 1, found {text.count(GALLERY_START)}")
    start = text.index(GALLERY_START)
    end = text.find(GALLERY_END, start)
    require(end >= 0, "gallery ad-state subscription end not found")
    end += len(GALLERY_END)

    owner = text[start:end]
    require("adContext.state" in owner, "gallery owner no longer subscribes to adContext.state")
    require("self.adSchedule = schedule" in owner, "gallery ad scheduling owner missing")

    text = text[:start] + GALLERY_REPLACEMENT + text[end:]
    require(text.count(GALLERY_MARKER) == 1, "gallery marker count after patch")
    require(GALLERY_START not in text, "gallery ad-context fetch survived patch")
    return text


def main() -> None:
    require(CHAT_HISTORY_LIST.is_file(), "missing ChatHistoryListNode.swift")
    require(VIDEO_GALLERY.is_file(), "missing UniversalVideoGalleryItem.swift")

    chat = patch_chat_history_list(CHAT_HISTORY_LIST.read_text(encoding="utf-8"))
    gallery = patch_video_gallery(VIDEO_GALLERY.read_text(encoding="utf-8"))

    CHAT_HISTORY_LIST.write_text(chat, encoding="utf-8")
    VIDEO_GALLERY.write_text(gallery, encoding="utf-8")

    print("[Build140 no ads] GREEN")
    print("[Build140 no ads] sponsored-message UI state disabled in chat history and video gallery; Premium state untouched")


if __name__ == "__main__":
    main()
