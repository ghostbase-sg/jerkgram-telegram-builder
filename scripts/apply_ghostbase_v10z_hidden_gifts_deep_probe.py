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

old_helper_marker = (
    "// MARK: GhostBase v1.0Y Hidden Gifts no-spend probe"
)
helper_end_marker = "private func ghostBaseSettingsEntries("

if old_helper_marker not in text:
    raise SystemExit("v1.0Y Hidden Gifts helper marker not found")

helper_start = text.index(old_helper_marker)
helper_end = text.index(helper_end_marker, helper_start)

helper = r'''// MARK: GhostBase v1.0Y Hidden Gifts no-spend probe
// MARK: GhostBase v1.0Z Hidden Gifts direct catalog deep probe

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

private struct GhostBaseHiddenGiftFormProbeResult {
    let total: Int64?
    let text: String
}

private func ghostBaseHiddenGiftCheckText(
    _ result: CanSendGiftResult
) -> String {
    switch result {
    case .available:
        return "available"
    case let .unavailable(text, _):
        return text.isEmpty
            ? "unavailable"
            : "unavailable: \(text)"
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

private func ghostBaseHiddenGiftDateText(
    _ value: Int32?
) -> String {
    guard let value else {
        return "nil"
    }

    let date = Date(timeIntervalSince1970: TimeInterval(value))
    return "\(value) / \(ISO8601DateFormatter().string(from: date))"
}

private func ghostBaseHiddenGiftCatalogText(
    index: Int,
    gift: StarGift.Gift
) -> String {
    var flags: [String] = []

    if gift.flags.contains(.isBirthdayGift) {
        flags.append("birthday")
    }
    if gift.flags.contains(.requiresPremium) {
        flags.append("requiresPremium")
    }
    if gift.flags.contains(.peerColorAvailable) {
        flags.append("peerColorAvailable")
    }
    if gift.flags.contains(.isAuction) {
        flags.append("auction")
    }

    let availability: String
    if let value = gift.availability {
        availability = """
        remains=\(value.remains)
        total=\(value.total)
        resale=\(value.resale)
        minResaleStars=\(value.minResaleStars.map(String.init) ?? "nil")
        """
    } else {
        availability = "nil"
    }

    let soldOut: String
    if let value = gift.soldOut {
        soldOut = """
        firstSale=\(ghostBaseHiddenGiftDateText(value.firstSale))
        lastSale=\(ghostBaseHiddenGiftDateText(value.lastSale))
        """
    } else {
        soldOut = "nil"
    }

    let perUserLimit: String
    if let value = gift.perUserLimit {
        perUserLimit =
            "remains=\(value.remains), total=\(value.total)"
    } else {
        perUserLimit = "nil"
    }

    let background: String
    if let value = gift.background {
        background = """
        center=\(value.centerColor)
        edge=\(value.edgeColor)
        text=\(value.textColor)
        """
    } else {
        background = "nil"
    }

    return """
    catalog: present
    catalogIndex: \(index)
    title: \(gift.title ?? "nil")
    fileId: \(gift.file.fileId.id)
    fileNamespace: \(gift.file.fileId.namespace)
    price: \(gift.price)
    convertStars: \(gift.convertStars)
    flags: \(flags.isEmpty ? "none" : flags.joined(separator: ","))
    availability:
    \(availability)
    soldOut:
    \(soldOut)
    upgradeStars: \(gift.upgradeStars.map(String.init) ?? "nil")
    upgradeVariantsCount: \(gift.upgradeVariantsCount.map(String.init) ?? "nil")
    releasedBy: \(gift.releasedBy.map { String(describing: $0) } ?? "nil")
    perUserLimit: \(perUserLimit)
    lockedUntilDate: \(ghostBaseHiddenGiftDateText(gift.lockedUntilDate))
    auctionSlug: \(gift.auctionSlug ?? "nil")
    auctionGiftsPerRound: \(gift.auctionGiftsPerRound.map(String.init) ?? "nil")
    auctionStartDate: \(ghostBaseHiddenGiftDateText(gift.auctionStartDate))
    background:
    \(background)
    """
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

text = text[:helper_start] + helper + text[helper_end:]

controller_start_marker = """    let runHiddenGiftsProbe: (
"""
controller_end_marker = """    let arguments = GhostBaseSettingsArguments(
"""

if controller_start_marker not in text:
    raise SystemExit("runHiddenGiftsProbe start not found")

controller_start = text.index(controller_start_marker)
controller_end = text.index(
    controller_end_marker,
    controller_start
)

controller = r'''    let runHiddenGiftsProbe: (
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

        let catalogSignal =
            context.engine.payments
            .ghostBaseFetchStarGiftsCatalogDirect()

        ghostBaseHiddenGiftsDisposable.set((
            catalogSignal
            |> mapToSignal {
                catalogResult -> Signal<[String], NoError> in

                var catalogById: [
                    Int64: (index: Int, gift: StarGift.Gift)
                ] = [:]

                let catalogHeader: String

                switch catalogResult {
                case let .catalog(list):
                    catalogHeader = """
                    DIRECT_CATALOG: success
                    hash: \(list.hashValue)
                    totalItems: \(list.items.count)
                    """

                    for (index, item) in list.items.enumerated() {
                        if case let .generic(gift) = item {
                            catalogById[gift.id] = (
                                index: index,
                                gift: gift
                            )
                        }
                    }

                case .notModified:
                    catalogHeader = """
                    DIRECT_CATALOG: notModified
                    hashRequested: 0
                    """

                case let .failed(error):
                    catalogHeader = """
                    DIRECT_CATALOG: failed
                    error: \(error)
                    """
                }

                let signals: [Signal<String, NoError>] =
                    ghostBaseHiddenGiftItems.map { name, giftId in

                        let checkSignal =
                            context.engine.payments
                            .checkCanSendStarGift(giftId: giftId)
                            |> map {
                                ghostBaseHiddenGiftCheckText($0)
                            }

                        let formProbe: (
                            Bool
                        ) -> Signal<
                            GhostBaseHiddenGiftFormProbeResult,
                            NoError
                        > = { includeUpgrade in
                            return context.engine.payments
                            .fetchBotPaymentForm(
                                source: .starGift(
                                    hideName: false,
                                    includeUpgrade: includeUpgrade,
                                    peerId: targetPeerId,
                                    giftId: giftId,
                                    text: nil,
                                    entities: nil
                                ),
                                themeParams: nil
                            )
                            |> map { form in
                                let prices =
                                    form.invoice.prices.map {
                                        "\($0.label)=\($0.amount)"
                                    }.joined(separator: ", ")

                                let total =
                                    form.invoice.prices.reduce(
                                        Int64(0),
                                        { $0 + $1.amount }
                                    )

                                let paymentBot =
                                    form.paymentBotId.map {
                                        String(describing: $0)
                                    } ?? "nil"

                                let provider =
                                    form.providerId.map {
                                        String(describing: $0)
                                    } ?? "nil"

                                let nativeProvider =
                                    form.nativeProvider?.name ?? "nil"

                                return GhostBaseHiddenGiftFormProbeResult(
                                    total: total,
                                    text: """
                                    success
                                    formId: \(form.id)
                                    currency: \(form.invoice.currency)
                                    total: \(total)
                                    prices: \(prices)
                                    isTest: \(form.invoice.isTest)
                                    passwordMissing: \(form.passwordMissing)
                                    canSaveCredentials: \(form.canSaveCredentials)
                                    paymentBotId: \(paymentBot)
                                    providerId: \(provider)
                                    nativeProvider: \(nativeProvider)
                                    urlPresent: \(form.url != nil)
                                    additionalMethods: \(form.additionalPaymentMethods.count)
                                    """
                                )
                            }
                            |> `catch` {
                                error -> Signal<
                                    GhostBaseHiddenGiftFormProbeResult,
                                    NoError
                                > in

                                return .single(
                                    GhostBaseHiddenGiftFormProbeResult(
                                        total: nil,
                                        text:
                                            ghostBaseHiddenGiftPaymentErrorText(
                                                error
                                            )
                                    )
                                )
                            }
                        }

                        let plainForm = formProbe(false)
                        let upgradedForm = formProbe(true)

                        return combineLatest(
                            checkSignal,
                            plainForm,
                            upgradedForm
                        )
                        |> map { check, plain, upgraded in
                            let catalogText: String

                            if let entry = catalogById[giftId] {
                                catalogText =
                                    ghostBaseHiddenGiftCatalogText(
                                        index: entry.index,
                                        gift: entry.gift
                                    )
                            } else {
                                catalogText = "catalog: absent"
                            }

                            let delta: String
                            if let plainTotal = plain.total,
                               let upgradedTotal = upgraded.total {
                                delta = String(
                                    upgradedTotal - plainTotal
                                )
                            } else {
                                delta = "n/a"
                            }

                            return """
                            \(name)
                            giftId: \(giftId)
                            \(catalogText)
                            checkCanSendGift: \(check)

                            plainForm:
                            \(plain.text)

                            includeUpgradeForm:
                            \(upgraded.text)

                            upgradeDelta: \(delta)
                            """
                        }
                    }

                return combineLatest(signals)
                |> map { lines in
                    return [catalogHeader] + lines
                }
            }
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

'''

text = (
    text[:controller_start]
    + controller
    + text[controller_end:]
)

text = text.replace(
    '"Hidden Gifts Probe"',
    '"Hidden Gifts Direct Catalog Probe"',
    1
)

required = [
    "GhostBase v1.0Z Hidden Gifts direct catalog deep probe",
    "ghostBaseFetchStarGiftsCatalogDirect",
    "DIRECT_CATALOG",
    "catalog: absent",
    "let plainForm = formProbe(false)",
    "let upgradedForm = formProbe(true)",
    "upgradeDelta",
    "availability:",
    "upgradeVariantsCount",
    "perUserLimit",
    "5956217000635139069",
    "6026193266406327981"
]

for proof in required:
    if proof not in text:
        raise SystemExit(f"missing deep probe proof: {proof}")

probe_start = text.index(
    "// MARK: GhostBase v1.0Z Hidden Gifts direct catalog deep probe"
)
probe_end = text.index(
    "private func ghostBaseSettingsEntries(",
    probe_start
)
probe_source = text[probe_start:probe_end]

for forbidden in (
    "sendStarsPaymentForm",
    "sendPaymentForm",
    "sendStarsForm"
):
    if forbidden in probe_source:
        raise SystemExit(f"forbidden payment call: {forbidden}")

if dry_run:
    print(f"[DRY RUN] would update {path}")
else:
    path.write_text(text, encoding="utf-8")

print("[v1.0Z] Hidden Gifts direct catalog deep probe OK")
