#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Sources/ChatControllerForwardMessages.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_PROTECTED_FORWARD_LOCAL_COPY1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 protected forward verify] " + message)


def main() -> None:
    require(TARGET.is_file(), f"target missing: {TARGET}")
    text = TARGET.read_text(encoding="utf-8")

    require(text.count(MARKER) == 1, "Build124 protected-forward owner missing or duplicated")
    require("import Postbox" in text, "Postbox import required for MediaResourceData")

    # Protected media must stop carrying the original protected cloud resource.
    require("LocalFileReferenceMediaResource" in text, "fresh local file resource missing")
    require("Namespaces.Media.LocalFile" in text, "fresh local file media id missing")
    require("Namespaces.Media.LocalImage" in text, "fresh local image media id missing")
    require("context.engine.resources.fetch" in text, "source-media fetch owner missing")
    require("waitUntilFetchStatus: true" in text, "full resource wait missing")
    require(
        "let mediaReference = message.media.first.map { AnyMediaReference.standalone(media: $0) }" not in text,
        "Build123 original-cloud standalone shortcut is still active",
    )

    # Sent-as-channel attribution must follow Telegram's author semantics.
    require(
        "message.forwardInfo?.author ?? message.effectiveAuthor" in text,
        "forward/channel author resolution is not Telegram-compatible",
    )
    require(
        "message.peers[message.id.peerId].map(EnginePeer.init)" not in text,
        "chat peer is still incorrectly used as forward author",
    )
    require('type: .TextUrl(url: "https://t.me/\\(username)")' in text, "public-channel attribution link missing")
    require("if !hideAuthor, let author =" in text, "hide-author contract missing")

    # Do not enqueue until the local file/photo is actually available.
    require("var jerkgramPortableMessagesSignal: Signal<[EnqueueMessage], NoError>?" in text, "async portable signal missing")
    require("combineLatest(messages.map" in text, "multi-message local-copy join missing")
    require("context: strongSelf.context" in text, "AccountContext not passed to local-copy owner")
    require("let commitResolved: ([EnqueueMessage]) -> Void" in text, "resolved commit owner missing")
    require("if let jerkgramPortableMessagesSignal" in text, "portable signal is never resolved")
    require("|> deliverOnMainQueue" in text, "resolved portable messages are not returned to main queue")
    require(text.index("var jerkgramPortableMessagesSignal") < text.index("let commitResolved"), "portable signal declared after commit owner")

    # Ordinary forwarding remains native and secret-chat portable copying remains forbidden.
    require("return .forward(source: message.id" in text, "native forward fallback missing")
    require("message.id.peerId.namespace != Namespaces.Peer.SecretChat" in text, "secret-chat exclusion missing")

    print("[Build124 protected forward verify] GREEN")
    print("[Build124 protected forward verify] protected file/photo media uses fresh local upload resources before enqueue")


if __name__ == "__main__":
    main()
