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

if not path.is_file():
    raise SystemExit(f"missing generated settings source: {path}")

text = path.read_text(encoding="utf-8")

marker = (
    "// MARK: GhostBase v1.0ZA Hidden Gifts "
    "self and anonymous send"
)

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(
            f"[v1.0ZA gifts self/anonymous] {message}"
        )

require(
    "// MARK: GhostBase v1.0ZA Hidden Gifts real send"
    in text,
    "real-send overlay must be applied first"
)

if marker not in text:
    old_state = '''private struct GhostBaseHiddenGiftSendState {
    var giftName: String?
    var giftId: Int64?
    var targetPeerId: EnginePeer.Id?
    var targetLabel: String?
    var firstConfirmed: Bool = false
    var isSending: Bool = false
    var status: String = "Выберите подарок и получателя."
}

private var ghostBaseHiddenGiftSendState =
'''

    new_state = '''private struct GhostBaseHiddenGiftSendState {
    var giftName: String?
    var giftId: Int64?
    var targetPeerId: EnginePeer.Id?
    var targetLabel: String?
    var hideName: Bool = false
    var firstConfirmed: Bool = false
    var isSending: Bool = false
    var status: String = "Выберите подарок и получателя."
}

// MARK: GhostBase v1.0ZA Hidden Gifts self and anonymous send
private var ghostBaseHiddenGiftSendState =
'''

    require(old_state in text, "send state anchor missing")
    text = text.replace(old_state, new_state, 1)

    old_summary = '''    let confirmation: String
    if state.isSending {
        confirmation = "выполняется платёжный запрос"
    } else if state.firstConfirmed {
        confirmation =
            "первое подтверждение принято; требуется списание"
    } else {
        confirmation = "не подтверждено"
    }

    return """
    Подарок:
    \\(gift)

    Получатель:
    \\(target)

    Цена:
    строго 50 XTR

    Подтверждение:
'''

    new_summary = '''    let anonymity =
        state.hideName
        ? "имя отправителя скрыто"
        : "имя отправителя открыто"

    let confirmation: String
    if state.isSending {
        confirmation = "выполняется платёжный запрос"
    } else if state.firstConfirmed {
        confirmation =
            "первое подтверждение принято; требуется списание"
    } else {
        confirmation = "не подтверждено"
    }

    return """
    Подарок:
    \\(gift)

    Получатель:
    \\(target)

    Цена:
    строго 50 XTR

    Отправитель:
    \\(anonymity)

    Подтверждение:
'''

    require(old_summary in text, "summary anchor missing")
    text = text.replace(old_summary, new_summary, 1)

    old_entries = '''        entries.append(.researchAction(
            debug,
            929,
            "Выбрать получателя",
            "hiddenGiftSendRecipient"
        ))

        if ghostBaseHiddenGiftSendState.giftId != nil,
           ghostBaseHiddenGiftSendState.targetPeerId != nil,
           !ghostBaseHiddenGiftSendState.firstConfirmed,
           !ghostBaseHiddenGiftSendState.isSending {
            entries.append(.researchAction(
                debug,
                930,
                "1. Подтвердить подарок и получателя",
                "hiddenGiftSendConfirm"
            ))
        }

        if ghostBaseHiddenGiftSendState.firstConfirmed,
           !ghostBaseHiddenGiftSendState.isSending {
            entries.append(.researchAction(
                debug,
                931,
                "2. СПИСАТЬ 50 STARS И ОТПРАВИТЬ",
                "hiddenGiftSendPay"
            ))
        }

        if !ghostBaseHiddenGiftSendState.isSending {
            entries.append(.researchAction(
                debug,
                932,
                "Сбросить выбор",
                "hiddenGiftSendReset"
            ))
        }

        entries.append(.researchInfo(
            debug,
            933,
            ghostBaseHiddenGiftSendSummary()
        ))
'''

    new_entries = '''        entries.append(.researchAction(
            debug,
            929,
            "Отправить себе",
            "hiddenGiftSendSelf"
        ))

        entries.append(.researchAction(
            debug,
            930,
            "Выбрать другого получателя",
            "hiddenGiftSendRecipient"
        ))

        entries.append(.researchAction(
            debug,
            931,
            ghostBaseHiddenGiftSendState.hideName
                ? "Скрыть имя отправителя: Вкл"
                : "Скрыть имя отправителя: Выкл",
            "hiddenGiftSendToggleHideName"
        ))

        if ghostBaseHiddenGiftSendState.giftId != nil,
           ghostBaseHiddenGiftSendState.targetPeerId != nil,
           !ghostBaseHiddenGiftSendState.firstConfirmed,
           !ghostBaseHiddenGiftSendState.isSending {
            entries.append(.researchAction(
                debug,
                932,
                "1. Подтвердить подарок и получателя",
                "hiddenGiftSendConfirm"
            ))
        }

        if ghostBaseHiddenGiftSendState.firstConfirmed,
           !ghostBaseHiddenGiftSendState.isSending {
            entries.append(.researchAction(
                debug,
                933,
                "2. СПИСАТЬ 50 STARS И ОТПРАВИТЬ",
                "hiddenGiftSendPay"
            ))
        }

        if !ghostBaseHiddenGiftSendState.isSending {
            entries.append(.researchAction(
                debug,
                934,
                "Сбросить выбор",
                "hiddenGiftSendReset"
            ))
        }

        entries.append(.researchInfo(
            debug,
            935,
            ghostBaseHiddenGiftSendSummary()
        ))
'''

    require(old_entries in text, "real-send entries anchor missing")
    text = text.replace(old_entries, new_entries, 1)

    old_source = '''        let source: BotPaymentInvoiceSource = .starGift(
            hideName: false,
            includeUpgrade: false,
'''

    new_source = '''        let hideName =
            ghostBaseHiddenGiftSendState.hideName

        let source: BotPaymentInvoiceSource = .starGift(
            hideName: hideName,
            includeUpgrade: false,
'''

    require(old_source in text, "payment source anchor missing")
    text = text.replace(old_source, new_source, 1)

    recipient_case = '''            case "hiddenGiftSendRecipient":
'''

    new_actions = '''            case "hiddenGiftSendSelf":
                guard !ghostBaseHiddenGiftSendState.isSending else {
                    break
                }

                ghostBaseHiddenGiftSendState.targetPeerId =
                    context.account.peerId
                ghostBaseHiddenGiftSendState.targetLabel =
                    "self: \\(String(describing: context.account.peerId))"
                ghostBaseHiddenGiftSendState.firstConfirmed = false
                ghostBaseHiddenGiftSendState.status =
                    "Получатель выбран: собственный аккаунт."
                refreshResearchPage()

            case "hiddenGiftSendToggleHideName":
                guard !ghostBaseHiddenGiftSendState.isSending else {
                    break
                }

                ghostBaseHiddenGiftSendState.hideName.toggle()
                ghostBaseHiddenGiftSendState.firstConfirmed = false

                ghostBaseHiddenGiftSendState.status =
                    ghostBaseHiddenGiftSendState.hideName
                    ? "Имя отправителя будет скрыто."
                    : "Имя отправителя будет открыто."

                refreshResearchPage()

            case "hiddenGiftSendRecipient":
'''

    require(recipient_case in text, "recipient action anchor missing")
    text = text.replace(recipient_case, new_actions, 1)

for proof in (
    marker,
    "var hideName: Bool = false",
    '"Отправить себе"',
    '"hiddenGiftSendSelf"',
    '"Скрыть имя отправителя: Вкл"',
    '"Скрыть имя отправителя: Выкл"',
    '"hiddenGiftSendToggleHideName"',
    "context.account.peerId",
    "ghostBaseHiddenGiftSendState.hideName.toggle()",
    "hideName: hideName",
):
    require(proof in text, f"missing proof: {proof}")

require(
    text.count(marker) == 1,
    "self/anonymous overlay duplicated"
)

path.write_text(text, encoding="utf-8")

print("[v1.0ZA] Hidden Gifts self-recipient added")
print("[v1.0ZA] anonymous sender toggle added")
print("[v1.0ZA] changing privacy resets confirmation")
