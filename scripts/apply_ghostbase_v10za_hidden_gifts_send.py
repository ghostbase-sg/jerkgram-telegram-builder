#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))
dry_run = os.environ.get("GHOSTBASE_DRY_RUN") == "1"

path = root / (
    "submodules/SettingsUI/Sources/GhostBase/"
    "GhostBaseSettingsController.swift"
)

if not path.is_file():
    raise SystemExit(f"missing generated settings source: {path}")

text = path.read_text(encoding="utf-8")

marker = "// MARK: GhostBase v1.0ZA Hidden Gifts real send"

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[v1.0ZA gifts send] {message}")

require(
    "GhostBase v1.0Z Hidden Gifts direct catalog deep probe"
    in text,
    "v1.0Z deep probe must be applied first"
)

if marker not in text:
    helper_insert_anchor = (
        "private func ghostBaseSettingsEntries("
    )

    require(
        helper_insert_anchor in text,
        "settings entries helper anchor missing"
    )

    helper = r'''// MARK: GhostBase v1.0ZA Hidden Gifts real send

private struct GhostBaseHiddenGiftSendState {
    var giftName: String?
    var giftId: Int64?
    var targetPeerId: EnginePeer.Id?
    var targetLabel: String?
    var firstConfirmed: Bool = false
    var isSending: Bool = false
    var status: String = "Выберите подарок и получателя."
}

private var ghostBaseHiddenGiftSendState =
    GhostBaseHiddenGiftSendState()

private func ghostBaseHiddenGiftSendSummary() -> String {
    let state = ghostBaseHiddenGiftSendState

    let gift: String
    if let giftName = state.giftName,
       let giftId = state.giftId {
        gift = "\(giftName)\nID: \(giftId)"
    } else {
        gift = "не выбран"
    }

    let target =
        state.targetLabel
        ?? "не выбран"

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
    \(gift)

    Получатель:
    \(target)

    Цена:
    строго 50 XTR

    Подтверждение:
    \(confirmation)

    Статус:
    \(state.status)
    """
}

private func ghostBaseHiddenGiftSendErrorText(
    _ error: SendBotPaymentFormError
) -> String {
    switch error {
    case .generic:
        return "generic"
    case .precheckoutFailed:
        return "precheckoutFailed"
    case .paymentFailed:
        return "paymentFailed"
    case .alreadyPaid:
        return "alreadyPaid"
    case .starGiftOutOfStock:
        return "starGiftOutOfStock"
    case .disallowedStarGift:
        return "disallowedStarGift"
    case .starGiftUserLimit:
        return "starGiftUserLimit"
    case let .serverProvided(value):
        return "serverProvided: \(value)"
    }
}

private func ghostBaseHiddenGiftSendResultText(
    _ result: SendBotPaymentResult
) -> String {
    switch result {
    case .done:
        return "SUCCESS: подарок отправлен, 50 Stars списаны."
    case let .externalVerificationRequired(url):
        return """
        externalVerificationRequired
        URL не открыт автоматически:
        \(url)
        """
    }
}

'''

    text = text.replace(
        helper_insert_anchor,
        helper + helper_insert_anchor,
        1
    )

    entries_anchor = """    if page == .root {
"""

    require(
        entries_anchor in text,
        "settings entries root anchor missing"
    )

    entries = r'''    if page == .debugResearch {
        entries.append(
            .header(
                debug,
                "Hidden Gifts Send — реальное списание"
            )
        )

        entries.append(.researchAction(
            debug,
            920,
            "New Year Bear · ID 5956217000635139069",
            "hiddenGiftSendSelect0"
        ))
        entries.append(.researchAction(
            debug,
            921,
            "Christmas Tree · ID 5922558454332916696",
            "hiddenGiftSendSelect1"
        ))
        entries.append(.researchAction(
            debug,
            922,
            "Valentine Bear · ID 5800655655995968830",
            "hiddenGiftSendSelect2"
        ))
        entries.append(.researchAction(
            debug,
            923,
            "March 8 Bear · ID 5866352046986232958",
            "hiddenGiftSendSelect3"
        ))
        entries.append(.researchAction(
            debug,
            924,
            "Valentine Card · ID 5801108895304779062",
            "hiddenGiftSendSelect4"
        ))
        entries.append(.researchAction(
            debug,
            925,
            "Leprechaun Bear · ID 5893356958802511476",
            "hiddenGiftSendSelect5"
        ))
        entries.append(.researchAction(
            debug,
            926,
            "April 1 Bear · ID 5935895822435615975",
            "hiddenGiftSendSelect6"
        ))
        entries.append(.researchAction(
            debug,
            927,
            "Easter Bear · ID 5969796561943660080",
            "hiddenGiftSendSelect7"
        ))
        entries.append(.researchAction(
            debug,
            928,
            "Builder Bear · ID 6026193266406327981",
            "hiddenGiftSendSelect8"
        ))

        entries.append(.researchAction(
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
    }

'''

    text = text.replace(
        entries_anchor,
        entries + entries_anchor,
        1
    )

    disposable_anchor = """    let ghostBaseHiddenGiftsDisposable = MetaDisposable()
"""

    require(
        disposable_anchor in text,
        "Hidden Gifts disposable anchor missing"
    )

    text = text.replace(
        disposable_anchor,
        disposable_anchor
        + """
    let ghostBaseHiddenGiftFormDisposable = MetaDisposable()
    let ghostBaseHiddenGiftPaymentDisposable = MetaDisposable()
""",
        1
    )

    arguments_anchor = """    let arguments = GhostBaseSettingsArguments(
"""

    require(
        arguments_anchor in text,
        "settings arguments anchor missing"
    )

    controller_helpers = r'''    let selectHiddenGiftForSend: (
        Int
    ) -> Void = { index in
        guard !ghostBaseHiddenGiftSendState.isSending else {
            return
        }

        guard index >= 0,
              index < ghostBaseHiddenGiftItems.count else {
            ghostBaseHiddenGiftSendState.status =
                "Ошибка: индекс подарка вне диапазона."
            refreshResearchPage()
            return
        }

        let item = ghostBaseHiddenGiftItems[index]

        ghostBaseHiddenGiftSendState.giftName = item.0
        ghostBaseHiddenGiftSendState.giftId = item.1
        ghostBaseHiddenGiftSendState.firstConfirmed = false
        ghostBaseHiddenGiftSendState.status =
            "Подарок выбран: \(item.0), ID \(item.1)."

        refreshResearchPage()
    }

    let runHiddenGiftRealSend: () -> Void = {
        guard !ghostBaseHiddenGiftSendState.isSending else {
            return
        }

        guard ghostBaseHiddenGiftSendState.firstConfirmed,
              let giftName =
                ghostBaseHiddenGiftSendState.giftName,
              let giftId =
                ghostBaseHiddenGiftSendState.giftId,
              let targetPeerId =
                ghostBaseHiddenGiftSendState.targetPeerId else {
            ghostBaseHiddenGiftSendState.status =
                "Отправка заблокирована: нет полного подтверждения."
            refreshResearchPage()
            return
        }

        let source: BotPaymentInvoiceSource = .starGift(
            hideName: false,
            includeUpgrade: false,
            peerId: targetPeerId,
            giftId: giftId,
            text: nil,
            entities: nil
        )

        ghostBaseHiddenGiftSendState.isSending = true
        ghostBaseHiddenGiftSendState.status =
            "Повторно получаем платёжную форму для \(giftName)…"
        refreshResearchPage()

        ghostBaseHiddenGiftFormDisposable.set((
            context.engine.payments.fetchBotPaymentForm(
                source: source,
                themeParams: nil
            )
            |> take(1)
            |> deliverOnMainQueue
        ).start(
            next: { form in
                let total = form.invoice.prices.reduce(
                    Int64(0),
                    { current, price in
                        current + price.amount
                    }
                )

                guard form.invoice.currency == "XTR" else {
                    ghostBaseHiddenGiftSendState.isSending = false
                    ghostBaseHiddenGiftSendState.firstConfirmed = false
                    ghostBaseHiddenGiftSendState.status =
                        "ОТМЕНЕНО: currency=\(form.invoice.currency), ожидалось XTR."
                    refreshResearchPage()
                    return
                }

                guard total == 50 else {
                    ghostBaseHiddenGiftSendState.isSending = false
                    ghostBaseHiddenGiftSendState.firstConfirmed = false
                    ghostBaseHiddenGiftSendState.status =
                        "ОТМЕНЕНО: сервер запросил \(total) Stars вместо 50."
                    refreshResearchPage()
                    return
                }

                guard !form.invoice.isTest else {
                    ghostBaseHiddenGiftSendState.isSending = false
                    ghostBaseHiddenGiftSendState.firstConfirmed = false
                    ghostBaseHiddenGiftSendState.status =
                        "ОТМЕНЕНО: сервер вернул тестовую форму."
                    refreshResearchPage()
                    return
                }

                ghostBaseHiddenGiftSendState.status =
                    "Форма подтверждена: 50 XTR. Выполняется единственный payment RPC."
                refreshResearchPage()

                ghostBaseHiddenGiftPaymentDisposable.set((
                    context.engine.payments.sendStarsPaymentForm(
                        formId: form.id,
                        source: source
                    )
                    |> take(1)
                    |> deliverOnMainQueue
                ).start(
                    next: { result in
                        ghostBaseHiddenGiftSendState.isSending = false
                        ghostBaseHiddenGiftSendState.firstConfirmed = false
                        ghostBaseHiddenGiftSendState.status =
                            ghostBaseHiddenGiftSendResultText(result)
                        refreshResearchPage()
                    },
                    error: { error in
                        ghostBaseHiddenGiftSendState.isSending = false
                        ghostBaseHiddenGiftSendState.firstConfirmed = false
                        ghostBaseHiddenGiftSendState.status =
                            "PAYMENT ERROR: "
                            + ghostBaseHiddenGiftSendErrorText(error)
                        refreshResearchPage()
                    }
                ))
            },
            error: { error in
                ghostBaseHiddenGiftSendState.isSending = false
                ghostBaseHiddenGiftSendState.firstConfirmed = false
                ghostBaseHiddenGiftSendState.status =
                    "FORM ERROR: "
                    + ghostBaseHiddenGiftPaymentErrorText(error)
                refreshResearchPage()
            }
        ))
    }

'''

    text = text.replace(
        arguments_anchor,
        controller_helpers + arguments_anchor,
        1
    )

    switch_anchor = """        runResearchAction: { action in
            switch action {
"""

    require(
        switch_anchor in text,
        "runResearchAction switch anchor missing"
    )

    switch_start = text.index(switch_anchor)

    default_anchor = """            default:
                break
"""

    default_index = text.index(
        default_anchor,
        switch_start
    )

    action_cases = r'''            case "hiddenGiftSendSelect0":
                selectHiddenGiftForSend(0)

            case "hiddenGiftSendSelect1":
                selectHiddenGiftForSend(1)

            case "hiddenGiftSendSelect2":
                selectHiddenGiftForSend(2)

            case "hiddenGiftSendSelect3":
                selectHiddenGiftForSend(3)

            case "hiddenGiftSendSelect4":
                selectHiddenGiftForSend(4)

            case "hiddenGiftSendSelect5":
                selectHiddenGiftForSend(5)

            case "hiddenGiftSendSelect6":
                selectHiddenGiftForSend(6)

            case "hiddenGiftSendSelect7":
                selectHiddenGiftForSend(7)

            case "hiddenGiftSendSelect8":
                selectHiddenGiftForSend(8)

            case "hiddenGiftSendRecipient":
                guard !ghostBaseHiddenGiftSendState.isSending else {
                    break
                }

                let controller =
                    context.sharedContext.makePeerSelectionController(
                        PeerSelectionControllerParams(
                            context: context,
                            filter: [
                                .onlyPrivateChats,
                                .excludeSavedMessages,
                                .removeSearchHeader,
                                .excludeRecent,
                                .doNotSearchMessages
                            ],
                            title: "Получатель сезонного подарка"
                        )
                    )

                controller.peerSelected = {
                    [weak controller] peer, _ in
                    controller?.dismiss()

                    ghostBaseHiddenGiftSendState.targetPeerId =
                        peer.id
                    ghostBaseHiddenGiftSendState.targetLabel =
                        "user: \(String(describing: peer.id))"
                    ghostBaseHiddenGiftSendState.firstConfirmed =
                        false
                    ghostBaseHiddenGiftSendState.status =
                        "Получатель выбран: \(String(describing: peer.id))."

                    refreshResearchPage()
                }

                pushController?(controller)

            case "hiddenGiftSendConfirm":
                guard !ghostBaseHiddenGiftSendState.isSending,
                      ghostBaseHiddenGiftSendState.giftId != nil,
                      ghostBaseHiddenGiftSendState.targetPeerId != nil else {
                    ghostBaseHiddenGiftSendState.status =
                        "Сначала выберите подарок и получателя."
                    refreshResearchPage()
                    break
                }

                ghostBaseHiddenGiftSendState.firstConfirmed = true
                ghostBaseHiddenGiftSendState.status =
                    "Первое подтверждение принято. Проверьте данные и нажмите кнопку списания 50 Stars."
                refreshResearchPage()

            case "hiddenGiftSendPay":
                runHiddenGiftRealSend()

            case "hiddenGiftSendReset":
                guard !ghostBaseHiddenGiftSendState.isSending else {
                    break
                }

                ghostBaseHiddenGiftSendState =
                    GhostBaseHiddenGiftSendState()
                refreshResearchPage()

'''

    text = (
        text[:default_index]
        + action_cases
        + text[default_index:]
    )

