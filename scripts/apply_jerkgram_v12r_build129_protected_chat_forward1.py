#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
FORWARD = ROOT / "submodules/TelegramUI/Sources/ChatControllerForwardMessages.swift"
MARKER = "// MARK: Jerkgram v1.2R BUILD129_PROTECTED_CHAT_FORWARD1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build129 protected chat forward] " + message)


def balanced_region(text: str, token: str) -> tuple[int, int]:
    start = text.find(token)
    require(start >= 0, f"missing owner: {token}")
    brace = text.find("{", start + len(token))
    require(brace >= 0, f"missing opening brace: {token}")
    depth = 0
    for index in range(brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return start, index + 1
    raise RuntimeError("[Build129 protected chat forward] unbalanced owner")


def patch_text(text: str) -> str:
    if MARKER in text:
        return text
    token = "private func jerkgramRequiresPortableForward(_ message: Message) -> Bool"
    start, end = balanced_region(text, token)
    replacement = '''// MARK: Jerkgram v1.2R BUILD129_PROTECTED_CHAT_FORWARD1
private func jerkgramRequiresPortableForward(_ message: Message) -> Bool {
    if message.isCopyProtected() {
        return true
    }
    // Chat-level protection is not represented by `isCopyProtected()` for
    // every channel post. Detect it in the sender owner without mutating the
    // context menu: the native Forward row and Jerkgram Forward without author
    // action keep their existing independent owners.
    if let chatPeer = message.peers[message.id.peerId], chatPeer.isCopyProtectionEnabled {
        return true
    }
    if let sourcePeer = message.forwardInfo?.author ?? message.effectiveAuthor {
        return sourcePeer.isCopyProtectionEnabled
    }
    return false
}'''
    return text[:start] + replacement + text[end:]


def main() -> None:
    require(FORWARD.is_file(), f"missing forward owner: {FORWARD}")
    forward = patch_text(FORWARD.read_text(encoding="utf-8"))
    FORWARD.write_text(forward, encoding="utf-8")
    print("[Build129 protected chat forward] GREEN")


if __name__ == "__main__":
    main()
