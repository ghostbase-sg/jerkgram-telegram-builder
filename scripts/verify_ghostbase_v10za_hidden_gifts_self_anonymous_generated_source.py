#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

path = root / (
    "submodules/SettingsUI/Sources/GhostBase/"
    "GhostBaseSettingsController.swift"
)

text = path.read_text(encoding="utf-8")

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(
            f"[v1.0ZA gifts self/anonymous verifier] {message}"
        )

for proof in (
    "GhostBase v1.0ZA Hidden Gifts self and anonymous send",
    "var hideName: Bool = false",
    '"Отправить себе"',
    'case "hiddenGiftSendSelf":',
    "context.account.peerId",
    '"Выбрать другого получателя"',
    '"Скрыть имя отправителя: Вкл"',
    '"Скрыть имя отправителя: Выкл"',
    'case "hiddenGiftSendToggleHideName":',
    "ghostBaseHiddenGiftSendState.hideName.toggle()",
    "ghostBaseHiddenGiftSendState.firstConfirmed = false",
    "let hideName =",
    "hideName: hideName",
):
    require(proof in text, f"missing proof: {proof}")

require(
    text.count(
        "GhostBase v1.0ZA Hidden Gifts self and anonymous send"
    ) == 1,
    "overlay duplicated"
)

require(
    text.count('case "hiddenGiftSendSelf":') == 1,
    "self-recipient action duplicated"
)

require(
    text.count(
        'case "hiddenGiftSendToggleHideName":'
    ) == 1,
    "anonymous-toggle action duplicated"
)

send_start = text.index(
    "    let runHiddenGiftRealSend: () -> Void = {"
)
send_end = text.index(
    "    let arguments = GhostBaseSettingsArguments(",
    send_start
)
send_source = text[send_start:send_end]

require(
    "hideName: false" not in send_source,
    "real payment still forces visible sender"
)

require(
    "hideName: hideName" in send_source,
    "selected anonymity is not routed to payment"
)

print("[v1.0ZA gifts verifier] self-recipient OK")
print("[v1.0ZA gifts verifier] anonymous toggle OK")
print("[v1.0ZA gifts verifier] payment source receives selection")
print("[v1.0ZA gifts verifier] reconfirmation after changes OK")
