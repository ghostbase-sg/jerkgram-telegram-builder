#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

files = {
    "controller": root / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryController.swift",
    "node": root / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryControllerNode.swift",
    "account": root / "submodules/TelegramCore/Sources/Account/Account.swift",
}

texts = {}
for name, path in files.items():
    if not path.is_file():
        raise SystemExit(f"[BOTSAFE2 verifier] missing {name}: {path}")
    texts[name] = path.read_text(encoding="utf-8")


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[BOTSAFE2 verifier] {message}")


controller = texts["controller"]
node = texts["node"]
account = texts["account"]

for proof in (
    "GhostBase v1.0ZF BOTSAFE2 first bot login",
    "guard self.account != nil",
    "mode: .ghostBaseBotToken",
):
    require(proof in controller, f"controller proof missing: {proof}")

require(
    "guard self.otherAccountPhoneNumbers.0 != nil" not in controller,
    "first bot login is still restricted to an existing account"
)

for proof in (
    "GhostBase v1.0ZF BOTSAFE2 first-screen button",
    'string: "Войти как бот"',
    "let botLoginReservedHeight: CGFloat = 40.0",
):
    require(proof in node, f"node proof missing: {proof}")

for proof in (
    "GhostBase v1.0ZF BOTSAFE2 local chat-list holes",
    "transaction.allChatListHoles(groupId: .root)",
    "transaction.replaceChatListHole",
    "Namespaces.PeerGroup.archive",
    "local chat-list holes closed",
):
    require(proof in account, f"account proof missing: {proof}")

for proof in (
    "AccountTaskManager blocked",
    "managedServiceViews blocked",
    "ghostBasePresenceSignal = .single(false)",
):
    require(proof in account, f"BOTSAFE1 quarantine missing: {proof}")

print("[BOTSAFE2 verifier] first-screen bot login OK")
print("[BOTSAFE2 verifier] local root/archive ChatList hole closure OK")
print("[BOTSAFE2 verifier] BOTSAFE1 quarantine preserved")
