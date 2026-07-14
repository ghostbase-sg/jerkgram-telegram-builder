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
    raise SystemExit(f"missing generated GhostBase settings: {path}")

text = path.read_text(encoding="utf-8")

def once(source: str, old: str, new: str, label: str) -> str:
    if new in source:
        return source
    if old not in source:
        raise SystemExit(f"anchor not found: {label}")
    return source.replace(old, new, 1)

helper_anchor = """private func ghostBaseSettingsEntries(
"""

helper = r'''
// MARK: GhostBase v1.0Y Hidden Gifts no-spend probe

private let ghostBaseHiddenGiftItems: [(String, Int64)] = [
    ("New Year Bear", 5956217000635139069),
    ("Christmas Tree", 5922558454332916696),
    ("Valentine Bear", 5800655655995968830),
    ("March 8 Bear", 5866352046986232958),
    ("Valentine Card", 5801108895304779062),
    ("Leprechaun Bear", 5893356958802511476),
    ("April 1 Bear", 5935895822435615975),
    ("Easter Bear", 5969796561943660080),
    ("Builder Bear", 6026193266406327981)
]

private let ghostBaseHiddenGiftsPrefix =
    "GhostBase.Research.HiddenGifts."

private func ghostBaseHiddenGiftCheckText(
    _ result: CanSendGiftResult
) -> String {
    switch result {
    case .available:
        return "available"
    case let .unavailable(text, _):
        return text.isEmpty ? "unavailable" : "unavailable: \(text)"
    case .failed:
        return "failed"
    }
}

private func ghostBaseHiddenGiftPaymentErrorText(
    _ error: BotPaymentFormRequestError
) -> String {
    switch error {
    case .generic:
        return "generic"
    case .alreadyActive:
        return "alreadyActive"
    case .noPaymentNeeded:
        return "noPaymentNeeded"
    case .disallowedStarGift:
        return "disallowedStarGift"
    case let .starGiftResellTooEarly(timeout):
        return "starGiftResellTooEarly(\(timeout))"
    case .starGiftUserLimit:
        return "starGiftUserLimit"
    }
}

private func ghostBaseHiddenGiftsReport() -> String {
    let defaults = UserDefaults.standard
    let status = defaults.string(
        forKey: ghostBaseHiddenGiftsPrefix + "Status"
    ) ?? "not tested"
    let target = defaults.string(
        forKey: ghostBaseHiddenGiftsPrefix + "Target"
    ) ?? "none"
    let updated = defaults.string(
        forKey: ghostBaseHiddenGiftsPrefix + "Updated"
    ) ?? "none"
    let report = defaults.string(
        forKey: ghostBaseHiddenGiftsPrefix + "Report"
    ) ?? "Результатов пока нет."

    return """
Status: \(status)
Target: \(target)
Updated: \(updated)

\(report)
"""
}

'''

if "GhostBase v1.0Y Hidden Gifts no-spend probe" not in text:
    if helper_anchor not in text:
        raise SystemExit("helper insertion anchor not found")
    text = text.replace(helper_anchor, helper + helper_anchor, 1)

text = once(
    text,
    """private final class GhostBaseSettingsArguments {
    let updateBool: (String, Bool) -> Void
""",
    """private final class GhostBaseSettingsArguments {
    let runResearchAction: (String) -> Void
    let updateBool: (String, Bool) -> Void
""",
    "research action property"
)

text = once(
    text,
    """    init(
        updateBool: @escaping (String, Bool) -> Void,
""",
    """    init(
        runResearchAction: @escaping (String) -> Void,
        updateBool: @escaping (String, Bool) -> Void,
""",
    "research action initializer parameter"
)

text = once(
    text,
    """    ) {
        self.updateBool = updateBool
""",
    """    ) {
        self.runResearchAction = runResearchAction
        self.updateBool = updateBool
""",
    "research action initializer assignment"
)

