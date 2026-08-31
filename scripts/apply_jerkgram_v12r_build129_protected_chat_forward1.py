#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
FORWARD = ROOT / "submodules/TelegramUI/Sources/ChatControllerForwardMessages.swift"
MENU = ROOT / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
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


def patch_forward(text: str) -> str:
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
    // every channel post. Preserve it through the target picker so the sender
    // still takes the local-recreation path.
    if let chatPeer = message.peers[message.id.peerId], chatPeer.isCopyProtectionEnabled {
        return true
    }
    if let sourcePeer = message.forwardInfo?.author ?? message.effectiveAuthor {
        return sourcePeer.isCopyProtectionEnabled
    }
    return false
}'''
    return text[:start] + replacement + text[end:]


def patch_menu(text: str) -> str:
    marker = "// MARK: Jerkgram v1.2O BUILD126_FORWARD_MENU_OWNER1"
    require(marker in text, "Build126 forward menu owner missing")
    start_token = "        let jerkgramNeedsPortableForward ="
    end_token = "        let jerkgramPortableForwardIsSafe ="
    start = text.find(start_token, text.index(marker))
    end = text.find(end_token, start)
    require(start >= 0 and end >= 0, "Build126 protected forward gate missing")
    replacement = '''        let jerkgramNeedsPortableForward = chatPresentationInterfaceState.copyProtectionEnabled || jerkgramPortableForwardTargets.contains { message in
            if message.isCopyProtected() {
                return true
            }
            if let chatPeer = message.peers[message.id.peerId], chatPeer.isCopyProtectionEnabled {
                return true
            }
            if let sourcePeer = message.forwardInfo?.author ?? message.effectiveAuthor {
                return sourcePeer.isCopyProtectionEnabled
            }
            return false
        }
'''
    return text[:start] + replacement + text[end:]


def patch_texts(forward: str, menu: str) -> tuple[str, str]:
    return patch_forward(forward), patch_menu(menu)


def main() -> None:
    require(FORWARD.is_file(), f"missing forward owner: {FORWARD}")
    require(MENU.is_file(), f"missing context-menu owner: {MENU}")
    forward, menu = patch_texts(
        FORWARD.read_text(encoding="utf-8"),
        MENU.read_text(encoding="utf-8"),
    )
    FORWARD.write_text(forward, encoding="utf-8")
    MENU.write_text(menu, encoding="utf-8")
    print("[Build129 protected chat forward] GREEN")


if __name__ == "__main__":
    main()