required = [
    marker,
    "Hidden Gifts Send — реальное списание",
    "hiddenGiftSendSelect0",
    "hiddenGiftSendSelect8",
    "hiddenGiftSendRecipient",
    "hiddenGiftSendConfirm",
    "hiddenGiftSendPay",
    "2. СПИСАТЬ 50 STARS И ОТПРАВИТЬ",
    "includeUpgrade: false",
    'form.invoice.currency == "XTR"',
    "guard total == 50",
    "guard !form.invoice.isTest",
    "sendStarsPaymentForm(",
    "GhostBaseHiddenGiftSendState"
]

for proof in required:
    require(proof in text, f"missing proof: {proof}")

require(
    text.count("sendStarsPaymentForm(") == 1,
    "payment call must exist exactly once"
)

deep_start = text.index(
    "// MARK: GhostBase v1.0Z Hidden Gifts direct catalog deep probe"
)
deep_end = text.index(
    "private func ghostBaseSettingsEntries(",
    deep_start
)
deep_probe_source = text[deep_start:deep_end]

require(
    "sendStarsPaymentForm" not in deep_probe_source,
    "no-spend deep probe was contaminated"
)

if dry_run:
    print(f"[DRY RUN] would update {path}")
else:
    path.write_text(text, encoding="utf-8")

print("[v1.0ZA] Hidden Gifts real-send UI added")
print("[v1.0ZA] nine named gift selections added")
print("[v1.0ZA] double confirmation and exact 50 XTR guard added")
print("[v1.0ZA] exactly one no-retry payment call added")