text = once(
    text,
    """    case stylePreview(Int32, Int32, String)
    case info(Int32, String)
""",
    """    case stylePreview(Int32, Int32, String)
    case researchAction(Int32, Int32, String, String)
    case researchInfo(Int32, Int32, String)
    case info(Int32, String)
""",
    "research entry cases"
)

text = once(
    text,
    """        case let .stylePreview(section, _, _):
            return section
        case let .info(section, _):
""",
    """        case let .stylePreview(section, _, _):
            return section
        case let .researchAction(section, _, _, _):
            return section
        case let .researchInfo(section, _, _):
            return section
        case let .info(section, _):
""",
    "research entry section"
)

text = once(
    text,
    """        case let .stylePreview(section, index, _):
            return section * 1000 + index
        case let .info(section, _):
""",
    """        case let .stylePreview(section, index, _):
            return section * 1000 + index
        case let .researchAction(section, index, _, _):
            return section * 1000 + index
        case let .researchInfo(section, index, _):
            return section * 1000 + index
        case let .info(section, _):
""",
    "research entry stable id"
)

text = once(
    text,
    """        case let .info(ls, lt):
            if case let .info(rs, rt) = rhs {
""",
    """        case let .researchAction(ls, li, lt, la):
            if case let .researchAction(rs, ri, rt, ra) = rhs {
                return ls == rs && li == ri && lt == rt && la == ra
            }
            return false
        case let .researchInfo(ls, li, lt):
            if case let .researchInfo(rs, ri, rt) = rhs {
                return ls == rs && li == ri && lt == rt
            }
            return false
        case let .info(ls, lt):
            if case let .info(rs, rt) = rhs {
""",
    "research entry equality"
)

text = once(
    text,
    """        case let .info(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
""",
    """        case let .researchAction(_, _, title, actionId):
            return ItemListDisclosureItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: title,
                label: "",
                labelStyle: .text,
                sectionId: self.section,
                style: .blocks,
                disclosureStyle: .none,
                action: {
                    arguments.runResearchAction(actionId)
                }
            )

        case let .researchInfo(_, _, text):
            return ItemListTextItem(
                presentationData: presentationData,
                text: .plain(text),
                sectionId: self.section
            )

        case let .info(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
""",
    "research list items"
)

entries_anchor = """    if page == .root {
"""

entries = """    if page == .debugResearch {
        entries.append(.header(debug, "Hidden Gifts Probe"))
        entries.append(.researchAction(
            debug,
            900,
            "Проверить 9 подарков на себе",
            "hiddenGiftsSelf"
        ))
        entries.append(.researchAction(
            debug,
            901,
            "Выбрать пользователя и проверить",
            "hiddenGiftsOther"
        ))
        entries.append(.researchInfo(
            debug,
            902,
            ghostBaseHiddenGiftsReport()
        ))
    }

"""

if entries not in text:
    if entries_anchor not in text:
        raise SystemExit("debug entries anchor not found")
    text = text.replace(entries_anchor, entries + entries_anchor, 1)

controller_anchor = """    var openSendTextStyleImpl: (() -> Void)?

    let arguments = GhostBaseSettingsArguments(updateBool:"""

