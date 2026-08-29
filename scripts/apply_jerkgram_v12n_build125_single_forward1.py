#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
MENU = ROOT / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
MARKER = "// MARK: Jerkgram v1.2N BUILD125_SINGLE_FORWARD_DIRECT_ACTION1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build125 single forward] " + message)


def patch_text(text: str) -> str:
    if MARKER in text:
        return text

    direct_owner = "let jerkgramForwardWithoutAuthorTargets = selectAll ? messages : [message]"
    direct_gate = "if ghostBaseForwardWithoutAuthor,\n           jerkgramForwardWithoutAuthorTargets.allSatisfy({ message in"
    if direct_owner in text and direct_gate in text:
        # Build124 may already have materialized the direct action. Its
        # explanatory comment deliberately mentions the former native gate;
        # do not let that comment be mistaken for executable code and rewrite
        # the action a second time.
        return text.replace(direct_owner, MARKER + "\n        " + direct_owner, 1)

    # Build124 has two materialized owners in the wild: the early direct
    # `data.messageActions` gate and the later portable-target gate. Both must
    # become one explicit action contract. The action is still restricted to
    # message types Jerkgram can recreate locally; it simply is not hidden by
    # Telegram's native server-forward permission.
    pattern = re.compile(
        r"(?P<indent>        )if ghostBaseForwardWithoutAuthor,\n"
        r"(?P<gate>.*?data\.messageActions\.options\.contains\(\.forward\).*?|.*?jerkgramForwardWithoutAuthorTargets\.allSatisfy\(\{ message in.*?\}\)\s*)\{\n"
        r"(?P<body>.*?)(?P=indent)\}\n",
        re.DOTALL,
    )
    match = pattern.search(text)
    require(match is not None, "single-message forward action owner missing")
    body = match.group("body")
    require("ContextMenuActionItem" in body, "single-message forward action body missing")

    replacement = '''        // MARK: Jerkgram v1.2N BUILD125_SINGLE_FORWARD_DIRECT_ACTION1
        // The custom local-recreation path must be available for one selected
        // message even when Telegram suppresses its native `.forward` action.
        // Keep exclusions for media that cannot be recreated safely.
        let jerkgramForwardWithoutAuthorTargets = selectAll ? messages : [message]
        if ghostBaseForwardWithoutAuthor,
           jerkgramForwardWithoutAuthorTargets.allSatisfy({ message in
               message.id.peerId.namespace != Namespaces.Peer.SecretChat
               && !message.media.contains(where: {
                   $0 is TelegramMediaPaidContent
                   || $0 is TelegramMediaAction
                   || $0 is TelegramMediaExpiredContent
               })
           }) {
''' + body + '''        }
'''
    return text[:match.start()] + replacement + text[match.end():]


def main() -> None:
    text = MENU.read_text(encoding="utf-8")
    MENU.write_text(patch_text(text), encoding="utf-8")
    print("[Build125 single forward] GREEN")
    print("[Build125 single forward] direct one-message action is independent of Telegram native forward permission")


if __name__ == "__main__":
    main()
