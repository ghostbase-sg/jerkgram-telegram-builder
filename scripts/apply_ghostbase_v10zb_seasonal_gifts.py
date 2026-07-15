#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

path = root / (
    "submodules/TelegramUI/Components/Gifts/"
    "GiftOptionsScreen/Sources/GiftOptionsScreen.swift"
)

if not path.is_file():
    raise SystemExit(f"missing GiftOptionsScreen source: {path}")

text = path.read_text(encoding="utf-8")

marker = "// MARK: GhostBase v1.0ZB Seasonal Gifts"

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[v1.0ZB seasonal gifts] {message}")

if marker not in text:
    component_anchor = (
        "final class GiftOptionsScreenComponent: Component {"
    )

    require(
        component_anchor in text,
        "GiftOptionsScreen component anchor missing"
    )

    helpers = r'''// MARK: GhostBase v1.0ZB Seasonal Gifts

private struct GhostBaseSeasonalGiftDescriptor {
    let id: Int64
    let title: String
    let price: Int64
    let stickerIndex: Int
}

private let ghostBaseSeasonalGiftDescriptors: [
    GhostBaseSeasonalGiftDescriptor
] = [
    GhostBaseSeasonalGiftDescriptor(
        id: 5956217000635139069,
        title: "New Year Bear",
        price: 50,
        stickerIndex: 1
    ),
    GhostBaseSeasonalGiftDescriptor(
        id: 5922558454332916696,
        title: "Christmas Tree",
        price: 50,
        stickerIndex: 2
    ),
    GhostBaseSeasonalGiftDescriptor(
        id: 5800655655995968830,
        title: "Valentine Bear",
        price: 50,
        stickerIndex: 3
    ),
    GhostBaseSeasonalGiftDescriptor(
        id: 5866352046986232958,
        title: "March 8 Bear",
        price: 50,
        stickerIndex: 4
    ),
    GhostBaseSeasonalGiftDescriptor(
        id: 5801108895304779062,
        title: "Valentine Card",
        price: 50,
        stickerIndex: 5
    ),
    GhostBaseSeasonalGiftDescriptor(
        id: 5893356958802511476,
        title: "Leprechaun Bear",
        price: 50,
        stickerIndex: 6
    ),
    GhostBaseSeasonalGiftDescriptor(
        id: 5935895822435615975,
        title: "April 1 Bear",
        price: 50,
        stickerIndex: 7
    ),
    GhostBaseSeasonalGiftDescriptor(
        id: 5969796561943660080,
        title: "Easter Bear",
        price: 50,
        stickerIndex: 8
    ),
    GhostBaseSeasonalGiftDescriptor(
        id: 6026193266406327981,
        title: "Builder Bear",
        price: 50,
        stickerIndex: 9
    )
]

private let ghostBaseSeasonalGiftIds = Set(
    ghostBaseSeasonalGiftDescriptors.map(\.id)
)

private func ghostBaseIsSeasonalGift(
    _ gift: StarGift
) -> Bool {
    if case let .generic(gift) = gift {
        return ghostBaseSeasonalGiftIds.contains(gift.id)
    } else {
        return false
    }
}

private func ghostBaseMakeSeasonalGifts(
    items: [StickerPackItem]
) -> [StarGift] {
    var result: [StarGift] = []

    for descriptor in ghostBaseSeasonalGiftDescriptors {
        guard descriptor.stickerIndex >= 0,
              descriptor.stickerIndex < items.count else {
            continue
        }

        let file =
            items[descriptor.stickerIndex].file._parse()

        let gift = StarGift.Gift(
            id: descriptor.id,
            title: descriptor.title,
            file: file,
            price: descriptor.price,
            convertStars: 0,
            availability: nil,
            soldOut: nil,
            flags: [],
            upgradeStars: nil,
            releasedBy: nil,
            perUserLimit: nil,
            lockedUntilDate: nil,
            auctionSlug: nil,
            auctionGiftsPerRound: nil,
            auctionStartDate: nil,
            upgradeVariantsCount: nil,
            background: nil
        )

        result.append(.generic(gift))
    }

    return result
}

private func ghostBaseMergeSeasonalGifts(
    serverGifts: [StarGift],
    seasonalGifts: [StarGift]
) -> [StarGift] {
    let serverIds = Set(serverGifts.map(\.id))

    let additions = seasonalGifts.filter {
        !serverIds.contains($0.id)
    }

    guard !additions.isEmpty else {
        return serverGifts
    }

    var insertionIndex = 0

    for (index, gift) in serverGifts.enumerated() {
        if case let .generic(gift) = gift,
           gift.availability == nil {
            insertionIndex = index + 1
        }
    }

    var result = serverGifts
    result.insert(
        contentsOf: additions,
        at: min(insertionIndex, result.count)
    )

    return result
}

'''

    text = text.replace(
        component_anchor,
        helpers + component_anchor,
        1
    )

    old_filter_cases = '''        case resale
        case stars(Int64)
        case transfer
'''

    new_filter_cases = '''        case resale
        case seasonal
        case stars(Int64)
        case transfer
'''

    require(
        old_filter_cases in text,
        "StarsFilter cases anchor missing"
    )
    text = text.replace(
        old_filter_cases,
        new_filter_cases,
        1
    )

    old_raw_init = '''            case -4:
                self = .resale
            default:
'''

    new_raw_init = '''            case -4:
                self = .resale
            case -5:
                self = .seasonal
            default:
'''

    require(
        old_raw_init in text,
        "StarsFilter raw init anchor missing"
    )
    text = text.replace(
        old_raw_init,
        new_raw_init,
        1
    )

    old_raw_value = '''            case .resale:
                return -4
            case let .stars(stars):
'''

    new_raw_value = '''            case .resale:
                return -4
            case .seasonal:
                return -5
            case let .stars(stars):
'''

    require(
        old_raw_value in text,
        "StarsFilter raw value anchor missing"
    )
    text = text.replace(
        old_raw_value,
        new_raw_value,
        1
    )

    old_filter_switch = '''                            case .resale:
                                if case let .generic(gift) = $0 {
                                    if let availability = gift.availability, availability.resale > 0 {
                                        return true
                                    }
                                }
                            case .transfer:
'''

    new_filter_switch = '''                            case .resale:
                                if case let .generic(gift) = $0 {
                                    if let availability = gift.availability, availability.resale > 0 {
                                        return true
                                    }
                                }
                            case .seasonal:
                                return ghostBaseIsSeasonalGift($0)
                            case .transfer:
'''

    require(
        old_filter_switch in text,
        "effective gift filter switch anchor missing"
    )
    text = text.replace(
        old_filter_switch,
        new_filter_switch,
        1
    )

    old_all_tab = '''                tabSelectorItems.append(TabSelectorComponent.Item(
                    id: AnyHashable(StarsFilter.all.rawValue),
                    title: strings.Gift_Options_Gift_Filter_AllGifts
                ))
                
                if hasTransferGifts {
'''

    new_all_tab = '''                tabSelectorItems.append(TabSelectorComponent.Item(
                    id: AnyHashable(StarsFilter.all.rawValue),
                    title: strings.Gift_Options_Gift_Filter_AllGifts
                ))

                let hasSeasonalGifts =
                    self.state?.starGifts?.contains(where: {
                        ghostBaseIsSeasonalGift($0)
                    }) ?? false

                if hasSeasonalGifts {
                    tabSelectorItems.append(
                        TabSelectorComponent.Item(
                            id: AnyHashable(
                                StarsFilter.seasonal.rawValue
                            ),
                            title: "Сезонные"
                        )
                    )
                }
                
                if hasTransferGifts {
'''

    require(
        old_all_tab in text,
        "All Gifts tab anchor missing"
    )
    text = text.replace(
        old_all_tab,
        new_all_tab,
        1
    )

    old_combine_tail = '''                availableProducts,
                context.engine.payments.cachedStarGifts(),
                self.starGiftsContext.state
            ).start(next: { [weak self] peer, disallowedGifts, availableProducts, starGifts, profileGiftsState in
'''

    new_combine_tail = '''                availableProducts,
                context.engine.payments.cachedStarGifts(),
                context.engine.stickers.loadedStickerPack(
                    reference: .name("DeletedGiftsStickers"),
                    forceActualized: false
                )
                |> map { result -> [StarGift] in
                    switch result {
                    case .fetching:
                        return []
                    case .none:
                        return []
                    case let .result(_, items, _):
                        return ghostBaseMakeSeasonalGifts(
                            items: items
                        )
                    }
                },
                self.starGiftsContext.state
            ).start(next: {
                [weak self]
                peer,
                disallowedGifts,
                availableProducts,
                starGifts,
                seasonalGifts,
                profileGiftsState in
'''

    require(
        old_combine_tail in text,
        "State combineLatest anchor missing"
    )
    text = text.replace(
        old_combine_tail,
        new_combine_tail,
        1
    )

    old_filtered_start = '''                var filteredStarGifts = starGifts
                if peerId.namespace == Namespaces.Peer.CloudChannel {
'''

    new_filtered_start = '''                var filteredStarGifts: [StarGift]?

                if let starGifts {
                    filteredStarGifts =
                        ghostBaseMergeSeasonalGifts(
                            serverGifts: starGifts,
                            seasonalGifts: seasonalGifts
                        )
                } else {
                    filteredStarGifts = nil
                }

                if peerId.namespace == Namespaces.Peer.CloudChannel {
'''

    require(
        old_filtered_start in text,
        "filteredStarGifts anchor missing"
    )
    text = text.replace(
        old_filtered_start,
        new_filtered_start,
        1
    )

    old_ribbon_start = '''                        case let .generic(gift):
                            if let _ = gift.soldOut {
'''

    new_ribbon_start = '''                        case let .generic(gift):
                            if ghostBaseSeasonalGiftIds.contains(
                                gift.id
                            ) {
                                ribbon = GiftItemComponent.Ribbon(
                                    text: "Сезонный",
                                    color: .blue
                                )
                            }

                            if let _ = gift.soldOut {
'''

    require(
        old_ribbon_start in text,
        "Gift ribbon anchor missing"
    )
    text = text.replace(
        old_ribbon_start,
        new_ribbon_start,
        1
    )