controller_block = r'''    var openSendTextStyleImpl: (() -> Void)?

    let ghostBaseHiddenGiftsDisposable = MetaDisposable()

    let refreshResearchPage: () -> Void = {
        statePromise.set(stateValue.with { $0 })
    }

    let runHiddenGiftsProbe: (
        EnginePeer.Id,
        String
    ) -> Void = { targetPeerId, targetLabel in
        let defaults = UserDefaults.standard

        defaults.set(
            "running",
            forKey: ghostBaseHiddenGiftsPrefix + "Status"
        )
        defaults.set(
            targetLabel,
            forKey: ghostBaseHiddenGiftsPrefix + "Target"
        )
        defaults.set(
            "",
            forKey: ghostBaseHiddenGiftsPrefix + "Report"
        )
        refreshResearchPage()

        let signals: [Signal<String, NoError>] =
            ghostBaseHiddenGiftItems.map { name, giftId in
                let checkSignal =
                    context.engine.payments.checkCanSendStarGift(
                        giftId: giftId
                    )
                    |> map { result in
                        ghostBaseHiddenGiftCheckText(result)
                    }

                let formSignal: Signal<String, NoError> =
                    context.engine.payments.fetchBotPaymentForm(
                        source: .starGift(
                            hideName: false,
                            includeUpgrade: false,
                            peerId: targetPeerId,
                            giftId: giftId,
                            text: nil,
                            entities: nil
                        ),
                        themeParams: nil
                    )
                    |> map { form in
                        let prices = form.invoice.prices.map {
                            "\($0.label)=\($0.amount)"
                        }.joined(separator: ", ")

                        let total = form.invoice.prices.reduce(
                            Int64(0),
                            { $0 + $1.amount }
                        )

                        return """
                        getPaymentForm: success
                        currency: \(form.invoice.currency)
                        total: \(total)
                        prices: \(prices)
                        """
                    }
                    |> `catch` { error -> Signal<String, NoError> in
                        return .single(
                            "getPaymentForm: "
                            + ghostBaseHiddenGiftPaymentErrorText(error)
                        )
                    }

                return combineLatest(checkSignal, formSignal)
                |> map { check, form in
                    return """
                    \(name)
                    giftId: \(giftId)
                    checkCanSendGift: \(check)
                    \(form)
                    """
                }
            }

        ghostBaseHiddenGiftsDisposable.set((
            combineLatest(signals)
            |> deliverOnMainQueue
        ).start(next: { lines in
            defaults.set(
                "completed",
                forKey: ghostBaseHiddenGiftsPrefix + "Status"
            )
            defaults.set(
                lines.joined(separator: "\n\n"),
                forKey: ghostBaseHiddenGiftsPrefix + "Report"
            )
            defaults.set(
                ISO8601DateFormatter().string(from: Date()),
                forKey: ghostBaseHiddenGiftsPrefix + "Updated"
            )
            refreshResearchPage()
        }))
    }

    let arguments = GhostBaseSettingsArguments(
        runResearchAction: { action in
            switch action {
            case "hiddenGiftsSelf":
                runHiddenGiftsProbe(
                    context.account.peerId,
                    "self: \(String(describing: context.account.peerId))"
                )

            case "hiddenGiftsOther":
                let presentationData =
                    context.sharedContext.currentPresentationData.with {
                        $0
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
                            title: "Получатель Hidden Gifts"
                        )
                    )

                controller.peerSelected = {
                    [weak controller] peer, _ in
                    controller?.dismiss()
                    runHiddenGiftsProbe(
                        peer.id,
                        "user: \(String(describing: peer.id))"
                    )
                }

                pushController?(controller)

            default:
                break
            }
        },
        updateBool:'''

if controller_block not in text:
    if controller_anchor not in text:
        raise SystemExit("controller action anchor not found")
    text = text.replace(
        controller_anchor,
        controller_block,
        1
    )

text = once(
    text,
    """let statePromise = ValuePromise(initialState, ignoreRepeated: true)""",
    """let statePromise = ValuePromise(initialState, ignoreRepeated: false)""",
    "research page refresh"
)

required = [
    "GhostBase v1.0Y Hidden Gifts no-spend probe",
    "5956217000635139069",
    "6026193266406327981",
    "checkCanSendStarGift",
    "fetchBotPaymentForm",
    "hiddenGiftsSelf",
    "hiddenGiftsOther"
]

for value in required:
    if value not in text:
        raise SystemExit(f"missing generated proof: {value}")

for forbidden in (
    "sendStarsPaymentForm",
    "sendPaymentForm",
    "sendStarsForm"
):
    if forbidden in text[text.index(
        "GhostBase v1.0Y Hidden Gifts no-spend probe"
    ):]:
        raise SystemExit(f"forbidden payment call: {forbidden}")

if dry_run:
    print(f"[DRY RUN] would update {path}")
else:
    path.write_text(text, encoding="utf-8")

print("[v1.0Y] Hidden Gifts no-spend probe anchors OK")