for proof in (
    marker,
    'reference: .name("DeletedGiftsStickers")',
    "ghostBaseMakeSeasonalGifts",
    "ghostBaseMergeSeasonalGifts",
    "case seasonal",
    "self = .seasonal",
    "case .seasonal:",
    'title: "Сезонные"',
    'text: "Сезонный"',
    "stickerIndex: 1",
    "stickerIndex: 9",
    "GiftSetupScreen",
):
    require(proof in text, f"missing proof: {proof}")

require(
    text.count(marker) == 1,
    "seasonal overlay duplicated"
)

require(
    text.count('reference: .name("DeletedGiftsStickers")') == 1,
    "sticker pack request duplicated"
)

# Normalize an already-patched generated tree as well.
text = text.replace(
    "        let file = items[descriptor.stickerIndex].file\n",
    "        let file =\n"
    "            items[descriptor.stickerIndex].file._parse()\n"
)

ids_anchor = """private let ghostBaseSeasonalGiftIds = Set(
    ghostBaseSeasonalGiftDescriptors.map(\\.id)
)

private func ghostBaseMakeSeasonalGifts(
"""

ids_replacement = """private let ghostBaseSeasonalGiftIds = Set(
    ghostBaseSeasonalGiftDescriptors.map(\\.id)
)

private func ghostBaseIsSeasonalGift(
    _ gift: StarGift
) -> Bool {
    if case let .generic(gift) = gift {
        return ghostBaseSeasonalGiftIds.contains(gift.id)
    } else {
        return false
    }
}

private func ghostBaseMakeSeasonalGifts(
"""

if "private func ghostBaseIsSeasonalGift(" not in text:
    if ids_anchor not in text:
        raise SystemExit("seasonal helper normalization anchor missing")
    text = text.replace(ids_anchor, ids_replacement, 1)

text = text.replace(
    """                            case .seasonal:
                                return ghostBaseSeasonalGiftIds.contains(
                                    $0.id
                                )
""",
    """                            case .seasonal:
                                return ghostBaseIsSeasonalGift($0)
"""
)

text = text.replace(
    """                let hasSeasonalGifts =
                    self.state?.starGifts?.contains(where: {
                        ghostBaseSeasonalGiftIds.contains($0.id)
                    }) ?? false
""",
    """                let hasSeasonalGifts =
                    self.state?.starGifts?.contains(where: {
                        ghostBaseIsSeasonalGift($0)
                    }) ?? false
"""
)

path.write_text(text, encoding="utf-8")

print("[v1.0ZB] Seasonal Gifts integrated into GiftOptionsScreen")
print("[v1.0ZB] DeletedGiftsStickers provider added")
print("[v1.0ZB] Seasonal filter and ribbons added")
print("[v1.0ZB] server gifts keep priority by giftId")
